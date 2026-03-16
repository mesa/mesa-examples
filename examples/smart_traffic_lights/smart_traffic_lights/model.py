import mesa

from .agents import (
    CarAgent,
    Direction,
    IntersectionController,
    LightState,
    TrafficLightAgent,
)


def track_total_wait_time(model: mesa.Model) -> int:
    """
    Helper function for the DataCollector to compute total wait time.
    """
    return sum(a.total_wait_time for a in model.agents_by_type[CarAgent])


def track_red_light_wait_time(model: mesa.Model) -> int:
    """
    Helper function for the DataCollector to compute total wait time.
    """
    return sum(a.red_light_wait_time for a in model.agents_by_type[CarAgent])


class TrafficModel(mesa.Model):
    """
    The simulation model for the traffic network.

    Attributes:
        grid (mesa.space.MultiGrid): The spatial grid.
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        num_cars_east: int = 8,
        num_cars_north: int = 8,
        smart_lights: bool = False,
    ):
        super().__init__()
        self.width = width
        self.height = height

        # Initialize the new discrete_space grid
        self.grid = OrthogonalVonNeumannGrid(
            (width, height), torus=True, capacity=None
        )

        # Build a lookup table mapping (x, y) to Cell objects
        self.cells = {cell.coordinate: cell for cell in self.grid.all_cells}

        # Setup intersection (center of the grid)
        center_x, center_y = width // 2, height // 2

        # Create Traffic Lights
        light_east = TrafficLightAgent(self, LightState.GREEN, Direction.EAST)
        light_east.cell = self.cells[(center_x - 1, center_y)]

        light_north = TrafficLightAgent(self, LightState.RED, Direction.NORTH)
        light_north.cell = self.cells[(center_x, center_y - 1)]

        # Create Meta-Agent Controller
        IntersectionController(
            self, smart=smart_lights, lights=[light_east, light_north], sensor_range=6
        )

        # Spawn Cars

        # Spawn East-bound cars on the horizontal road
        for _ in range(num_cars_east):
            car = CarAgent(self, Direction.EAST)
            pos = (self.random.randrange(width), center_y)
            car.cell = self.cells[pos]
            
        # Spawn North-bound cars on the vertical road
        for _ in range(num_cars_north):
            car = CarAgent(self, Direction.NORTH)
            pos = (center_x, self.random.randrange(height))
            car.cell = self.cells[pos]

        # Setup Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Total_Wait_Time": track_total_wait_time,
                "Total_Red_Light_Wait_Time": track_red_light_wait_time,
            }
        )

    def step(self):
        # Get cars by direction
        all_cars = self.agents_by_type[CarAgent]
        east_cars = all_cars.select(lambda a: a.direction == Direction.EAST)
        north_cars = all_cars.select(lambda a: a.direction == Direction.NORTH)

        # Sort front-to-back: Cars with higher x (for East) or higher y (for North)
        # are "further ahead" and should move first to clear the path.
        sorted_east = sorted(east_cars, key=lambda a: a.cell.coordinate[0], reverse=True)
        sorted_north = sorted(north_cars, key=lambda a: a.cell.coordinate[1], reverse=True)

        # Execute movement in the specific order
        for car in sorted_east:
            car.step()
        for car in sorted_north:
            car.step()

        # Controller steps last to perceive the final positions of the cars
        self.agents_by_type[IntersectionController].do("step")

        self.datacollector.collect(self)
