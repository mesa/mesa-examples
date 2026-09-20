"""Mesa model for collaborative minefield mapping with swarm drones."""

from __future__ import annotations

import heapq
from collections.abc import Iterable

if __package__:
    from .agents import (
        DEAD_END,
        FINAL_PATH,
        MINE,
        SAFE,
        UNSAFE_BUFFER,
        CheckpointAgent,
        DeadEndAgent,
        DroneAgent,
        KnowledgeCellAgent,
        MineAgent,
    )
else:  # pragma: no cover - direct script compatibility
    from agents import (
        DEAD_END,
        FINAL_PATH,
        MINE,
        SAFE,
        UNSAFE_BUFFER,
        CheckpointAgent,
        DeadEndAgent,
        DroneAgent,
        KnowledgeCellAgent,
        MineAgent,
    )
from mesa import Model
from mesa.datacollection import DataCollector

Coordinate = tuple[int, int]


class SimpleMultiGrid:
    """Minimal grid adapter for swarm navigation across Mesa versions."""

    def __init__(self, width: int, height: int, torus: bool = False) -> None:
        self.width = width
        self.height = height
        self.torus = torus
        self._cells: dict[Coordinate, list[object]] = {
            (x_coord, y_coord): []
            for x_coord in range(width)
            for y_coord in range(height)
        }

    def out_of_bounds(self, position: Coordinate) -> bool:
        x_coord, y_coord = position
        return not (0 <= x_coord < self.width and 0 <= y_coord < self.height)

    def place_agent(self, agent, position: Coordinate) -> None:
        if self.out_of_bounds(position):
            raise IndexError(f"Position {position} is outside the grid")
        self._cells[position].append(agent)
        agent.pos = position

    def move_agent(self, agent, position: Coordinate) -> None:
        if self.out_of_bounds(position):
            raise IndexError(f"Position {position} is outside the grid")
        current_position = getattr(agent, "pos", None)
        if current_position is not None:
            self._cells[current_position].remove(agent)
        self._cells[position].append(agent)
        agent.pos = position

    def remove_agent(self, agent) -> None:
        current_position = getattr(agent, "pos", None)
        if current_position is None:
            return
        self._cells[current_position].remove(agent)
        agent.pos = None

    def get_cell_list_contents(
        self,
        cell_list: list[Coordinate] | tuple[Coordinate, ...],
    ) -> list[object]:
        contents: list[object] = []
        for position in cell_list:
            contents.extend(self._cells.get(position, []))
        return contents

    def get_neighborhood(
        self,
        position: Coordinate,
        moore: bool = True,
        include_center: bool = False,
        radius: int = 1,
    ) -> list[Coordinate]:
        neighbors: list[Coordinate] = []
        x_coord, y_coord = position
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if not include_center and dx == 0 and dy == 0:
                    continue
                if not moore and abs(dx) + abs(dy) > radius:
                    continue
                candidate = (x_coord + dx, y_coord + dy)
                if self.out_of_bounds(candidate):
                    continue
                neighbors.append(candidate)
        return neighbors


class MinefieldModel(Model):
    """Minefield exploration model with shared-map swarm coordination."""

    def __init__(
        self,
        width: int = 100,
        height: int = 100,
        drone_count: int = 4,
        mine_density: float = 0.07,
        num_mines: int = 150,
        drone_1_x: int = 40,
        drone_2_x: int = 45,
        drone_3_x: int = 50,
        drone_4_x: int = 55,
        seed: int | None = None,
    ) -> None:
        super().__init__(rng=seed)
        self.width = width
        self.height = height
        self.drone_count = drone_count
        self.mine_density = max(0.05, min(0.10, mine_density))
        self.num_mines = min(500, max(0, int(num_mines)))
        self.grid = SimpleMultiGrid(width, height, False)
        self.knowledge_base: dict[Coordinate, str] = {}
        self.discovered_map = self.knowledge_base
        self.verification_queue: set[Coordinate] = set()
        self.checkpoints: list[Coordinate] = []
        self.checkpoint_positions: set[Coordinate] = set()
        self.dead_ends: set[Coordinate] = set()
        self.discovered_mines: set[Coordinate] = set()
        self.scanned_cells: set[Coordinate] = set()
        self.knowledge_cell_agents: dict[Coordinate, KnowledgeCellAgent] = {}
        self.checkpoint_agents: dict[Coordinate, CheckpointAgent] = {}
        self.dead_end_agents: dict[Coordinate, DeadEndAgent] = {}
        self.entry_points: list[Coordinate] = []
        self.top_reached_positions: set[Coordinate] = set()
        self.final_path: list[Coordinate] = []
        self.mission_time_seconds = 0.0
        self.path_status = "Exploration in progress"
        self.running = True
        self.minefield_epicenters: list[Coordinate] = []
        self.leader_agent: DroneAgent | None = None
        self.follower_offsets: list[Coordinate] = [(-2, -1), (2, -1), (0, -2)]
        self.free_flight_ticks_remaining = 0
        self.free_flight_origin_y: dict[int, int] = {}
        self.initial_drone_x = [
            self._normalize_drone_x(drone_1_x),
            self._normalize_drone_x(drone_2_x),
            self._normalize_drone_x(drone_3_x),
            self._normalize_drone_x(drone_4_x),
        ]
        self.search_origin_x = self._build_search_formation()
        self.formation_ready = False

        self._safe_corridor_cells = self._generate_reserved_safe_zone()
        self.place_mines()
        self._place_drones()

        self.datacollector = DataCollector(
            model_reporters={
                "Battery Levels": self.get_battery_levels,
                "Mines Discovered": lambda model: len(model.discovered_mines),
                "Cells Explored": lambda model: len(model.scanned_cells),
            }
        )
        self.datacollector.collect(self)

    def _generate_reserved_safe_zone(self) -> set[Coordinate]:
        """Create a narrow wandering corridor that guarantees a valid route exists."""
        reserved: set[Coordinate] = set()
        center_x = self.random.randint(self.width // 4, (3 * self.width) // 4)
        corridor_half_width = max(1, min(2, self.width // 40))

        for y_coord in range(self.height):
            shift = self.random.choice([-2, -1, 0, 1, 2])
            center_x = min(
                max(center_x + shift, corridor_half_width),
                self.width - 1 - corridor_half_width,
            )
            for offset in range(-corridor_half_width, corridor_half_width + 1):
                reserved.add((center_x + offset, y_coord))

        return reserved

    def place_mines(self) -> None:
        """Place a distributed minefield outside the reserved safe corridor."""
        spawn_clear_rows = min(4, max(1, self.height // 10))
        self.minefield_epicenters = []

        candidates = [
            (x_coord, y_coord)
            for x_coord in range(self.width)
            for y_coord in range(spawn_clear_rows, self.height)
            if (x_coord, y_coord) not in self._safe_corridor_cells
        ]
        self.random.shuffle(candidates)
        if not candidates:
            return

        target_mines = min(self.num_mines, len(candidates))
        if target_mines == 0:
            return

        placed_mines: set[Coordinate] = set()
        row_bands = min(8, max(4, self.height // 12))
        column_bands = min(8, max(4, self.width // 12))
        band_height = max(1, (self.height - spawn_clear_rows) // row_bands)
        band_width = max(1, self.width // column_bands)

        band_buckets: dict[tuple[int, int], list[Coordinate]] = {}
        for candidate in candidates:
            band_y = min(
                (candidate[1] - spawn_clear_rows) // band_height, row_bands - 1
            )
            band_x = min(candidate[0] // band_width, column_bands - 1)
            band_buckets.setdefault((band_x, band_y), []).append(candidate)

        bucket_keys = list(band_buckets.keys())
        self.random.shuffle(bucket_keys)
        for key in bucket_keys:
            self.random.shuffle(band_buckets[key])

        # First pass: seed mines across as many field sectors as possible.
        while bucket_keys and len(placed_mines) < target_mines:
            next_round_keys = []
            for key in bucket_keys:
                bucket = band_buckets[key]
                if not bucket:
                    continue
                position = bucket.pop()
                placed_mines.add(position)
                self.minefield_epicenters.append(position)
                if bucket:
                    next_round_keys.append(key)
                if len(placed_mines) >= target_mines:
                    break
            bucket_keys = next_round_keys

        # Second pass: fill the remaining quota with shuffled candidates for a broad spread.
        if len(placed_mines) < target_mines:
            self.random.shuffle(candidates)
            for position in candidates:
                if len(placed_mines) >= target_mines:
                    break
                placed_mines.add(position)

        for position in placed_mines:
            mine = MineAgent(self)
            self.grid.place_agent(mine, position)

    def _place_drones(self) -> None:
        """Create one leader and three followers in a V-formation architecture."""
        leader_start = (self.initial_drone_x[0], 0)
        leader = DroneAgent(
            model=self,
            formation_slot=0,
            origin_x=self.search_origin_x[0],
            role="LEADER",
            leader_agent=None,
            formation_offset=(0, 0),
        )
        self.grid.place_agent(leader, leader_start)
        self.entry_points.append(leader_start)
        self.leader_agent = leader

        for slot in range(1, min(self.drone_count, 4)):
            start_position = (self.initial_drone_x[slot], 0)
            follower = DroneAgent(
                model=self,
                formation_slot=slot,
                origin_x=self.search_origin_x[slot],
                role="FOLLOWER",
                leader_agent=leader,
                formation_offset=self.follower_offsets[slot - 1],
            )
            self.grid.place_agent(follower, start_position)
            self.entry_points.append(start_position)

    def _build_search_formation(self) -> list[int]:
        """Build the compact post-rendezvous formation from slider spawn values."""
        active_columns = self.initial_drone_x[: self.drone_count]
        anchor_x = round(sum(active_columns) / len(active_columns))
        offsets = [-3, -1, 1, 3]
        compact_columns = []
        for slot in range(self.drone_count):
            desired_x = anchor_x + offsets[slot]
            compact_columns.append(min(max(desired_x, 0), self.width - 1))
        return compact_columns

    def update_formation_status(self) -> None:
        """Mark the swarm ready once all drones have reached compact assembly lanes."""
        drones = list(self.iter_drones())
        if not drones:
            self.formation_ready = False
            return

        self.formation_ready = all(
            drone.pos[1] <= 1 and abs(drone.pos[0] - drone.origin_x) <= 1
            for drone in drones
        )

    def _normalize_drone_x(self, raw_x: int) -> int:
        """Map slider-based x positions onto the current model width."""
        if self.width == 100:
            return min(max(int(raw_x), 0), self.width - 1)

        scaled_x = round((int(raw_x) / 99) * (self.width - 1))
        return min(max(scaled_x, 0), self.width - 1)

    @staticmethod
    def _evenly_spaced_indices(length: int, count: int) -> list[int]:
        """Return roughly evenly spaced indices across a sorted column list."""
        if count == 1:
            return [length // 2]
        indices = []
        for slot in range(count):
            ratio = slot / (count - 1)
            indices.append(min(round(ratio * (length - 1)), length - 1))
        return indices

    def step(self) -> None:
        """Advance the simulation by one scheduler tick."""
        if not self.running:
            return

        self.agents.shuffle_do("step")
        self._update_free_flight()
        self._evaluate_leadership()
        self.update_formation_status()

        top_goal = next(
            (
                drone.pos
                for drone in self.iter_drones()
                if drone.pos[1] == self.height - 1
            ),
            None,
        )
        if top_goal is not None:
            self.generate_final_path(top_goal)
            self.running = False

        if self.running and not any(agent.is_active for agent in self.iter_drones()):
            self.path_status = (
                "No path found before all drones exhausted their batteries"
            )
            self.running = False

        self.datacollector.collect(self)

    def _evaluate_leadership(self) -> None:
        """Promote the most advanced drone if it surpasses the current leader."""
        drones = [drone for drone in self.iter_drones() if drone.is_active]
        if not drones or self.leader_agent is None:
            return

        candidate = max(drones, key=lambda drone: (drone.pos[1], drone.pos[0]))
        if candidate == self.leader_agent:
            return
        if candidate.pos[1] <= self.leader_agent.pos[1]:
            return
        if self.free_flight_ticks_remaining > 0:
            return
        self.leadership_handoff(candidate)

    def leadership_handoff(self, new_leader_agent: DroneAgent) -> None:
        """Promote a new leader and retarget every follower to its V-formation."""
        if self.leader_agent is None or new_leader_agent == self.leader_agent:
            return

        old_leader = self.leader_agent
        old_leader.role = "FOLLOWER"
        old_leader.state = "RALLYING"
        old_leader.flank_direction = None
        old_leader.retreat_target = None
        old_leader.safety_override = False

        new_leader_agent.role = "LEADER"
        new_leader_agent.leader_agent = None
        new_leader_agent.state = "SCANNING"
        new_leader_agent.flank_direction = None
        new_leader_agent.retreat_target = None
        new_leader_agent.checkpoint_stack = []
        new_leader_agent.safety_override = False

        self.leader_agent = new_leader_agent

        followers = [
            drone for drone in self.iter_drones() if drone is not self.leader_agent
        ]
        followers.sort(key=lambda drone: (drone.pos[0], drone.unique_id))
        for drone, offset in zip(followers, self.follower_offsets):
            drone.role = "FOLLOWER"
            drone.leader_agent = self.leader_agent
            drone.formation_offset = offset
            drone.state = "RALLYING"
            drone.flank_direction = None
            drone.retreat_target = None
            drone.safety_override = False

    def start_free_flight(self) -> None:
        """Release all drones for a short independent exploration burst."""
        if self.free_flight_ticks_remaining > 0:
            return

        self.free_flight_ticks_remaining = 2
        self.free_flight_origin_y = {
            drone.unique_id: drone.pos[1] for drone in self.iter_drones()
        }
        self.path_status = "Leader stuck: swarm free-flying for 2 seconds"
        for drone in self.iter_drones():
            drone.state = "FREE_FLY"
            drone.safety_override = False
            drone.flank_direction = None
            drone.retreat_target = None

    def _update_free_flight(self) -> None:
        """Resolve the free-fly window and assign a new leader if needed."""
        if self.free_flight_ticks_remaining <= 0:
            return

        self.free_flight_ticks_remaining -= 1
        if self.free_flight_ticks_remaining > 0:
            return

        drones = [drone for drone in self.iter_drones() if drone.is_active]
        if not drones:
            return

        candidate = max(
            drones,
            key=lambda drone: (
                drone.pos[1]
                - self.free_flight_origin_y.get(drone.unique_id, drone.pos[1]),
                drone.pos[1],
                drone.pos[0],
            ),
        )
        if self.leader_agent is None:
            self.leader_agent = candidate
        elif (
            candidate is not self.leader_agent
            and candidate.pos[1] > self.leader_agent.pos[1]
        ):
            self.leadership_handoff(candidate)
        else:
            self.leader_agent.state = "SCANNING"
            self.leader_agent.flank_direction = None
            self.leader_agent.safety_override = False
            for drone, offset in zip(
                [d for d in self.iter_drones() if d is not self.leader_agent],
                self.follower_offsets,
            ):
                drone.role = "FOLLOWER"
                drone.leader_agent = self.leader_agent
                drone.formation_offset = offset
                drone.state = "RALLYING"
                drone.safety_override = False
        self.path_status = (
            f"Free flight complete: leader is drone {self.leader_agent.unique_id}"
        )

    def iter_drones(self) -> Iterable[DroneAgent]:
        """Yield active and inactive drone agents from the scheduler."""
        for agent in self.agents:
            if isinstance(agent, DroneAgent):
                yield agent

    def record_exploration(self, position: Coordinate) -> None:
        """Track unique cells that were scanned by a drone."""
        self.scanned_cells.add(position)

    def mark_safe(self, position: Coordinate) -> None:
        """Record a cell as safe unless it is already known hazardous."""
        state = self.knowledge_base.get(position)
        if state in {MINE, UNSAFE_BUFFER, FINAL_PATH, DEAD_END}:
            return
        self.knowledge_base[position] = SAFE
        self._sync_knowledge_cell(position, SAFE)
        if position[1] == self.height - 1:
            self.top_reached_positions.add(position)

    def register_mine(self, position: Coordinate) -> None:
        """Broadcast a newly discovered mine and its one-cell safety buffer."""
        if position in self.discovered_mines:
            return

        self.discovered_mines.add(position)
        self.knowledge_base[position] = MINE
        self._remove_knowledge_cell(position)

        for neighbor in self.moore_neighborhood(position):
            if neighbor == position:
                continue
            if self.knowledge_base.get(neighbor) in {MINE, DEAD_END}:
                continue
            self.knowledge_base[neighbor] = UNSAFE_BUFFER
            self._sync_knowledge_cell(neighbor, UNSAFE_BUFFER)

    def generate_final_path(self, goal: Coordinate | None = None) -> list[Coordinate]:
        """Resolve and mark the winning route once a drone reaches the top edge."""
        goal = goal or self._select_top_goal()
        if goal is None:
            self.path_status = "No top-edge drone available for final path generation"
            return []

        if self._cell_contains_mine(goal):
            self.register_mine(goal)
        else:
            self.mark_safe(goal)

        path = self.generate_safe_path(goal)
        self.final_path = path
        if not path:
            self.path_status = (
                "No fully verified path found through explored safe cells"
            )
            return []

        for coordinate in path:
            self.knowledge_base[coordinate] = FINAL_PATH
            self._sync_knowledge_cell(coordinate, FINAL_PATH)
        self.path_status = f"Safe path found with {len(path)} cells"
        return path

    def _select_top_goal(self) -> Coordinate | None:
        """Choose a safe goal candidate from the top edge."""
        top_positions = [
            drone.pos for drone in self.iter_drones() if drone.pos[1] == self.height - 1
        ]
        if top_positions:
            return top_positions[0]
        if self.top_reached_positions:
            return max(self.top_reached_positions, key=lambda coordinate: coordinate[1])
        return None

    def moore_neighborhood(self, position: Coordinate) -> list[Coordinate]:
        """Return the inclusive Moore neighborhood for a grid position."""
        neighbors: list[Coordinate] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidate = (position[0] + dx, position[1] + dy)
                if self.grid.out_of_bounds(candidate):
                    continue
                neighbors.append(candidate)
        return neighbors

    def _sync_knowledge_cell(self, position: Coordinate, cell_state: str) -> None:
        """Create or update a background visualization overlay for knowledge."""
        marker = self.knowledge_cell_agents.get(position)
        if marker is None:
            marker = KnowledgeCellAgent(self, cell_state)
            self.knowledge_cell_agents[position] = marker
            self.grid.place_agent(marker, position)
            return
        marker.set_state(cell_state)

    def _remove_knowledge_cell(self, position: Coordinate) -> None:
        """Remove an overlay when a cell becomes a visible mine."""
        marker = self.knowledge_cell_agents.pop(position, None)
        if marker is None:
            return
        self.grid.remove_agent(marker)

    def mark_checkpoint(self, position: Coordinate) -> None:
        """Persist a checkpoint coordinate and its UI marker."""
        if position in self.checkpoint_positions:
            return
        self.checkpoints.append(position)
        self.checkpoint_positions.add(position)
        marker = CheckpointAgent(self)
        self.checkpoint_agents[position] = marker
        self.grid.place_agent(marker, position)

    def mark_dead_end(self, position: Coordinate) -> None:
        """Collapse a retreating branch so the leader does not choose it again."""
        if position in self.dead_ends or position in self.checkpoint_positions:
            return
        self.dead_ends.add(position)
        self.knowledge_base[position] = DEAD_END
        marker = DeadEndAgent(self)
        self.dead_end_agents[position] = marker
        self.grid.place_agent(marker, position)

    def retire_checkpoint(self, position: Coordinate) -> None:
        """Convert an exhausted checkpoint into a dead-end marker."""
        if position in self.checkpoint_positions:
            self.checkpoint_positions.remove(position)
            self.checkpoints = [
                checkpoint for checkpoint in self.checkpoints if checkpoint != position
            ]
            marker = self.checkpoint_agents.pop(position, None)
            if marker is not None:
                self.grid.remove_agent(marker)
        self.mark_dead_end(position)

    def notify_leader_backtracking(self) -> None:
        """Force all followers into airborne rally mode during leader retreat."""
        for drone in self.iter_drones():
            if drone is self.leader_agent:
                continue
            drone.state = "RALLYING"
            drone.safety_override = True

    def _cell_contains_mine(self, position: Coordinate) -> bool:
        """Return True if the grid position contains a mine agent."""
        contents = self.grid.get_cell_list_contents([position])
        return any(isinstance(agent, MineAgent) for agent in contents)

    def get_battery_levels(self) -> dict[int, int]:
        """Return the current battery level for each drone."""
        return {agent.unique_id: agent.battery for agent in self.iter_drones()}

    def get_elapsed_seconds(self) -> int:
        """Return elapsed mission time in seconds."""
        return round(self.mission_time_seconds, 2)

    def register_step_time(self, seconds: float) -> None:
        """Accumulate mission time using scan or flight durations."""
        self.mission_time_seconds += seconds

    def generate_safe_path(self, goal: Coordinate) -> list[Coordinate]:
        """Run A* only through fully verified safe cells."""
        if not self._is_verified_safe(goal):
            return []

        start_candidates = [
            position
            for position in self.entry_points
            if self._is_verified_safe(position)
        ]
        if not start_candidates:
            return []

        g_score: dict[Coordinate, int] = {}
        came_from: dict[Coordinate, Coordinate] = {}
        frontier: list[tuple[int, int, Coordinate]] = []

        for start in start_candidates:
            g_score[start] = 0
            heapq.heappush(frontier, (self._heuristic(start, goal), 0, start))

        closed: set[Coordinate] = set()

        while frontier:
            _, current_cost, current = heapq.heappop(frontier)
            if current in closed:
                continue
            closed.add(current)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            for neighbor in self._safe_neighbors(current):
                tentative_cost = current_cost + 1
                if tentative_cost >= g_score.get(neighbor, float("inf")):
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative_cost
                priority = tentative_cost + self._heuristic(neighbor, goal)
                heapq.heappush(frontier, (priority, tentative_cost, neighbor))

        return []

    def _safe_neighbors(self, position: Coordinate) -> list[Coordinate]:
        """Return Moore-neighbor cells that are fully verified safe."""
        neighbors: list[Coordinate] = []
        for candidate in self.moore_neighborhood(position):
            if candidate == position:
                continue
            if not self._is_verified_safe(candidate):
                continue
            neighbors.append(candidate)
        return neighbors

    def _is_verified_safe(self, position: Coordinate) -> bool:
        """Return True if the path cell is safe and every neighbor is explicitly known."""
        if self.knowledge_base.get(position) not in {SAFE, FINAL_PATH}:
            return False

        for neighbor in self.moore_neighborhood(position):
            neighbor_state = self.knowledge_base.get(neighbor)
            if neighbor_state is None:
                return False
        return True

    @staticmethod
    def _heuristic(source: Coordinate, target: Coordinate) -> int:
        """Chebyshev distance matches Moore-neighborhood motion."""
        return max(abs(source[0] - target[0]), abs(source[1] - target[1]))

    @staticmethod
    def _reconstruct_path(
        came_from: dict[Coordinate, Coordinate],
        current: Coordinate,
    ) -> list[Coordinate]:
        """Rebuild an A* path from the predecessor map."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
