import mesa
from mesa.experimental.continuous_space import ContinuousSpace


# simple replacement for Mesa 2-style RandomActivation scheduler; the
# built-in scheduling API changed in Mesa 3.x, so we keep a minimal class
# to retain compatibility with existing example code and data collector
# lambdas that look at `schedule.agents`.
class SimpleRandomActivation:
    def __init__(self, model):
        self.model = model
        self.agents = []

    def add(self, agent):
        self.agents.append(agent)

    def step(self):
        # random activation order without modifying original list
        order = list(self.agents)
        self.model.random.shuffle(order)
        for a in order:
            a.step()


# import agents with a fallback so the module works both as part of the
# examples package and when the directory is added to sys.path (e.g. running
# run.py directly).
try:
    from .agents import (  # here world model is created and we will add the agents in it
        Predator,
        Prey,
    )
except ImportError:
    from agents import (  # type: ignore[import-not-found]  # running as script
        Predator,
        Prey,
    )


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
        # Pass rng and kwargs to the new Mesa 4 Model class
        super().__init__(rng=rng, **kwargs)

        # 0. THESE MUST BE DEFINED FIRST!
        self.width = width
        self.height = height

        # now biological parameters are defined which will affect the behaviour of the agents in the simulation
        self.prey_reproduce = prey_reproduce
        self.predator_reproduce = predator_reproduce
        self.predator_gain_from_food = predator_gain_from_food

        # again we need make sure it doesn't go off the edge so torus wrap around is used
        # ContinuousSpace requires a list of (min,max) bounds for each dimension.
        dims = [(0, self.width), (0, self.height)]
        # pass the model's random number generator so the space is reproducible
        self.space = ContinuousSpace(dims, torus=True, random=self.random)
        # use our simple scheduler that mirrors Mesa 2 behaviour
        self.schedule = SimpleRandomActivation(
            self
        )  # it's a scheduler that randomly activates the agents in each step of the simulation

        # creation of prey(objects of prey class)
        for _ in range(initial_prey):
            # need start with random coordinates for each prey
            x = self.random.uniform(0, self.width)
            y = self.random.uniform(0, self.height)
            pos = (x, y)
            # get a fresh id and create the agent in the space
            agent_id = self.next_id()
            prey = Prey(agent_id, self.space, self, pos)
            # registration with model is automatic in ContinuousSpaceAgent.__init__
            self.schedule.add(prey)

        # creation of predators(objects of predator class)
        for _ in range(initial_predators):
            # need start with random coordinates for each predator
            x = self.random.uniform(0, self.width)
            y = self.random.uniform(0, self.height)
            pos = (x, y)
            agent_id = self.next_id()
            predator = Predator(agent_id, self.space, self, pos)
            self.schedule.add(predator)

        # it keeps track of no. of prey and predators in each step of the simulation for analysis and visualization purposes
        self.data_collector = mesa.DataCollector(
            model_reporters={
                "Prey": lambda m: sum(
                    1 for a in m.schedule.agents if isinstance(a, Prey)
                ),  # it's count the number of prey by checking instances of prey class in the schedule
                "Predators": lambda m: sum(
                    1 for a in m.schedule.agents if isinstance(a, Predator)
                ),  # it's count the number of predators by checking instances of predator class in the schedule
            }
        )

    def step(self):
        # advancing to next step,model need to collect data before the agents take their actions

        self.data_collector.collect(
            self
        )  # collect the data for the current step of the simulation
        self.schedule.step()  # it step all agents  during the scheduling process

    def next_id(self):
        """Return a new unique agent id (compatibility helper)."""
        nid = getattr(self, "agent_id_counter", 1)
        self.agent_id_counter = nid + 1
        return nid
