import random

import mesa
from agent import Trader
from mesa.datacollection import DataCollector


class Trading_interface(mesa.Model):
    """
    📊 Market Model

    - Manages global market state
    - Updates price using demand-supply imbalance
    - Generates OHLC data for ML agents
    """

    def __init__(self, n):
        super().__init__()

        # 📌 Current share price
        self.share_price = 300

        # 📌 Market capacity (not enforced yet)
        self.num_of_share = 30000

        # 📌 Reset every step
        self.total_demand = 0
        self.total_supply = 0

        # 📌 Create Trader agents
        Trader.create_agents(model=self, n=n)

        # 📊 Collect model-level data
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
        """
        📈 Price formation mechanism

        New Price =
            Old Price
            + (Demand - Supply) * sensitivity
            + random noise
        """

        imbalance = self.total_demand - self.total_supply

        # Market sensitivity parameter
        sensitivity = 0.005

        # Add Gaussian noise (market volatility)
        noise = random.gauss(0, 0.5)

        self.share_price += imbalance * sensitivity + noise

        # Prevent negative price
        self.share_price = max(1, self.share_price)

        # Reset counters for next step
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
