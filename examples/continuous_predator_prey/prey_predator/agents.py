import math

from mesa.experimental.continuous_space import ContinuousSpaceAgent


class Prey(ContinuousSpaceAgent):
    # a prey agent which has random motion in continuous space

    def __init__(self, space, model, pos, speed=1.0, max_age=40):
        # unique_id is handled automatically by super()
        super().__init__(space, model)
        self.position = pos
        self.speed = speed

        # we need give them random starting age so they don't all die on the exact same step!
        self.age = self.random.randint(0, max_age)
        self.max_age = max_age  # it's maximum lifespan of prey agent

    # now we need make it motion random so we need move agent to random position based on it's speed
    def random_move(self):
        # random angle between 0 and 2pi would taken
        angle = self.random.uniform(0, 2 * math.pi)
        # change in x and y by trigonometry
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        # NEW POSITION calculated
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

        # 1. DYING OLD: increase age, and die if too old
        self.age += 1  # age increasing each step
        if self.age > self.max_age:
            self.remove()  # agent removed when too old
            return

        self.random_move()

        # check surroundings for mating and overcrowding
        neighbors, _ = self.get_neighbors_in_radius(
            radius=2.5
        )  # it get nearby agents within radius
        prey_neighbors = [
            n for n in neighbors if isinstance(n, Prey)
        ]  # it filter to find only prey

        # 2. MATING & CROWDING: must have at least 1 mate nearby (>0),
        # but won't reproduce if it's too overcrowded (<6)
        # it check not too lonely and not too crowded
        if (
            0 < len(prey_neighbors) < 6
            and self.random.random() < self.model.prey_reproduce
        ):
            # create new prey at the exact same position (asexual reproduction)
            Prey(self.model.space, self.model, self.position, self.speed, self.max_age)


class Predator(ContinuousSpaceAgent):
    # a predator agent which moves randomly but also hunts nearby prey

    def __init__(self, space, model, pos, speed=1.5, energy=0, max_age=60):
        # unique_id is handled automatically by super()
        super().__init__(space, model)
        self.position = pos
        self.speed = speed
        self.energy = energy  # energy level of the predator; it need for survival and reproduction

        # dying old - we need give them random starting age
        self.age = self.random.randint(0, max_age)
        self.max_age = max_age  # it's maximum lifespan of predator agent

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
        # 1. DYING OLD
        self.age += 1  # age increasing each step
        if self.age > self.max_age:
            self.remove()  # agent removed when too old
            return

        self.random_move()
        self.energy -= 1  # predator lose energy each step; it's cost of living

        # get nearby agents within hunting radius (increased from 2.0 so they can find food easier)
        neighbors, _ = self.get_neighbors_in_radius(radius=4.0)
        prey_neighbors = [
            n for n in neighbors if isinstance(n, Prey)
        ]  # it filter the nearby agents to find the prey

        if prey_neighbors:
            prey_to_eat = self.random.choice(
                prey_neighbors
            )  # choose random prey to eat
            self.energy += self.model.predator_gain_from_food  # gain energy from eating

            # Modern Mesa 4.0 removal (replaces all the contextlib fallbacks)
            prey_to_eat.remove()  # prey agent removed from simulation

        # Starvation - if energy reaches 0, predator dies
        if self.energy <= 0:
            self.remove()  # predator removed when starved
            return

        # 3. ENERGY REPRODUCTION: they MUST have high energy (>30) to reproduce now!
        if self.energy > 30 and self.random.random() < self.model.predator_reproduce:
            self.energy /= 2  # reproduction costs energy; parent loses half
            # create new predator with half of parent's energy
            Predator(
                self.model.space,
                self.model,
                self.position,
                self.speed,
                int(self.energy),
                self.max_age,
            )  # new predator starts with half parent's energy
