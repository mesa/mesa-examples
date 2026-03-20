import math
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class Prey(ContinuousSpaceAgent):
    "a prey agent which has random motion in continuous space"

    # Added max_age to the initialization
    def __init__(self, space, model, pos, speed=1.0, max_age=40):
        super().__init__(space, model)
        self.position = pos
        self.speed = speed
        
        # Give them a random starting age so they don't all die on the exact same step!
        self.age = self.random.randint(0, max_age)
        self.max_age = max_age

    def random_move(self):
        angle = self.random.uniform(0, 2 * math.pi)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed

        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        new_pos = (new_x, new_y)

        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)
        self.position = new_pos

    def step(self):
        # 1. DYING OLD: Increase age, and die if too old
        self.age += 1
        if self.age > self.max_age:
            self.remove()
            return

        self.random_move()

        # Check surroundings for mating and overcrowding
        neighbors, _ = self.get_neighbors_in_radius(radius=2.5)
        prey_neighbors = [n for n in neighbors if isinstance(n, Prey)]

        # 2. MATING & CROWDING: Must have at least 1 mate nearby (>0), 
        # but won't reproduce if it's too overcrowded (<6)
        if 0 < len(prey_neighbors) < 6:
            if self.random.random() < self.model.prey_reproduce:
                Prey(self.model.space, self.model, self.position, self.speed, self.max_age)


class Predator(ContinuousSpaceAgent):
    "a predator agent which moves randomly but also hunts nearby prey"

    def __init__(self, space, model, pos, speed=1.5, energy=0, max_age=60): 
        super().__init__(space, model)
        self.position = pos
        self.speed = speed
        self.energy = energy
        
        # Dying old
        self.age = self.random.randint(0, max_age)
        self.max_age = max_age

    def random_move(self):
        angle = self.random.uniform(0, 2 * math.pi)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed

        new_pos = (self.position[0] + dx, self.position[1] + dy)
        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)
        self.position = new_pos

    def step(self):
        # 1. DYING OLD
        self.age += 1
        if self.age > self.max_age:
            self.remove()
            return

        self.random_move()
        self.energy -= 1  

        # Increased hunting radius so they can find food easier
        neighbors, _ = self.get_neighbors_in_radius(radius=4.0)  
        prey_neighbors = [n for n in neighbors if isinstance(n, Prey)]  

        if prey_neighbors:
            prey_to_eat = self.random.choice(prey_neighbors)
            self.energy += self.model.predator_gain_from_food
            prey_to_eat.remove()

        # Starvation
        if self.energy <= 0:
            self.remove()
            return

        # 3. ENERGY REPRODUCTION: They MUST have high energy (>30) to reproduce now!
        if self.energy > 30 and self.random.random() < self.model.predator_reproduce:
            self.energy /= 2  
            Predator(
                self.model.space,
                self.model,
                self.position,
                self.speed,
                int(self.energy),
                self.max_age
            ) 
