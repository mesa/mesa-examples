import random

import mesa
from agent import Trader
from mesa.datacollection import DataCollector


class TradingInterface(mesa.Model):
    """Core market simulation model."""

    def __init__(self, n):
        super().__init__()

        # ======================================================
        # MARKET STATE VARIABLES
        # ======================================================

        self.share_price = 300
        self.num_of_share = 30000

        self.total_demand = 0
        self.total_supply = 0

        # ======================================================
        # CREATE AGENTS
        # ======================================================

        Trader.create_agents(model=self, n=n)

        # ======================================================
        # DATA COLLECTION
        # ======================================================

        self.datacollector = DataCollector(
            model_reporters={
                "Price": "share_price",
                "Demand": "total_demand",
                "Supply": "total_supply",
            },
            agent_reporters={"Wealth": lambda a: a.amount},
        )

        self.datacollector.collect(self)

    def update_price(self):
        """Adjust price using demand-supply imbalance + noise."""

        imbalance = self.total_demand - self.total_supply
        sensitivity = 0.005
        noise = random.gauss(0, 0.5)

        self.share_price += imbalance * sensitivity + noise
        self.share_price = max(1, self.share_price)

        self.total_demand = 0
        self.total_supply = 0

    def step(self):
        """
        🔄 Simulation Step Order (Corrected)

        1️⃣ Generate OHLC from previous price
        2️⃣ Agents make decisions
        3️⃣ Update price
        4️⃣ Collect data
        """

        # 1️⃣ Generate OHLC from current price
        self.open = self.share_price
        self.high = self.share_price + random.uniform(0, 1)
        self.low = self.share_price - random.uniform(0, 1)
        self.close = self.share_price
        self.volume = self.total_demand + self.total_supply

        # 2️⃣ Agents act (they now can access OHLC safely)
        self.agents.shuffle_do("step")

        # 3️⃣ Update price after trades
        self.update_price()

        print("Current Price:", self.share_price)

        # 4️⃣ Collect data
        self.datacollector.collect(self)
