from mesa import Model
from mesa.space import MultiGrid
import random
from mesa import DataCollector
from agents import citizen


def c_healthy(model):
    return sum(1 for i in model.agents if i.state == "healthy")


def c_infected(model):
    return sum(1 for i in model.agents if i.state == "infected")


def c_immune(model):
    return sum(1 for i in model.agents if i.state == "immune")


def c_dead(model):
    return sum(1 for i in model.agents if i.state == "dead")


class dis_Model(Model):

    def __init__(
        self,
        n=100,
        infn=5,
        width=20,
        height=20,
        quarantine_threshold_strt=25,
        quarantine_threshold_stp=5,
        compliance=0.25,
    ):
        super().__init__()
        self.compliance_rate = compliance
        self.quarantine_thresh_up = quarantine_threshold_strt
        self.quarantine_thresh_lw = quarantine_threshold_stp
        self.infected_count = 0
        self.quarantine_status = False

        self.grid = MultiGrid(width, height, False)

        self.datacollector = DataCollector(
            model_reporters={
                "healthy": c_healthy,
                "immune": c_immune,
                "infected": c_infected,
                "dead": c_dead,
                "quarantine": lambda i: int(i.quarantine_status),
            }
        )

        for i in range(n):
            j = citizen(self)
            self.grid.place_agent(
                j, (random.randrange(width), random.randrange(height))
            )

        for i in range(infn):
            self.agents[i].state = "infected"

    def step(self):
        self.infected_count = c_infected(self)

        if self.infected_count > self.quarantine_thresh_up:
            self.quarantine_status = True
        elif self.infected_count < self.quarantine_thresh_lw:
            self.quarantine_status = False

        self.datacollector.collect(self)

        self.agents.do("step")
        # see_on_terminal(self)


def see_on_terminal(model):
    hthy = 0
    inf = 0
    im = 0
    ded = 0
    for i in model.agents:
        if i.state == "healthy":
            hthy += 1
        elif i.state == "infected":
            inf += 1
        elif i.state == "immune":
            im += 1
        elif i.state == "dead":
            ded += 1

    print(f"Step {model.steps}: H={hthy}, I={inf}, R={im}, D={ded}")
