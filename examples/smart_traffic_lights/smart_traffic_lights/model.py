import mesa
from .agents import (
    TrafficLightAgent,
    CarAgent,
    IntersectionController,
    LightState,
    Direction,
)


def track_total_wait_time(model: mesa.Model) -> int:
    """
    Helper function for the DataCollector to compute total wait time.
    """
    return sum(a.total_wait_time for a in model.agents if isinstance(a, CarAgent))


def track_red_light_wait_time(model: mesa.Model) -> int:
    """
    Helper function for the DataCollector to compute total wait time.
    """
    return sum(a.red_light_wait_time for a in model.agents if isinstance(a, CarAgent))


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
        self.grid = mesa.space.MultiGrid(width, height, torus=True)

        # Setup intersection (center of the grid)
        center_x, center_y = width // 2, height // 2

        # Create Traffic Lights
        light_east = TrafficLightAgent(self, LightState.GREEN, Direction.EAST)
        self.grid.place_agent(light_east, (center_x - 1, center_y))

        light_north = TrafficLightAgent(self, LightState.RED, Direction.NORTH)
        self.grid.place_agent(light_north, (center_x, center_y - 1))

        # Create Meta-Agent Controller
        controller = IntersectionController(
            self, smart=smart_lights, lights=[light_east, light_north], sensor_range=6
        )

        # Spawn Cars

        # Spawn East-bound cars on the horizontal road
        for i in range(num_cars_east):
            car = CarAgent(self, Direction.EAST)
            self.grid.place_agent(car, (self.random.randrange(width), center_y))

        # Spawn North-bound cars on the vertical road
        for i in range(num_cars_north):
            car = CarAgent(self, Direction.NORTH)
            self.grid.place_agent(car, (center_x, self.random.randrange(height)))

        # Setup Data Collection
        self.datacollector = mesa.DataCollector(
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
        sorted_east = sorted(east_cars, key=lambda a: a.pos[0], reverse=True)
        sorted_north = sorted(north_cars, key=lambda a: a.pos[1], reverse=True)

        # Execute movement in the specific order
        for car in sorted_east:
            car.step()
        for car in sorted_north:
            car.step()

        # Controller steps last to perceive the final positions of the cars
        self.agents_by_type[IntersectionController].do("step")

        self.datacollector.collect(self)
