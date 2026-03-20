import mesa
from agents import Predator, Prey
from mesa.experimental.continuous_space import ContinuousSpace


class PredatorPreyModel(mesa.Model):
    "model duty is to simulate predator and prey behaviour in a continuous space"

    def __init__(
        self,
        width=100,
        height=100,
        initial_prey=100,
        initial_predators=20,  # there are more prey than predators in nature so we will set it like that
        prey_reproduce=0.04,
        predator_reproduce=0.05,  # it reproduce faster than prey to keep the population in check; this will affect how quickly the predator population can grow when food is abundant
        predator_gain_from_food=20,  # energy gained by predator when it eats a prey; this will affect how long the predator can survive without food and how quickly it can reproduce
        rng=None,
        **kwargs,  # purpose of kwargs allow extra parameters to be passed to the model if needed without changing the method signature
    ):
        super().__init__(rng=rng, **kwargs)

        self.width = width
        self.height = height
        self.prey_reproduce = prey_reproduce
        self.predator_reproduce = predator_reproduce
        self.predator_gain_from_food = predator_gain_from_food

        # again we need make sure it doesn't go off the edge so torus wrap around is used
        # ContinuousSpace requires a list of (min,max) bounds for each dimension.
        dims = [(0, self.width), (0, self.height)]
        # pass the model's random number generator so the space is reproducible
        self.space = ContinuousSpace(dims, torus=True, random=self.random)

        # creation of prey (unique_id and scheduling is now automatic!)
        for _ in range(initial_prey):
            # need start with random coordinates for each prey
            x = self.random.uniform(0, self.width)
            y = self.random.uniform(0, self.height)
            pos = (x, y)
            Prey(self.space, self, pos)

        # creation of predators
        for _ in range(initial_predators):
            # need start with random coordinates for each predator
            x = self.random.uniform(0, self.width)
            y = self.random.uniform(0, self.height)
            pos = (x, y)
            Predator(self.space, self, pos)

        # it keeps track of no. of prey and predators in each step of the simulation for analysis and visualization purposes
        self.data_collector = mesa.DataCollector(
            model_reporters={
                "Prey": lambda m: sum(1 for a in m.agents if isinstance(a, Prey)),
                "Predators": lambda m: sum(
                    1 for a in m.agents if isinstance(a, Predator)
                ),
            }
        )

    def step(self):
        # advancing to next step,model need to collect data before the agents take their actions
        self.data_collector.collect(
            self
        )  # collect the data for the current step of the simulation
        # Mesa 4.0 native agent activation (replaces the old scheduler)
        self.agents.shuffle_do("step")
