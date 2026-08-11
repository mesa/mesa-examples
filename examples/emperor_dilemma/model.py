import random

from agents import EmperorAgent, WhistleblowerAgent
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space.grid import OrthogonalMooreGrid


class EmperorModel(Model):
    """The Emperor's Dilemma Model — extended.

    Simulates how an unpopular norm sustains itself through fear and false
    enforcement, even when the vast majority privately reject it.

    Extensions over the base model:
    - Whistleblower agents who publicly defy the norm regardless of pressure
    - Belief gap metric tracking the illusion of consensus over time
    - Norm collapse detection — the step at which the norm loses its grip
    """

    def __init__(
        self,
        width=25,
        height=25,
        fraction_true_believers=0.05,
        k=0.125,
        homophily=False,
        fraction_whistleblowers=0.0,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.width = width
        self.height = height
        self.fraction_true_believers = fraction_true_believers
        self.k = k
        self.homophily = homophily
        self.fraction_whistleblowers = fraction_whistleblowers
        self.collapse_step = None

        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, capacity=1, random=self.random
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Compliance": compute_compliance,
                "Enforcement": compute_enforcement,
                "False Enforcement": compute_false_enforcement,
                "Belief Gap": compute_belief_gap,
                "Whistleblowers Defying": compute_whistleblowers_defying,
            }
        )

        self.init_agents()
        self.running = True
        self.datacollector.collect(self)

    def init_agents(self):
        num_agents = self.width * self.height
        num_believers = int(num_agents * self.fraction_true_believers)

        all_coords = [(x, y) for x in range(self.width) for y in range(self.height)]
        believer_coords = set()

        if self.homophily:
            center_x = self.random.randint(0, self.width - 1)
            center_y = self.random.randint(0, self.height - 1)
            start_x = center_x - int(num_believers**0.5) // 2
            start_y = center_y - int(num_believers**0.5) // 2

            for i in range(num_believers):
                bx = (start_x + (i % int(num_believers**0.5 + 1))) % self.width
                by = (start_y + (i // int(num_believers**0.5 + 1))) % self.height
                believer_coords.add((bx, by))
        else:
            believer_coords = set(random.sample(all_coords, num_believers))

        disbeliever_coords = [c for c in all_coords if c not in believer_coords]
        num_whistleblowers = int(len(disbeliever_coords) * self.fraction_whistleblowers)
        whistleblower_coords = set(
            random.sample(disbeliever_coords, num_whistleblowers)
        )

        for x, y in all_coords:
            cell = self.grid[(x, y)]

            if (x, y) in believer_coords:
                agent = EmperorAgent(self, 1, 1.0, self.k)
            elif (x, y) in whistleblower_coords:
                conviction = random.uniform(0.3, 0.5)
                agent = WhistleblowerAgent(self, -1, conviction, self.k)
            else:
                conviction = random.uniform(0.01, 0.38)
                agent = EmperorAgent(self, -1, conviction, self.k)

            agent.cell = cell
            agent.pos = (x, y)
            self.agents.add(agent)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        if self.collapse_step is None:
            compliance = compute_compliance(self)
            if compliance < 0.5:
                self.collapse_step = self.steps


def compute_compliance(model):
    if not model.agents:
        return 0
    return sum(1 for a in model.agents if a.compliance == 1) / len(model.agents)


def compute_enforcement(model):
    if not model.agents:
        return 0
    return sum(1 for a in model.agents if a.enforcement == 1) / len(model.agents)


def compute_false_enforcement(model):
    disbelievers = [a for a in model.agents if a.private_belief == -1]
    if not disbelievers:
        return 0
    return sum(1 for a in disbelievers if a.enforcement == 1) / len(disbelievers)


def compute_belief_gap(model):
    if not model.agents:
        return 0
    return sum(a.belief_gap for a in model.agents) / len(model.agents)


def compute_whistleblowers_defying(model):
    whistleblowers = [a for a in model.agents if a.agent_type == "whistleblower"]
    if not whistleblowers:
        return 0
    return sum(1 for a in whistleblowers if a.compliance != 1) / len(whistleblowers)
