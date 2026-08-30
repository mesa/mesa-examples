"""Unit tests for the swarm minefield mapping model."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import (  # noqa: E402
    DEAD_END,
    FINAL_PATH,
    MINE,
    SAFE,
    UNSAFE_BUFFER,
    MineAgent,
)
from model import MinefieldModel  # noqa: E402


class MinefieldModelTestCase(unittest.TestCase):
    """Behavioral tests for swarm coordination and path generation."""

    def setUp(self) -> None:
        self.model = MinefieldModel(
            width=20,
            height=20,
            mine_density=0.05,
            num_mines=0,
            seed=7,
        )

    def _mark_verified_vertical_corridor(self, x_coord: int) -> list[tuple[int, int]]:
        """Mark a 3-cell-wide corridor so each center cell is fully verified safe."""
        corridor: list[tuple[int, int]] = []
        for y_coord in range(self.model.height):
            for offset in (-1, 0, 1):
                cell = (x_coord + offset, y_coord)
                if self.model.grid.out_of_bounds(cell):
                    continue
                self.model.mark_safe(cell)
                if offset == 0:
                    corridor.append(cell)
        return corridor

    def test_register_mine_marks_neighbor_buffer(self) -> None:
        """A discovered mine should mark its full Moore buffer as unsafe."""
        target = (10, 10)
        self.model.register_mine(target)

        self.assertEqual(self.model.discovered_map[target], MINE)
        for neighbor in self.model.moore_neighborhood(target):
            if neighbor == target:
                continue
            self.assertEqual(self.model.discovered_map[neighbor], UNSAFE_BUFFER)

    def test_drone_step_consumes_battery_and_respects_move_radius(self) -> None:
        """A drone spends one battery unit and moves at most one cell."""
        drone = next(self.model.iter_drones())
        start = drone.pos

        drone.step()

        delta_x = abs(drone.pos[0] - start[0])
        delta_y = abs(drone.pos[1] - start[1])

        self.assertEqual(drone.battery, 599)
        self.assertLessEqual(max(delta_x, delta_y), 1)

    def test_battery_exhaustion_deactivates_drone(self) -> None:
        """A drone with one step of battery left becomes inactive after stepping."""
        drone = next(self.model.iter_drones())
        drone.battery = 1

        drone.step()

        self.assertEqual(drone.battery, 0)
        self.assertFalse(drone.is_active)

    def test_generate_safe_path_returns_continuous_route(self) -> None:
        """A* should return a valid path across discovered safe cells."""
        start = self.model.entry_points[0]
        safe_path = self._mark_verified_vertical_corridor(start[0])

        goal = safe_path[-1]
        path = self.model.generate_safe_path(goal)

        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        self.assertEqual(path, safe_path)
        self.assertTrue(
            all(self.model.discovered_map[position] == SAFE for position in path)
        )

    def test_generate_safe_path_returns_empty_when_goal_is_blocked(self) -> None:
        """A* should fail gracefully for blocked or unknown goals."""
        start = self.model.entry_points[0]
        goal = (start[0], self.model.height - 1)

        self.model.mark_safe(start)
        self.model.register_mine(goal)

        self.assertEqual(self.model.generate_safe_path(goal), [])

    def test_generate_safe_path_allows_cells_adjacent_to_buffer(self) -> None:
        """A verified safe cell may be used even if a neighbor is UNSAFE_BUFFER."""
        self._mark_verified_vertical_corridor(10)
        self.model.register_mine((12, 10))

        self.assertEqual(self.model.knowledge_base[(11, 10)], UNSAFE_BUFFER)
        self.assertEqual(self.model.knowledge_base[(10, 10)], SAFE)
        self.assertTrue(self.model._is_verified_safe((10, 10)))

    def test_generate_final_path_marks_winning_route(self) -> None:
        """The halt workflow should upgrade a discovered path to FINAL_PATH."""
        start = self.model.entry_points[0]
        safe_path = self._mark_verified_vertical_corridor(start[0])

        final_path = self.model.generate_final_path(safe_path[-1])

        self.assertEqual(final_path, safe_path)
        self.assertTrue(
            all(
                self.model.knowledge_base[position] == FINAL_PATH
                for position in final_path
            )
        )

    def test_model_stops_when_all_drones_are_inactive(self) -> None:
        """The model should terminate once no drone can continue exploring."""
        for drone in self.model.iter_drones():
            drone.battery = 1

        self.model.step()

        self.assertFalse(self.model.running)
        self.assertIn("No path found", self.model.path_status)

    def test_reserved_safe_zone_is_mine_free(self) -> None:
        """The hidden guaranteed corridor must remain physically clear of mines."""
        for position in self.model._safe_corridor_cells:
            contents = self.model.grid.get_cell_list_contents([position])
            self.assertFalse(any(isinstance(agent, MineAgent) for agent in contents))

    def test_step_stops_model_when_drone_reaches_top(self) -> None:
        """Reaching the top edge should generate a final path and halt the model."""
        drone = next(self.model.iter_drones())
        path = self._mark_verified_vertical_corridor(drone.pos[0])

        self.model.grid.move_agent(drone, path[-1])
        self.model.step()

        self.assertFalse(self.model.running)
        self.assertEqual(self.model.final_path[0], path[0])
        self.assertEqual(self.model.final_path[-1][1], self.model.height - 1)

    def test_dead_end_cells_remain_dead_end_after_rescan(self) -> None:
        """A retired dead-end cell must never become SAFE or BUFFER again."""
        drone = next(self.model.iter_drones())
        target = drone.pos

        self.model.mark_dead_end(target)
        self.assertEqual(self.model.knowledge_base[target], DEAD_END)

        self.model.mark_safe(target)
        self.assertEqual(self.model.knowledge_base[target], DEAD_END)

        self.model.register_mine((target[0] + 1, target[1]))
        self.assertEqual(self.model.knowledge_base[target], DEAD_END)

        drone.scan_surroundings()
        self.assertEqual(self.model.knowledge_base[target], DEAD_END)

    def test_drone_does_not_immediately_reverse_when_other_move_exists(self) -> None:
        """A drone should not bounce directly back to its last cell."""
        drone = next(self.model.iter_drones())
        current = drone.pos
        drone.last_position = (current[0], max(current[1] - 1, 0))
        alternative = (min(current[0] + 1, self.model.width - 1), current[1])

        chosen = drone._tabu_aware_choice([drone.last_position, alternative])

        self.assertEqual(chosen, alternative)

    def test_leadership_handoff_promotes_highest_drone(self) -> None:
        """A follower ahead of the leader should become the new leader."""
        drones = list(self.model.iter_drones())
        old_leader = self.model.leader_agent
        self.assertIsNotNone(old_leader)

        promoted = drones[-1]
        self.model.grid.move_agent(old_leader, (5, 4))
        self.model.grid.move_agent(promoted, (7, 8))

        self.model._evaluate_leadership()

        self.assertIs(self.model.leader_agent, promoted)
        self.assertEqual(promoted.role, "LEADER")
        self.assertEqual(old_leader.role, "FOLLOWER")
        self.assertIsNone(promoted.leader_agent)
        followers = [
            drone for drone in self.model.iter_drones() if drone is not promoted
        ]
        self.assertTrue(all(drone.leader_agent is promoted for drone in followers))
        self.assertTrue(all(drone.state == "RALLYING" for drone in followers))

    def test_free_flight_promotes_best_progress_drone(self) -> None:
        """A stuck leader should trigger free flight before picking a new leader."""
        drones = list(self.model.iter_drones())
        old_leader = self.model.leader_agent
        promoted = drones[-1]

        self.model.grid.move_agent(old_leader, (5, 4))
        self.model.grid.move_agent(promoted, (6, 4))
        self.model.start_free_flight()

        self.assertEqual(self.model.free_flight_ticks_remaining, 2)
        self.assertTrue(
            all(drone.state == "FREE_FLY" for drone in self.model.iter_drones())
        )

        self.model.grid.move_agent(promoted, (6, 7))
        self.model._update_free_flight()
        self.assertEqual(self.model.free_flight_ticks_remaining, 1)
        self.assertIs(self.model.leader_agent, old_leader)

        self.model._update_free_flight()
        self.assertEqual(self.model.free_flight_ticks_remaining, 0)
        self.assertIs(self.model.leader_agent, promoted)


if __name__ == "__main__":
    unittest.main()
