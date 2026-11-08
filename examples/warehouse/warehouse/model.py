"""Warehouse meta-agent example built on the public meta-agents API."""

from __future__ import annotations

import mesa
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.discrete_space.cell_agent import CellAgent
from mesa.experimental.meta_agents import MetaAgents
from mesa.experimental.scenarios import Scenario

from .agents import InventoryAgent, RouteAgent, SensorAgent, WorkerAgent
from .make_warehouse import get_warehouse_coords, make_warehouse


def _robot_find_path(self, start, goal):  # type: ignore[no-untyped-def]
    """Delegate path finding to the typed ``router`` member."""
    router = next(
        iter(self.model.meta_agents.members_of(self, relation="router")), None
    )
    if router is None:
        raise RuntimeError("Robot has no router member")
    return router.find_path(start, goal)


def _robot_move(self, coord, path):  # type: ignore[no-untyped-def]
    """Delegate movement to the typed ``sensor`` member."""
    sensor = next(
        iter(self.model.meta_agents.members_of(self, relation="sensor")), None
    )
    if sensor is None:
        raise RuntimeError("Robot has no sensor member")
    return sensor.move(coord, path)


def _robot_initiate_task(self, item):  # type: ignore[no-untyped-def]
    """Delegate task start to the typed ``worker`` member."""
    worker = next(
        iter(self.model.meta_agents.members_of(self, relation="worker")), None
    )
    if worker is None:
        raise RuntimeError("Robot has no worker member")
    return worker.initiate_task(item)


def _robot_continue_task(self):  # type: ignore[no-untyped-def]
    """Delegate task continuation to the typed ``worker`` member."""
    worker = next(
        iter(self.model.meta_agents.members_of(self, relation="worker")), None
    )
    if worker is None:
        raise RuntimeError("Robot has no worker member")
    return worker.continue_task()


class WarehouseScenario(Scenario):
    """Scenario parameters for the warehouse meta-agent example."""

    rows: int = 8
    cols: int = 8
    height: int = 2


class WarehouseModel(mesa.Model):
    """Model for simulating warehouse robots assembled from sub-agents."""

    def __init__(self, scenario: WarehouseScenario = WarehouseScenario):  # type: ignore[assignment]
        """Create the warehouse, inventory, and robot meta-agents."""
        super().__init__(scenario=scenario)
        self.inventory = {}
        self.meta_agents = MetaAgents(self)
        # Expose backend for shallow inspection (triplet count, invariants).
        # Most code should use self.meta_agents; this alias shows the
        # underlying MembershipBackend that tracks triplets.
        self.membership_backend = self.meta_agents.backend

        layout = make_warehouse(
            rows=self.scenario.rows,
            cols=self.scenario.cols,
            height=self.scenario.height,
            rng=self.random,
        )
        self.warehouse = OrthogonalMooreGrid(
            (layout.shape[0], layout.shape[1], layout.shape[2]),
            torus=False,
            capacity=1,
            random=self.random,
        )

        # Inventory agents live in the storage rows of the warehouse.
        for row in range(2, layout.shape[0] - 1, 3):
            for col in range(layout.shape[1]):
                for height in range(layout.shape[2]):
                    item = layout[row][col][height]
                    if item.strip():
                        InventoryAgent(self, self.warehouse[row, col, height], item)

        self.robots: list = []

        # One robot per dock/station pair; coords adapt to scenario size.
        loading_docks, charging_stations = get_warehouse_coords(
            self.scenario.rows, self.scenario.cols
        )
        self.loading_docks = loading_docks
        self.charging_stations = charging_stations

        for idx, (loading_dock, charging_station) in enumerate(
            zip(loading_docks, charging_stations, strict=True)
        ):
            router = RouteAgent(self)
            sensor = SensorAgent(self)
            worker = WorkerAgent(
                self,
                self.warehouse[loading_dock],
                self.warehouse[charging_station],
            )

            # Unique class name per robot keeps string lookups unambiguous
            # (mesa warns that reusing the same name with disjoint members
            # creates distinct groups with the same name). For this shallow
            # example we keep two robots; unique names mirror
            # alliance_formation's f"MetaAgentLevel{level}_{sig}" pattern.
            class_name = f"RobotAgent_{idx}"

            meta = self.meta_agents.create(
                class_name,
                [router, sensor, worker],
                CellAgent,
                meta_attributes={
                    "cell": self.warehouse[charging_station],
                    "status": "open",
                    "path": None,
                    "item": None,
                    "carrying": None,
                    "loading_dock": self.warehouse[loading_dock],
                    "charging_station": self.warehouse[charging_station],
                },
                meta_methods={
                    "find_path": _robot_find_path,
                    "move": _robot_move,
                    "initiate_task": _robot_initiate_task,
                    "continue_task": _robot_continue_task,
                },
                memberships=[
                    (router, "router"),
                    (sensor, "sensor"),
                    (worker, "worker"),
                ],
            )

            if meta is None:
                continue

            self.robots.append(meta)

    def central_move(self, robot):
        """Delegate path execution to the robot's worker role."""
        robot.move(robot.cell.coordinate, robot.path)

    @property
    def triplet_count(self) -> int:
        """Number of membership triplets tracked by the backend."""

        return len(self.membership_backend.as_triplets())

    def step(self):
        """Advance the model by one step."""
        # Iterate over the explicit robot list so unique class names
        # (RobotAgent_0, RobotAgent_1) both get stepped. Using
        # agents_by_type would only cover the first type when names are
        # unique.
        if not self.robots:
            return

        for robot in list(self.robots):
            agent_list = self.agents_by_type[InventoryAgent].to_list()

            if robot.status == "open":
                item = self.random.choice(agent_list)
                if item.quantity > 0:
                    robot.initiate_task(item)
                    robot.status = "inventory"
                    self.central_move(robot)

            else:
                robot.continue_task()
