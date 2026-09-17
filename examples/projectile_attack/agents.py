"""
Agent definitions, including Tank, Shell, Target, Wall
"""

from __future__ import annotations

from mesa.discrete_space import CellAgent, FixedAgent

PosF = tuple[float, float]
PosI = tuple[int, int]


class Tank(FixedAgent):
    # Tank agent - fixed position as the firing origin
    def __init__(self, model, pos: PosF = (1.0, 1.0)):
        super().__init__(model)
        self.pos_f: PosF = pos  # floating position

        # Place the tank on the grid
        grid_x, grid_y = int(pos[0]), int(pos[1])
        self.cell = self.model.grid[(grid_x, grid_y)]

    # Tank behavior per step - fixed in place, no movement
    def step(self) -> None:
        return


class Wall(FixedAgent):
    # Wall agent - fixed obstacle for visualization only
    def __init__(self, model, pos: PosI):
        super().__init__(model)
        grid_x, grid_y = int(pos[0]), int(pos[1])
        self.cell = self.model.grid[(grid_x, grid_y)]

    def step(self) -> None:
        return


class Shell(CellAgent):
    # Shell agent - affected by gravity; can collide
    def __init__(
        self,
        model,
        pos_f: PosF,
        vx: float = 0.0,
        vy: float = 0.0,
    ):
        """
        Args:
            model: Model instance.
            pos_f: Floating position (x, y). (Required)
            vx: Initial x velocity.
            vy: Initial y velocity.
        """
        super().__init__(model)

        self.pos_f: PosF = pos_f
        self.vx: float = vx
        self.vy: float = vy
        self.alive: bool = True

        # Initial grid position
        grid_x, grid_y = int(pos_f[0]), int(pos_f[1])
        self.cell = self.model.grid[(grid_x, grid_y)]

    def step(self) -> None:
        # Shell behavior per step: update position, apply physics, check collisions
        if not self.alive:
            return

        # Record current grid for trajectory display (treated as passed through next step)
        prev_grid = (int(self.pos_f[0]), int(self.pos_f[1]))
        self.model.add_trajectory_cell(prev_grid)

        # Get physical constants
        g = self.model.g
        vmax = self.model.vmax
        ground_y = 1

        # Apply gravity
        self.vy -= g

        # Speed clamp: normalize velocity vector so |v| ≤ vmax
        speed = (self.vx**2 + self.vy**2) ** 0.5
        if speed > vmax:
            scale = vmax / speed
            self.vx *= scale
            self.vy *= scale

        # Update position
        self.pos_f = (self.pos_f[0] + self.vx, self.pos_f[1] + self.vy)

        # Compute new grid position
        grid_x = int(self.pos_f[0])
        grid_y = int(self.pos_f[1])

        # Collision checks
        # 1. Out of grid bounds
        if (
            grid_x < 0
            or grid_x >= self.model.grid.width
            or grid_y < 0
            or grid_y >= self.model.grid.height
        ):
            self._die(reason="out_of_bounds")
            return

        # 2. Ground collision (y < ground_y)
        if self.pos_f[1] < ground_y:
            self._die(reason="ground")
            return

        # 3. Wall collision
        if (grid_x, grid_y) in self.model.wall_cells:
            self._die(reason="wall")
            return

        # 4. Target collision
        target = self.model.target
        if target is not None:
            target_grid_x = int(target.pos_f[0])
            target_grid_y = int(target.pos_f[1])
            if grid_x == target_grid_x and grid_y == target_grid_y:
                self._die()
                self.model._handle_target_hit(grid_x, grid_y)
                return

        # Update grid position
        self.cell = self.model.grid[(grid_x, grid_y)]

    def _die(self, reason: str | None = None) -> None:
        if not self.alive:
            return
        self.alive = False
        if reason is not None:
            self.model._handle_failure()
        if self in self.model.agents:
            self.remove()


class Target(CellAgent):
    # Target agent - fixed position; removed when hit
    def __init__(self, model, pos_f: PosF):
        super().__init__(model)

        self.pos_f: PosF = pos_f
        self.direction: int = 1
        self.move_tick: int = 0

        grid_x, grid_y = int(pos_f[0]), int(pos_f[1])
        self.cell = self.model.grid[(grid_x, grid_y)]

    # Target behavior per step - optional vertical movement
    def step(self) -> None:
        if not getattr(self.model, "target_movable", False):
            return

        # Throttle: move every 3 steps
        self.move_tick = (self.move_tick + 1) % 3
        if self.move_tick != 0:
            return

        # Bounce vertically within y ∈ [1, 25]
        min_y, max_y = 1, 25
        grid_height = self.model.grid.height
        max_y = min(max_y, grid_height - 1)
        min_y = max(min_y, 0)

        new_y = self.pos_f[1] + self.direction
        if new_y >= max_y:
            new_y = max_y
            self.direction = -1
        elif new_y <= min_y:
            new_y = min_y
            self.direction = 1

        new_x = self.pos_f[0]
        self.pos_f = (new_x, new_y)

        self.cell = self.model.grid[(int(new_x), int(new_y))]


class ResultText(FixedAgent):
    # Result text agent rendered on the grid (win/lose message)
    def __init__(self, model, pos: PosI, text: str, kind: str):
        super().__init__(model)
        self.text = text
        self.kind = kind
        self.cell = self.model.grid[(int(pos[0]), int(pos[1]))]

    def step(self) -> None:
        return
