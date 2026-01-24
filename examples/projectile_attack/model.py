"""
Rules definition
"""

from __future__ import annotations

import math

try:
    from .agents import ResultText, Shell, Tank, Target, Wall
except ImportError:
    from agents import ResultText, Shell, Tank, Target, Wall
from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid


class TankGameModel(Model):
    def __init__(
        self,
        angle: float = 45.0,
        power: float = 70.0,
        target_movable: bool = False,
        width: int = 35,
        height: int = 35,
        seed: int | None = None,
    ):
        super().__init__(seed=seed)

        # UI parameters (modifiable)
        self.angle = angle
        self.power = power
        self.target_movable = target_movable

        # Physical constants
        self.g = 0.01  # gravitational acceleration
        self.vmax = 1.0  # maximum speed

        # Grid
        self.grid = OrthogonalMooreGrid((width, height), random=self.random)
        self.space = self.grid

        # State variables
        self.tank: Tank | None = None
        self.target: Target | None = None
        self.wall_cells: set[tuple[int, int]] = set()
        self.trajectory_cells: set[tuple[int, int]] = set()
        self.trajectory_layer = self.grid.create_property_layer(
            "trajectory", default_value=0, dtype=int
        )

        # Game result state
        self.game_over = False
        self.failed = False
        self.max_shots = 5
        self.shots_fired = 0
        self.time = 0.0

        # Fixed wall configuration (no UI control)
        self.wall_position = 17
        self.wall_height = 10

        self._initialize_game()

    def _build_wall_cells(self) -> None:
        # Build the set of wall cells
        self.wall_cells.clear()
        ground_y = 1
        for y in range(ground_y, ground_y + self.wall_height):
            if 0 <= self.wall_position < self.grid.width and 0 <= y < self.grid.height:
                self.wall_cells.add((self.wall_position, y))

    def _create_wall_agents(self) -> None:
        # Create wall agents for visualization (fixed wall)
        if self.agents_by_type.get(Wall):
            return
        for cell in self.wall_cells:
            Wall(self, pos=cell)

    def add_trajectory_cell(self, cell: tuple[int, int]) -> None:
        # Record grid cells traversed by shells (only within bounds)
        x, y = cell
        if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            self.trajectory_cells.add((x, y))
            self.trajectory_layer.data[x, y] = 1

    def clear_trajectory(self) -> None:
        # Clear current round's shell trajectory
        self.trajectory_cells.clear()
        self.trajectory_layer.data.fill(0)

    def _clear_result_text(self) -> None:
        # Remove result text agents from the grid/model if present
        result_agents = list(self.agents_by_type.get(ResultText, []))
        if not result_agents:
            return
        for agent in result_agents:
            if agent in self.agents:
                agent.remove()

    def _show_result_text(self, text: str, kind: str) -> None:
        # Create one or more result text agents at grid center
        self._clear_result_text()
        center_x = self.grid.width // 2
        center_y = int(self.grid.height * 0.8)
        lines = [line for line in text.split("\n") if line.strip()]
        if not lines:
            return
        spacing = 2
        start_y = center_y + (len(lines) - 1) * spacing // 2
        for idx, line in enumerate(lines):
            y = start_y - idx * spacing
            ResultText(
                self,
                pos=(center_x, y),
                text=line,
                kind=kind,
            )

    @property
    def shell_exists(self) -> bool:
        # Check whether a live shell exists
        shells = self.agents_by_type.get(Shell)
        if not shells:
            return False
        return any(shell.alive for shell in shells)

    @property
    def target_exists(self) -> bool:
        # Check whether the target exists and is still in the model
        return self.target is not None and self.target in self.agents

    def _initialize_game(self) -> None:
        # Initialize the game: create tank, target, and wall
        # Create tank at (1.0, 1.0)
        self.tank = Tank(self, pos=(1.0, 1.0))

        # Create target
        target_y = self.random.randint(1, 25)
        self.target = Target(self, pos_f=(self.grid.width - 2, float(target_y)))

        # Build wall cells
        self._build_wall_cells()
        self._create_wall_agents()

        self.running = True
        self.shots_fired = 0

    def fire(self) -> None:
        # Fire a shell
        if self.shell_exists:
            return
        if self.tank is None:
            return
        if self.shots_fired >= self.max_shots:
            if not self.game_over:
                self._handle_out_of_shots()
            return
        self._clear_result_text()
        if self.game_over or not self.running:
            self.game_over = False
            self.failed = False
            self.running = True

        speed = self.power / 100.0
        angle_rad = math.radians(self.angle)

        vx = math.sin(angle_rad) * speed
        vy = math.cos(angle_rad) * speed

        self.shots_fired += 1
        Shell(self, pos_f=self.tank.pos_f, vx=vx, vy=vy)

    def _handle_target_hit(self, hit_x: int, hit_y: int) -> None:
        # Handle target hit: remove target and create explosion effect
        self.clear_trajectory()

        # Remove target
        if self.target is not None and self.target in self.agents:
            self.target.remove()
            self.target = None

        self.game_over = True
        self.failed = False
        self._show_result_text(
            "Congratulations! YOU WIN!!!\n\nPerhaps you could make the target move to increase the difficulty.",
            "success",
        )

    def _handle_failure(self) -> None:
        # Handle failure conditions (missed shot, boundary/wall hit)
        if self.game_over:
            return
        self.clear_trajectory()
        if self.shots_fired >= self.max_shots:
            self._handle_out_of_shots()
        else:
            self.game_over = False
            self.failed = False

    def _handle_out_of_shots(self) -> None:
        # Stop the game when no shots remain
        self.game_over = True
        self.failed = True
        self.running = False
        self._show_result_text(
            'You have no chance!\n\nPlease click the left "Reset" button to try again.',
            "fail",
        )

    def step(self) -> None:
        # Model step logic
        self.time += 1.0
        if not self.running:
            return
        # 1) If target gone, stop running (but still decay explosions)
        if not self.target_exists:
            self.running = False
            return

        # 2) Step agents in random order
        self.agents.shuffle_do("step")

        super().step()
