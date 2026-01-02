"""
TankGameModel definition: game model with physics, collision, and explosion effects
"""

from mesa import Model
from mesa.space import MultiGrid
import random
import math
from typing import Set, Tuple, Dict, List

from agents import Tank, Shell, Target, Cloud


class RandomActivation:
    """Simple random activation scheduler (Mesa 3.x compatible)"""
    
    def __init__(self, model):
        self.model = model
        self._agents: List = []
    
    def add(self, agent):
        """Add agent to the scheduler"""
        self._agents.append(agent)
    
    def remove(self, agent):
        """Remove agent from the scheduler"""
        if agent in self._agents:
            self._agents.remove(agent)
    
    def step(self):
        """Execute all agents' step methods in random order"""
        random.shuffle(self._agents)
        for agent in self._agents[:]:  # use slice copy to avoid mutation during iteration
            if agent in self._agents:  # double-check in case removed during step
                agent.step()
    
    @property
    def agents(self):
        """Return the agent list (for compatibility)"""
        return self._agents


class TankGameModel(Model):
    """Tank game model - manages game state, physics rules, and agent interaction"""
    
    def __init__(
        self,
        angle: float = 45.0,
        power: float = 70.0,
        wind: float = 0.0,
        wall_position: int = 17,
        wall_height: int = 10,
        wall_block_wind: bool = False,
        target_movable: bool = False,
        width: int = 35,
        height: int = 35,
        seed: int | None = None
    ):
        """
        Initialize the game model.
        Args:
            angle: Launch angle (degrees), default 45.
            power: Launch power, default 70.
            wind: Wind strength, default 0.
            wall_position: X position of the wall, default 17.
            wall_height: Height of the wall, default 10.
            wall_block_wind: Whether the wall blocks wind, default False.
            target_movable: Whether the target moves vertically, default False (static).
            width: Grid width, default 35.
            height: Grid height, default 35.
            seed: Random seed, default None.
        """
        super().__init__(seed=seed)
        
        # UI parameters (modifiable)
        self.angle = angle
        self.power = power
        self.wind = wind
        self.wall_position = wall_position
        self.wall_height = wall_height
        self.wall_block_wind = wall_block_wind
        self.target_movable = target_movable
        
        # Physical constants
        self.g = 0.01  # gravitational acceleration
        self.vmax = 1.0  # maximum speed
        self._update_wind_acc()  # compute wind acceleration
        
        # Grid and scheduler
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        
        # State variables
        self.tank = None
        self.target = None
        self.cloud = None
        self.wall_cells: Set[Tuple[int, int]] = set()
        self.explosion_cells: Dict[Tuple[int, int], int] = {}  # {(x, y): ttl}
        self.explosion_centers: List[Tuple[int, int]] = []  # explosion centers
        self.trajectory_cells: Set[Tuple[int, int]] = set()  # shell trajectory cells
        
        # Step counter
        self.step_count = 0
        
        # Agent ID counter
        self._agent_id_counter = 0
        
        # For detecting wall parameter changes
        self._last_wall_position = wall_position
        self._last_wall_height = wall_height
        
        # Initialize game
        self._initialize_game()
    
    def next_id(self):
        """Generate the next unique agent ID"""
        self._agent_id_counter += 1
        return self._agent_id_counter
    
    def _update_wind_acc(self):
        """Update wind acceleration"""
        self.wind_acc = self.wind / 10000.0
    
    def _build_wall_cells(self):
        """Build the set of wall cells"""
        self.wall_cells.clear()
        ground_y = 1
        for y in range(ground_y, ground_y + self.wall_height):
            if 0 <= self.wall_position < self.grid.width and 0 <= y < self.grid.height:
                self.wall_cells.add((self.wall_position, y))
    
    def reset(self):
        """Reset game state: remove shells, recreate target and cloud"""
        # Clear trajectory
        self.clear_trajectory()

        # Remove all shells
        for agent in self.schedule.agents[:]:
            if isinstance(agent, Shell):
                self.grid.remove_agent(agent)
                self.schedule.remove(agent)
        
        # Remove existing target if present
        if self.target is not None:
            self.grid.remove_agent(self.target)
            self.schedule.remove(self.target)
            self.target = None
        
        # Remove existing cloud if present
        if self.cloud is not None:
            self.grid.remove_agent(self.cloud)
            self.schedule.remove(self.cloud)
            self.cloud = None
        
        # Clear explosion effects
        self.explosion_cells.clear()
        self.explosion_centers.clear()
        
        # Recreate cloud at (17.0, 30.0)
        cloud_id = self.next_id()
        self.cloud = Cloud(self, cloud_id, pos_f=(17.0, 30.0))
        self.schedule.add(self.cloud)
        
        # Recreate target at (width-2, random(10,25))
        target_y = random.randint(10, 25)
        target_id = self.next_id()
        self.target = Target(self, target_id, pos_f=(self.grid.width - 2, float(target_y)))
        self.schedule.add(self.target)
        
        # Resume running state
        self.running = True
        
        # Optional: reset step counter
        # self.step_count = 0
    
    def _initialize_game(self):
        """Initialize the game: create tank, cloud, target, and wall"""
        # Create tank at (1.0, 1.0)
        # Mesa 3.x: Agent(model, *args, **kwargs), unique_id passed via *args
        tank_id = self.next_id()
        self.tank = Tank(self, tank_id, pos=(1.0, 1.0))
        self.schedule.add(self.tank)
        
        # Create cloud at (17.0, 30.0)
        cloud_id = self.next_id()
        self.cloud = Cloud(self, cloud_id, pos_f=(17.0, 32.0))
        self.schedule.add(self.cloud)
        
        # Create target at (width-2, random(10,25))
        target_y = random.randint(1, 25)
        target_id = self.next_id()
        self.target = Target(self, target_id, pos_f=(self.grid.width - 2, float(target_y)))
        self.schedule.add(self.target)
        
        # Build wall cells
        self._build_wall_cells()

    def add_trajectory_cell(self, cell: Tuple[int, int]):
        """Record grid cells traversed by shells (only within bounds)"""
        x, y = cell
        if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            self.trajectory_cells.add((x, y))

    def clear_trajectory(self):
        """Clear current round's shell trajectory"""
        self.trajectory_cells.clear()
    
    @property
    def shell_exists(self) -> bool:
        """Check whether a shell exists"""
        for agent in self.schedule.agents:
            if isinstance(agent, Shell) and agent.alive:
                return True
        return False
    
    @property
    def target_exists(self) -> bool:
        """Check whether a target exists"""
        return self.target is not None and self.target in self.schedule.agents
    
    def fire(self):
        """Fire a shell"""
        # Only fire when no shell exists
        if self.shell_exists:
            return
        
        # Compute initial velocity
        speed = self.power / 100.0
        angle_rad = math.radians(self.angle)
        vx = math.sin(angle_rad) * speed
        vy = math.cos(angle_rad) * speed
        
        # Create shell at tank position
        # Mesa 3.x: Agent(model, *args, **kwargs), unique_id passed via *args
        shell_id = self.next_id()
        shell = Shell(self, shell_id, pos_f=self.tank.pos_f, vx=vx, vy=vy)
        self.schedule.add(shell)
    
    def _handle_target_hit(self, hit_x: int, hit_y: int):
        """Handle target hit: remove target and shell, create explosion effect"""
        # Clear trajectory immediately after a hit
        self.clear_trajectory()

        # Remove target
        if self.target is not None:
            self.grid.remove_agent(self.target)
            self.schedule.remove(self.target)
            self.target = None
        
        # Record explosion center
        self.explosion_centers.append((hit_x, hit_y))
        
        # Create explosion effect
        # Radius 1 (Manhattan distance ≤ 1): red, TTL=10
        # Radius 2 (Manhattan distance ≤ 2 but >1): yellow, TTL=10
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                manhattan_dist = abs(dx) + abs(dy)
                if manhattan_dist <= 2:
                    x = hit_x + dx
                    y = hit_y + dy
                    # Check if within grid bounds
                    if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                        self.explosion_cells[(x, y)] = 10  # TTL=10
    
    def _update_explosion_cells(self):
        """Update explosion effects: decrement TTL, remove when zero"""
        cells_to_remove = []
        for cell, ttl in self.explosion_cells.items():
            new_ttl = ttl - 1
            if new_ttl <= 0:
                cells_to_remove.append(cell)
            else:
                self.explosion_cells[cell] = new_ttl
        
        for cell in cells_to_remove:
            del self.explosion_cells[cell]
        
        # If all explosion effects are gone, clear explosion centers
        if not self.explosion_cells:
            self.explosion_centers.clear()
    
    def step(self):
        """Model step logic"""
        # 1. Check if target exists; if not, stop running (but still update explosions)
        if not self.target_exists:
            self.running = False
            # Even without target, update explosion TTL
            if self.explosion_cells:
                self._update_explosion_cells()
            return
        
        # 2. If wall params changed, rebuild wall cells
        if (self.wall_position != self._last_wall_position or 
            self.wall_height != self._last_wall_height):
            self._build_wall_cells()
            self._last_wall_position = self.wall_position
            self._last_wall_height = self.wall_height
        
        # 3. Update wind acceleration (if wind changed)
        self._update_wind_acc()
        
        # 4. Call all agents' step()
        self.schedule.step()
        
        # 5. Update explosion cell TTL
        self._update_explosion_cells()
        
        # 6. Increment step counter
        self.step_count += 1

