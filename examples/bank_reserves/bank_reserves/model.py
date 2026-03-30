import mesa
import numpy as np
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import Bank, Person


def get_num_rich_agents(model):
    return len([a for a in model.agents if a.savings > model.rich_threshold])


def get_num_poor_agents(model):
    return len([a for a in model.agents if a.loans > 10])


def get_num_mid_agents(model):
    return len([
        a for a in model.agents
        if a.loans < 10 and a.savings < model.rich_threshold
    ])


def get_total_savings(model):
    return np.sum([a.savings for a in model.agents])


def get_total_wallets(model):
    return np.sum([a.wallet for a in model.agents])


def get_total_money(model):
    return get_total_wallets(model) + get_total_savings(model)


def get_total_loans(model):
    return np.sum([a.loans for a in model.agents])


class BankReservesModel(mesa.Model):

    grid_h = 20
    grid_w = 20

    def __init__(
        self,
        height=grid_h,
        width=grid_w,
        init_people=25,   # ✅ FIXED (was 2)
        rich_threshold=10,
        reserve_percent=50,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.height = height
        self.width = width
        self.init_people = init_people

        self.grid = OrthogonalMooreGrid(
            (self.width, self.height),
            torus=True,
            random=self.random
        )

        self.rich_threshold = rich_threshold
        self.reserve_percent = reserve_percent

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Rich": get_num_rich_agents,
                "Poor": get_num_poor_agents,
                "Middle Class": get_num_mid_agents,
                "Savings": get_total_savings,
                "Wallets": get_total_wallets,
                "Money": get_total_money,
                "Loans": get_total_loans,
            },
            agent_reporters={
                "Wealth": lambda x: getattr(x, "wealth", None)
            },
        )

        self.bank = Bank(self, self.reserve_percent)

        for _ in range(self.init_people):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)

            p = Person(self, True, self.bank, self.rich_threshold)
            p.move_to(self.grid[(x, y)])

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

    def run_model(self):
        for _ in range(self.run_time):
            self.step()