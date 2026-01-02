"""
Agent definitions: Tank, Shell, Target, Cloud
"""

from mesa import Agent


class Tank(Agent):
    """Tank agent - fixed position as the firing origin"""

    def __init__(self, model, unique_id=None, pos: tuple[float, float] = (1.0, 1.0)):
        """
        Initialize a tank.
        Args:
            model: Model instance.
            unique_id: Unique ID of the agent (Mesa 3.x autogenerates; kept for compatibility).
            pos: Position tuple (x, y), default (1.0, 1.0).
        """
        super().__init__(model)
        self.pos_f = pos  # floating position
        # Place the tank on the grid
        grid_x = int(pos[0])
        grid_y = int(pos[1])
        self.model.grid.place_agent(self, (grid_x, grid_y))

    def step(self):
        """Tank behavior per step - fixed in place, no movement"""


class Shell(Agent):
    """Shell agent - affected by gravity and wind; can collide"""

    def __init__(
        self,
        model,
        unique_id=None,
        pos_f: tuple[float, float] | None = None,
        vx: float = 0.0,
        vy: float = 0.0,
    ):
        """
        Initialize a shell.
        Args:
            model: Model instance.
            unique_id: Unique ID of the agent (Mesa 3.x autogenerates; kept for compatibility).
            pos_f: Floating position (x, y).
            vx: Initial x velocity.
            vy: Initial y velocity.
        """
        super().__init__(model)
        self.pos_f = pos_f  # floating position
        self.vx = vx  # x-axis velocity
        self.vy = vy  # y-axis velocity
        self.alive = True  # alive flag

        # Initial grid position
        grid_x = int(pos_f[0])
        grid_y = int(pos_f[1])
        self.model.grid.place_agent(self, (grid_x, grid_y))

    def step(self):
        """Shell behavior per step: update position, apply physics, check collisions"""
        if not self.alive:
            return

        # Record current grid for trajectory display (treated as passed through next step)
        prev_grid = (int(self.pos_f[0]), int(self.pos_f[1]))
        self.model.add_trajectory_cell(prev_grid)

        # Get physical constants
        g = self.model.g
        vmax = self.model.vmax
        wind_acc = self.model.wind_acc
        wall_block_wind = self.model.wall_block_wind
        wall_position = self.model.wall_position
        wall_height = self.model.wall_height
        ground_y = 1

        # Current grid position (integers for wind shadow check)
        grid_x = int(self.pos_f[0])
        grid_y = int(self.pos_f[1])

        # Check whether wind is blocked by wall.
        # Rule: if wind < 0, cells left of the wall within wall height ignore wind;
        # if wind > 0, cells right of the wall within wall height ignore wind.
        # The wall itself also ignores wind; height range includes the top.
        in_wall_shadow = False
        if wall_block_wind:
            within_wall_height = ground_y <= grid_y <= ground_y + wall_height
            if within_wall_height and (
                grid_x == wall_position
                or (wind_acc < 0 and grid_x < wall_position)
                or (wind_acc > 0 and grid_x > wall_position)
            ):
                in_wall_shadow = True

        # Apply wind if not in shadow
        if not in_wall_shadow:
            self.vx += wind_acc

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
            self.alive = False
            self.model.grid.remove_agent(self)
            return

        # 2. Ground collision (y < ground_y)
        if self.pos_f[1] < ground_y:
            self.alive = False
            self.model.grid.remove_agent(self)
            return

        # 3. Wall collision
        if (grid_x, grid_y) in self.model.wall_cells:
            self.alive = False
            self.model.grid.remove_agent(self)
            return

        # 4. Target collision
        target = self.model.target
        if target is not None:
            target_grid_x = int(target.pos_f[0])
            target_grid_y = int(target.pos_f[1])
            if grid_x == target_grid_x and grid_y == target_grid_y:
                # Target hit - model handles explosion and removal
                self.alive = False
                self.model.grid.remove_agent(self)
                # Notify model to handle target hit
                self.model._handle_target_hit(grid_x, grid_y)
                return

        # Update grid position
        self.model.grid.move_agent(self, (grid_x, grid_y))


class Target(Agent):
    """Target agent - fixed position; removed when hit"""

    def __init__(self, model, unique_id=None, pos_f: tuple[float, float] | None = None):
        """
        Initialize a target.
        Args:
            model: Model instance.
            unique_id: Unique ID of the agent (Mesa 3.x autogenerates; kept for compatibility).
            pos_f: Position tuple (x, y).
        """
        super().__init__(model)
        self.pos_f = pos_f  # floating position (fixed but kept consistent)
        self.direction = 1  # vertical direction: 1 up, -1 down
        self.move_tick = 0  # movement cadence counter; move every 3 steps

        # Place target on the grid
        grid_x = int(pos_f[0])
        grid_y = int(pos_f[1])
        self.model.grid.place_agent(self, (grid_x, grid_y))

    def step(self):
        """Target behavior per step - optional vertical movement"""
        if not getattr(self.model, "target_movable", False):
            return

        # Throttle: move every 3 steps
        self.move_tick = (self.move_tick + 1) % 3
        if self.move_tick != 0:
            return

        # Bounce vertically within y ∈ [1, 25]
        min_y, max_y = 1, 25
        grid_height = self.model.grid.height
        # Guard for smaller grids to avoid overflow
        max_y = min(max_y, grid_height - 1)
        min_y = max(min_y, 0)

        # Compute new position
        new_y = self.pos_f[1] + self.direction
        if new_y >= max_y:
            new_y = max_y
            self.direction = -1
        elif new_y <= min_y:
            new_y = min_y
            self.direction = 1

        new_x = self.pos_f[0]  # x fixed
        self.pos_f = (new_x, new_y)

        # Update grid position
        grid_x = int(new_x)
        grid_y = int(new_y)
        self.model.grid.move_agent(self, (grid_x, grid_y))


class Cloud(Agent):
    """Cloud agent - moves horizontally; affected by wind"""

    def __init__(
        self, model, unique_id=None, pos_f: tuple[float, float] = (17.0, 30.0)
    ):
        """
        Initialize a cloud.
        Args:
            model: Model instance.
            unique_id: Unique ID of the agent (Mesa 3.x autogenerates; kept for compatibility).
            pos_f: Position tuple (x, y), default (17.0, 30.0).
        """
        super().__init__(model)
        self.pos_f = pos_f  # floating position

        # Place cloud on the grid
        grid_x = int(pos_f[0])
        grid_y = int(pos_f[1])
        self.model.grid.place_agent(self, (grid_x, grid_y))

    def step(self):
        """Cloud behavior per step: horizontal movement with wind, wraps horizontally"""
        # Get wind
        wind = self.model.wind
        cloud_factor = 0.01  # cloud movement factor

        # Horizontal movement
        new_x = self.pos_f[0] + wind * cloud_factor

        # Wrap horizontally (re-enter from other side when leaving grid)
        grid_width = self.model.grid.width
        if new_x < 0:
            new_x += grid_width
        elif new_x >= grid_width:
            new_x -= grid_width

        # Update position
        self.pos_f = (new_x, self.pos_f[1])

        # Compute new grid position
        grid_x = int(self.pos_f[0])
        grid_y = int(self.pos_f[1])

        # Ensure grid_x stays valid (wraparound should guarantee validity)
        grid_x = grid_x % grid_width

        # Update grid position
        self.model.grid.move_agent(self, (grid_x, grid_y))
