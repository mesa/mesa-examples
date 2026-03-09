import enum
from typing import List

import mesa


class Direction(enum.Enum):
    EAST = (1, 0)
    NORTH = (0, 1)


class LightState(enum.Enum):
    RED = 0
    GREEN = 1


class TrafficLightAgent(mesa.Agent):
    """
    An agent representing a single traffic light.

    Attributes:
        state (LightState): The current state of the light (RED or GREEN).
        direction (Direction): The flow of traffic this light controls.
    """

    def __init__(self, model: mesa.Model, state: LightState, direction: Direction):
        super().__init__(model)
        self.state = state
        self.direction = direction

    def step(self):
        # Traffic lights are passive; the Controller changes their state.
        pass


class CarAgent(mesa.Agent):
    """
    An agent representing a car in the grid.

    Attributes:
        direction (Direction): The direction the car is traveling.
        wait_time (int): Accumulator for time steps spent not moving.
    """

    def __init__(self, model: mesa.Model, direction: Direction):
        super().__init__(model)
        self.direction = direction
        self.total_wait_time = 0
        self.red_light_wait_time = 0

    def step(self):
        """
        Determines if the car can move forward based on obstacles and lights.
        """

        # Calculate the next coordinate based on direction
        next_x = (self.pos[0] + self.direction.value[0]) % self.model.grid.width
        next_y = (self.pos[1] + self.direction.value[1]) % self.model.grid.height
        next_pos = (next_x, next_y)

        can_move = True
        stopped_by_red_light = False
        cell_contents = self.model.grid.get_cell_list_contents([next_pos])

        for obj in cell_contents:
            if isinstance(obj, CarAgent):
                can_move = False
                break
            elif isinstance(obj, TrafficLightAgent):
                # Only stop if the light controls our direction and is red
                if obj.direction == self.direction and obj.state == LightState.RED:
                    can_move = False
                    stopped_by_red_light = True
                    break

        if can_move:
            self.model.grid.move_agent(self, next_pos)
        else:
            self.total_wait_time += 1
            if stopped_by_red_light:
                self.red_light_wait_time += 1


class IntersectionController(mesa.Agent):
    """
    A meta-agent that controls the traffic lights at an intersection.

    Attributes:
        smart (bool): If True, uses queue density to toggle. If False, uses fixed timer.
        lights (List[TrafficLightAgent]): The lights managed by this controller.
    """

    def __init__(
        self,
        model: mesa.Model,
        smart: bool,
        lights: list[TrafficLightAgent],
        sensor_range: int = 5,
        static_wait=15,
    ):
        super().__init__(model)
        self.smart = smart
        self.static_wait = static_wait
        self.lights = {l.direction: l for l in lights}  # Dictionary
        self.sensor_range = sensor_range
        self.timer = 0
        self.cooldown = 2  # Minimum steps before a light can change again

    def get_queue_density(self, light: TrafficLightAgent) -> int:
        """
        Calculates the number of cars waiting in the sensor zone approaching the light.
        """
        count = 0
        # Look backwards from the light based on the direction it controls
        dx, dy = light.direction.value
        for i in range(1, self.sensor_range + 1):
            check_x = (light.pos[0] - dx * i) % self.model.grid.width
            check_y = (light.pos[1] - dy * i) % self.model.grid.height

            check_pos = (check_x, check_y)
            if any(
                isinstance(a, CarAgent)
                for a in self.model.grid.get_cell_list_contents([check_pos])
            ):
                count += 1
        return count

    def toggle_lights(self):
        """
        Switches all lights managed by the controller.
        """
        for light in self.lights.values():
            light.state = (
                LightState.GREEN if light.state == LightState.RED else LightState.RED
            )
        self.timer = 0

    def step(self):
        self.timer += 1

        if not self.smart:
            # Static: Toggle every fixed interval
            if self.timer >= self.static_wait:
                self.toggle_lights()
        else:
            # Smart: Toggle based on dynamic queue density
            if self.timer >= self.cooldown:
                # Select lights by direction to find queue lengths
                east_light = self.lights[Direction.EAST]
                north_light = self.lights[Direction.NORTH]

                east_queue = self.get_queue_density(east_light)
                north_queue = self.get_queue_density(north_light)

                # If the current green light has a smaller queue than the red light, toggle
                if (
                    east_light.state == LightState.GREEN and north_queue > east_queue
                ) or (
                    north_light.state == LightState.GREEN and east_queue > north_queue
                ):
                    self.toggle_lights()
