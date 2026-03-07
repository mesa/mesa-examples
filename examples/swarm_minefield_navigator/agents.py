"""Agent definitions for the autonomous swarm drone minefield model."""

from __future__ import annotations

from collections import deque
import heapq
from typing import Dict, Set, Tuple

from mesa import Agent


Coordinate = Tuple[int, int]


SAFE = "SAFE"
MINE = "MINE"
UNSAFE_BUFFER = "UNSAFE_BUFFER"
FINAL_PATH = "FINAL_PATH"
DEAD_END = "DEAD_END"


class MineAgent(Agent):
    """Static mine hidden on the grid until a drone scans its cell."""

    def __init__(self, unique_id: int, model) -> None:
        super().__init__(unique_id, model)

    def step(self) -> None:
        """Mines are inert and are not scheduled."""


class KnowledgeCellAgent(Agent):
    """Visualization-only overlay for the shared mesh-network state."""

    def __init__(self, unique_id: int, model, cell_state: str) -> None:
        super().__init__(unique_id, model)
        self.cell_state = cell_state

    def set_state(self, cell_state: str) -> None:
        """Update the rendered knowledge state for a cell."""
        self.cell_state = cell_state

    def step(self) -> None:
        """Knowledge cells are not scheduled."""


class CheckpointAgent(Agent):
    """Visualization-only checkpoint marker for leader retreat anchors."""

    def __init__(self, unique_id: int, model) -> None:
        super().__init__(unique_id, model)

    def step(self) -> None:
        """Checkpoint markers are not scheduled."""


class DeadEndAgent(Agent):
    """Visualization-only marker for collapsed dead-end branches."""

    def __init__(self, unique_id: int, model) -> None:
        super().__init__(unique_id, model)

    def step(self) -> None:
        """Dead-end markers are not scheduled."""


class DroneAgent(Agent):
    """Autonomous drone in a heterogeneous leader-follower swarm."""

    def __init__(
        self,
        unique_id: int,
        model,
        formation_slot: int,
        origin_x: int,
        role: str,
        leader_agent=None,
        formation_offset: Coordinate = (0, 0),
    ) -> None:
        super().__init__(unique_id, model)
        self.formation_slot = formation_slot
        self.origin_x = origin_x
        self.role = role
        self.leader_agent = leader_agent
        self.formation_offset = formation_offset
        self.battery = 600
        self.is_active = True
        self.state = "SCANNING"
        self.flank_direction: Coordinate | None = None
        self.preferred_direction = -1 if formation_slot < model.drone_count / 2 else 1
        self.recent_path: deque[Coordinate] = deque(maxlen=8)
        self.last_position: Coordinate | None = None
        self.local_safe_memory: set[Coordinate] = set()
        self.retreat_target: Coordinate | None = None
        self.checkpoint_stack: list[Coordinate] = []
        self.safety_override = False
        self.frustration_counter = 0
        self.max_y_reached = 0

    def step(self) -> None:
        """Scan locally, move one cell by role, and scan again."""
        if not self.is_active:
            return

        move_duration = 0.25 if self._is_airborne_mode() else 1.0
        self.scan_surroundings()
        self._remember_safe_position()
        next_position = self._decide_next_move()
        self._consume_battery()
        if not self.is_active:
            return

        if next_position is not None and next_position != self.pos:
            self.last_position = self.pos
            if self.role == "LEADER" and self.state == "BACKTRACKING":
                self.model.mark_dead_end(self.pos)
            self.model.grid.move_agent(self, next_position)
            self.recent_path.append(next_position)
        self.scan_surroundings()
        self._remember_safe_position()
        self.model.register_step_time(move_duration)
        if self.role == "LEADER":
            self._update_leader_progress()

    def _consume_battery(self) -> None:
        """Spend one unit of battery per scheduler tick."""
        self.battery -= 1
        if self.battery <= 0:
            self.battery = 0
            self.is_active = False

    def scan_surroundings(self) -> None:
        """Update the mesh network using only the drone's local 1-cell sensor radius."""
        neighborhood = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=True,
            radius=1,
        )
        discovered_mines: list[Coordinate] = []
        scanned_safe: list[Coordinate] = []
        sensor_cells = set(neighborhood)

        for cell in neighborhood:
            contents = self.model.grid.get_cell_list_contents([cell])
            self.model.verification_queue.discard(cell)
            if self.model.knowledge_base.get(cell) == DEAD_END:
                continue
            if any(isinstance(agent, MineAgent) for agent in contents):
                discovered_mines.append(cell)
            else:
                scanned_safe.append(cell)

        for mine_cell in discovered_mines:
            self.model.register_mine(mine_cell)

        for safe_cell in scanned_safe:
            self.model.mark_safe(safe_cell)
            self.model.record_exploration(safe_cell)
            self._enqueue_frontier_neighbors(safe_cell, sensor_cells)

        if self.role == "LEADER":
            self._maybe_store_checkpoint(discovered_mines, neighborhood)

    def _maybe_store_checkpoint(
        self,
        discovered_mines: list[Coordinate],
        neighborhood: list[Coordinate],
    ) -> None:
        """Store fully clear 3x3 intersections as macro backtracking anchors."""
        if discovered_mines:
            return
        if len(neighborhood) < 9:
            return
        if self.pos in self.model.checkpoint_positions:
            return
        self.model.mark_checkpoint(self.pos)
        self.checkpoint_stack.append(self.pos)

    def _decide_next_move(self) -> Coordinate | None:
        """Dispatch movement logic based on drone role."""
        if self.state == "FREE_FLY":
            return self._free_fly_move()
        if self.role == "LEADER":
            if self.frustration_counter > 15 and self.state != "BACKTRACKING":
                return self._start_backtracking()
            return self._leader_move()
        if self.state == "RALLYING":
            return self._rally_move()
        return self._follower_move()

    def _update_leader_progress(self) -> None:
        """Detect horizontal loops and trigger retreat from soft deadlocks."""
        if self.state == "BACKTRACKING":
            return
        if self.pos[1] > self.max_y_reached:
            self.max_y_reached = self.pos[1]
            self.frustration_counter = 0
            return
        self.frustration_counter += 1

    def _leader_move(self) -> Coordinate | None:
        """Drive the leader north, flank around hazards, and retreat from dead ends."""
        if self.state == "BACKTRACKING":
            return self._backtracking_step()

        if self.state == "AVOIDING":
            avoiding_move = self._avoiding_step()
            if avoiding_move is not None:
                return avoiding_move

        north = self._offset_position((0, 1))
        north_move = self._leader_choice([north])
        if north_move is not None:
            self.state = "SCANNING"
            self.flank_direction = None
            return north_move

        east = self._offset_position((1, 0))
        west = self._offset_position((-1, 0))
        lateral_moves = self._leader_choice(self._ordered_lateral_candidates(east, west))
        if lateral_moves is not None:
            self.state = "AVOIDING"
            self.flank_direction = (lateral_moves[0] - self.pos[0], 0)
            return lateral_moves

        return self._start_backtracking()

    def _ordered_lateral_candidates(
        self,
        east: Coordinate | None,
        west: Coordinate | None,
    ) -> list[Coordinate | None]:
        """Order east and west according to the preferred flank direction."""
        if self.flank_direction is None:
            self.flank_direction = self._choose_flank_direction()
        if self.flank_direction[0] >= 0:
            return [east, west]
        return [west, east]

    def _follower_move(self) -> Coordinate | None:
        """Follower navigates safely toward its dynamic V-formation target."""
        if self.leader_agent is None or self.leader_agent.pos is None:
            return None

        target_x = self.leader_agent.pos[0] + self.formation_offset[0]
        target_y = self.leader_agent.pos[1] + self.formation_offset[1]
        target = (
            min(max(target_x, 0), self.model.grid.width - 1),
            min(max(target_y, 0), self.model.grid.height - 1),
        )

        valid_moves = [
            candidate
            for candidate in self._adjacent_moves()
            if self._is_valid_move(candidate)
        ]
        if not valid_moves:
            return None

        if target in valid_moves:
            return self._tabu_aware_choice([target]) or target

        next_step = self._path_step_toward(target)
        if next_step is not None:
            return next_step

        tabu_filtered = [
            candidate for candidate in valid_moves if candidate not in self.recent_path
        ]
        candidate_pool = tabu_filtered or valid_moves
        return min(
            candidate_pool,
            key=lambda cell: (
                self._manhattan_distance(cell, target),
                abs(cell[0] - target[0]),
                abs(cell[1] - target[1]),
            ),
        )

    def _rally_move(self) -> Coordinate | None:
        """Rally a follower toward the current leader, escaping traps if needed."""
        if self.leader_agent is None or self.leader_agent.pos is None:
            return None

        if self.leader_agent.state == "BACKTRACKING":
            rally_target = self.leader_agent.retreat_target or self.leader_agent.pos
            self.safety_override = True
            if self.pos == rally_target or self._will_be_adjacent(self.pos, rally_target):
                self.local_safe_memory.clear()
                self.safety_override = False
                return None

        if self._is_adjacent_to_leader():
            self.safety_override = False
            self.local_safe_memory.clear()
            self.state = "SCANNING"
            return None

        target = self.leader_agent.pos
        self.safety_override = False
        standard_candidates = [
            candidate
            for candidate in self._adjacent_moves()
            if self._is_valid_move(candidate)
        ]
        standard_move = self._pick_best_rally_move(standard_candidates, target)
        if standard_move is not None:
            return standard_move

        memory_candidates = [
            candidate
            for candidate in self._adjacent_moves()
            if candidate in self.local_safe_memory
        ]
        memory_move = self._pick_best_rally_move(
            memory_candidates,
            target,
            prefer_farther=True,
        )
        if memory_move is not None:
            return memory_move

        self.safety_override = True
        override_move = self._override_step_toward(target)
        if override_move is not None and self._will_be_adjacent(override_move, target):
            self.local_safe_memory.clear()
            self.state = "SCANNING"
            self.safety_override = False
        return override_move

    def _free_fly_move(self) -> Coordinate | None:
        """Temporarily release formation constraints and search independently."""
        north = self._offset_position((0, 1))
        east = self._offset_position((1, 0))
        west = self._offset_position((-1, 0))
        south = self._offset_position((0, -1))

        priority_moves = [north]
        lateral_moves = [candidate for candidate in (east, west) if candidate is not None]
        self.random.shuffle(lateral_moves)
        priority_moves.extend(lateral_moves)
        priority_moves.append(south)

        move = self._tabu_aware_choice(priority_moves)
        if move is not None:
            return move
        return self._override_step_toward((self.pos[0], min(self.pos[1] + 1, self.model.height - 1)))

    def _pick_best_rally_move(
        self,
        candidates: list[Coordinate],
        target: Coordinate,
        prefer_farther: bool = False,
    ) -> Coordinate | None:
        """Choose a rally move, preferring non-tabu steps and useful escape motion."""
        if not candidates:
            return None

        candidates = self._filter_immediate_reversal(candidates)
        if not candidates:
            return None

        tabu_filtered = [
            candidate for candidate in candidates if candidate not in self.recent_path
        ]
        candidate_pool = tabu_filtered or candidates
        if prefer_farther:
            return max(
                candidate_pool,
                key=lambda cell: (
                    self._manhattan_distance(cell, target),
                    cell[1],
                ),
            )
        return min(
            candidate_pool,
            key=lambda cell: (
                self._manhattan_distance(cell, target),
                abs(cell[0] - target[0]),
                abs(cell[1] - target[1]),
            ),
        )

    def _override_step_toward(self, target: Coordinate) -> Coordinate | None:
        """Ignore hazard knowledge and move directly toward the leader."""
        candidates = self._adjacent_moves()
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda cell: (
                self._manhattan_distance(cell, target),
                abs(cell[0] - target[0]),
                abs(cell[1] - target[1]),
            ),
        )

    def _is_airborne_mode(self) -> bool:
        """Return True when the drone is traversing cells via airborne override."""
        if self.state == "BACKTRACKING":
            return True
        if self.state == "RALLYING" and self.safety_override:
            return True
        return self.state == "FREE_FLY"

    def _remember_safe_position(self) -> None:
        """Store cells that this drone has physically occupied safely."""
        state = self.model.knowledge_base.get(self.pos)
        if state not in {MINE, UNSAFE_BUFFER}:
            self.local_safe_memory.add(self.pos)

    def _is_adjacent_to_leader(self) -> bool:
        """Return True when the drone is within one cell of the leader."""
        if self.leader_agent is None or self.leader_agent.pos is None:
            return False
        return self._manhattan_distance(self.pos, self.leader_agent.pos) <= 1

    def _will_be_adjacent(self, position: Coordinate, target: Coordinate) -> bool:
        """Return True if the proposed position is adjacent to the rally target."""
        return self._manhattan_distance(position, target) <= 1

    def _path_step_toward(
        self,
        target: Coordinate,
        require_known_safe: bool = False,
    ) -> Coordinate | None:
        """Return the first step of a local A* route toward the given target."""
        frontier: list[Tuple[int, int, Coordinate]] = []
        g_score: Dict[Coordinate, int] = {self.pos: 0}
        came_from: Dict[Coordinate, Coordinate] = {}
        closed: Set[Coordinate] = set()

        heapq.heappush(frontier, (self._manhattan_distance(self.pos, target), 0, self.pos))

        while frontier:
            _, current_cost, current = heapq.heappop(frontier)
            if current in closed:
                continue
            closed.add(current)

            if current == target:
                return self._first_path_step(came_from, current)

            for neighbor in self._adjacent_moves_from(current):
                if not self._is_valid_move(neighbor, require_known_safe=require_known_safe):
                    continue
                if self.role == "LEADER" and neighbor in self.model.dead_ends:
                    continue
                tentative_cost = current_cost + 1
                if tentative_cost >= g_score.get(neighbor, float("inf")):
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative_cost
                priority = tentative_cost + self._manhattan_distance(neighbor, target)
                heapq.heappush(frontier, (priority, tentative_cost, neighbor))

        return None

    def _first_path_step(
        self,
        came_from: Dict[Coordinate, Coordinate],
        current: Coordinate,
    ) -> Coordinate | None:
        """Return the first move from the current drone position along a route."""
        while current in came_from and came_from[current] != self.pos:
            current = came_from[current]
        if current == self.pos:
            return None
        if current in self.recent_path:
            alternatives = [
                candidate
                for candidate in self._adjacent_moves()
                if self._is_valid_move(candidate) and candidate not in self.recent_path
            ]
            if alternatives:
                return min(
                    alternatives,
                    key=lambda cell: self._manhattan_distance(cell, current),
                )
        return current

    def _avoiding_step(self) -> Coordinate | None:
        """Wall-follow laterally until north reopens, otherwise retreat to a checkpoint."""
        north = self._offset_position((0, 1))
        north_move = self._leader_choice([north])
        if north_move is not None:
            self.state = "SCANNING"
            self.flank_direction = None
            return north_move

        if self.flank_direction is None:
            self.flank_direction = self._choose_flank_direction()

        lateral = self._offset_position(self.flank_direction)
        lateral_move = self._leader_choice([lateral])
        if lateral_move is not None:
            return lateral_move

        self.flank_direction = (-self.flank_direction[0], 0)
        reverse_lateral = self._offset_position(self.flank_direction)
        reverse_move = self._leader_choice([reverse_lateral])
        if reverse_move is not None:
            return reverse_move

        return self._start_backtracking()

    def _start_backtracking(self) -> Coordinate | None:
        """Select the most recent viable checkpoint and begin retreating."""
        self.state = "BACKTRACKING"
        self.flank_direction = None
        self.retreat_target = None
        self.frustration_counter = 0
        self.safety_override = True
        self.model.notify_leader_backtracking()
        self.retreat_target = self._select_retreat_checkpoint()

        return self._backtracking_step()

    def _backtracking_step(self) -> Coordinate | None:
        """Walk back toward the latest checkpoint through known-safe cells."""
        if self.retreat_target is None:
            self.state = "SCANNING"
            self.max_y_reached = self.pos[1]
            self.safety_override = False
            south = self._offset_position((0, -1))
            return self._tabu_aware_choice([south], require_known_safe=True)

        if self.pos == self.retreat_target:
            if self._checkpoint_has_fresh_forward_option():
                self.state = "SCANNING"
                self.retreat_target = None
                self.max_y_reached = self.pos[1]
                self.frustration_counter = 0
                self.safety_override = False
                return None
            exhausted_checkpoint = self.pos
            self.model.retire_checkpoint(exhausted_checkpoint)
            self.retreat_target = self._select_retreat_checkpoint()
            if self.retreat_target is None:
                self.state = "SCANNING"
                self.safety_override = False
                return None
            return self._override_step_toward(self.retreat_target)

        return self._override_step_toward(self.retreat_target)

    def _checkpoint_has_fresh_forward_option(self) -> bool:
        """Return True if northward progress from a checkpoint is not exhausted."""
        for delta in ((0, 1), (1, 0), (-1, 0)):
            candidate = self._offset_position(delta)
            if self._is_leader_move_valid(candidate):
                return True
        return False

    def _select_retreat_checkpoint(self) -> Coordinate | None:
        """Return the nearest remaining checkpoint and remove it from the stack."""
        candidates = [
            checkpoint
            for checkpoint in self.checkpoint_stack
            if checkpoint != self.pos and checkpoint in self.model.checkpoint_positions
        ]
        if not candidates:
            return None
        retreat_target = min(
            candidates,
            key=lambda checkpoint: self._manhattan_distance(self.pos, checkpoint),
        )
        self.checkpoint_stack = [
            checkpoint
            for checkpoint in self.checkpoint_stack
            if checkpoint != retreat_target
        ]
        return retreat_target

    def _leader_choice(
        self,
        candidates: list[Coordinate | None],
    ) -> Coordinate | None:
        """Choose a leader move while avoiding known dead-end branches."""
        valid_moves = [
            candidate
            for candidate in candidates
            if self._is_leader_move_valid(candidate)
        ]
        if not valid_moves:
            return None

        valid_moves = self._filter_immediate_reversal(valid_moves)
        if not valid_moves:
            return None

        tabu_filtered = [
            candidate for candidate in valid_moves if candidate not in self.recent_path
        ]
        usable_moves = tabu_filtered or valid_moves
        return usable_moves[0]

    def _is_leader_move_valid(self, position: Coordinate | None) -> bool:
        """Return True if the leader can still consider the destination."""
        if position is None:
            return False
        if position in self.model.dead_ends:
            return False
        return self._is_valid_move(position)

    def _tabu_aware_choice(
        self,
        candidates: list[Coordinate | None],
        require_known_safe: bool = False,
    ) -> Coordinate | None:
        """Prefer moves outside the tabu list, but never freeze because of it."""
        valid_moves = [
            candidate
            for candidate in candidates
            if candidate is not None
            and self._is_valid_move(candidate, require_known_safe=require_known_safe)
        ]
        if not valid_moves:
            return None

        valid_moves = self._filter_immediate_reversal(valid_moves)
        if not valid_moves:
            return None

        tabu_filtered = [
            candidate for candidate in valid_moves if candidate not in self.recent_path
        ]
        usable_moves = tabu_filtered or valid_moves
        return usable_moves[0]

    def _filter_immediate_reversal(
        self,
        candidates: list[Coordinate],
    ) -> list[Coordinate]:
        """Block direct back-and-forth oscillation during normal navigation."""
        if self.last_position is None:
            return candidates
        if self._is_airborne_mode():
            return candidates
        non_reversing = [
            candidate for candidate in candidates if candidate != self.last_position
        ]
        return non_reversing

    def _choose_flank_direction(self) -> Coordinate:
        """Pick the initial wall-following direction."""
        east_space = self.model.grid.width - 1 - self.pos[0]
        west_space = self.pos[0]
        if east_space > west_space:
            return (1, 0)
        if west_space > east_space:
            return (-1, 0)
        return (self.preferred_direction, 0)

    def _enqueue_frontier_neighbors(
        self,
        safe_cell: Coordinate,
        sensor_cells: set[Coordinate],
    ) -> None:
        """Queue unexplored neighbors of scanned safe cells for future verification."""
        for neighbor in self.model.moore_neighborhood(safe_cell):
            if neighbor in sensor_cells:
                continue
            if self.model.knowledge_base.get(neighbor) is not None:
                continue
            self.model.verification_queue.add(neighbor)

    def _is_valid_move(
        self,
        position: Coordinate,
        require_known_safe: bool = False,
    ) -> bool:
        """Return True if a candidate move is allowed under current knowledge."""
        if self.model.grid.out_of_bounds(position):
            return False
        state = self.model.knowledge_base.get(position, "UNEXPLORED")
        if state in {MINE, UNSAFE_BUFFER, DEAD_END}:
            return False
        if require_known_safe:
            return state in {SAFE, FINAL_PATH}
        return True

    def _adjacent_moves(self) -> list[Coordinate]:
        """Return all in-bounds Moore-adjacent moves excluding the current cell."""
        return self._adjacent_moves_from(self.pos)

    def _adjacent_moves_from(self, origin: Coordinate) -> list[Coordinate]:
        """Return all in-bounds Moore-adjacent moves from an arbitrary origin."""
        moves: list[Coordinate] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                destination = (origin[0] + dx, origin[1] + dy)
                if self.model.grid.out_of_bounds(destination):
                    continue
                moves.append(destination)
        return moves

    def _offset_position(self, delta: Coordinate) -> Coordinate | None:
        """Return an in-bounds offset position or None if it leaves the grid."""
        destination = (self.pos[0] + delta[0], self.pos[1] + delta[1])
        if self.model.grid.out_of_bounds(destination):
            return None
        return destination

    @staticmethod
    def _manhattan_distance(source: Coordinate, target: Coordinate) -> int:
        """Return the Manhattan distance between two coordinates."""
        return abs(source[0] - target[0]) + abs(source[1] - target[1])
