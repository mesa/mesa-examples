import math

from mesa.experimental.continuous_space import ContinuousSpaceAgent


class Prey(ContinuousSpaceAgent):
    "a prey agent which has random motion in continuous space"

    def __init__(self, space, model, pos, speed=1.0):
        # unique_id is handled automatically by super()
        super().__init__(space, model)
        self.position = pos
        self.speed = speed

    # now we need make it motion randomso we need move agent to random position based it's spee
    def random_move(self):
        # random angle between 0 and 2pi would taken
        angle = self.random.uniform(0, 2 * math.pi)
        # change in x and y by trigonometry
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        # NEW POSITION  calculated
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy

        new_pos = (new_x, new_y)

        # to make sure it doesn't go off the map; use the new helper
        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)

        # update the stored position
        self.position = new_pos

    def step(self):
        # it calls the random move function to move the agent in each step of the simulation
        self.random_move()
        if self.random.random() < self.model.prey_reproduce:
            # Automatic registration to model.agents
            Prey(
                self.model.space,
                self.model,
                self.position,
                self.speed,
            )


class Predator(ContinuousSpaceAgent):
    "a predator agent which moves randomly but also hunts nearby prey"

    def __init__(
        self, space, model, pos, speed=1.5, energy=0
    ):  # it need faster than prey to catch it
        super().__init__(space, model)
        self.position = pos
        self.speed = speed
        self.energy = energy  # energy level of the predator

    def random_move(self):
        # here we make it hunt the prey if it is nearby
        # we will same random walk logic used in prey agent
        angle = self.random.uniform(0, 2 * math.pi)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed

        new_pos = (self.position[0] + dx, self.position[1] + dy)
        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)
        self.position = new_pos

    def step(self):
        self.random_move()
        self.energy -= 1  # predator lose energy each step

        neighbors, distances = self.get_neighbors_in_radius(
            radius=2.0
        )  # it get the nearby agents within a certain radius
        prey_neighbors = [
            obj for obj in neighbors if isinstance(obj, Prey)
        ]  # it filter the nearby agents to find the prey

        if prey_neighbors:
            prey_to_eat = self.random.choice(prey_neighbors)
            self.energy += self.model.predator_gain_from_food

            # Modern Mesa 4.0 removal (replaces all the contextlib fallbacks)
            prey_to_eat.remove()

        # Starvation
        if self.energy <= 0:
            self.remove()
            return

        # Reproduction
        if self.random.random() < self.model.predator_reproduce:
            self.energy /= 2  # reproduction costs energy
            Predator(
                self.model.space,
                self.model,
                self.position,
                self.speed,
                int(self.energy),
            )  # new predator starts with half parent's energy
