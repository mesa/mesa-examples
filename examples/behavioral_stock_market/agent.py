import random

import mesa
import pandas as pd
from trend_predictor import TrendPredictor


class Trader(mesa.Agent):
    """Behavioral trader agent."""

    trend_model = TrendPredictor()  # Load ML model once

    def __init__(self, model):
        super().__init__(model)

        self.amount = random.randrange(10000, 50000, 1000)
        self.volume = random.randrange(1, 20)

        self.trader_type = random.choice(
            ["Fundamentalist", "TrendFollower", "RiskAverse"]
        )

        self.intrinsic_value = random.uniform(280, 320)
        self.memory = []

    def step(self):
        """Execute behavioral strategy."""
        self.memory.append(self.model.share_price)

        if self.trader_type == "Fundamentalist":
            self.fundamental_logic()
        elif self.trader_type == "TrendFollower":
            self.trend_logic()
        elif self.trader_type == "RiskAverse":
            self.risk_averse_logic()

    # 📊 Fundamentalist Strategy
    def fundamental_logic(self):
        if len(self.memory) < 3:
            return

        p1, p2, p3 = self.memory[-3:]

        if p1 < p2 < p3:
            self.buy()
        elif p1 > p2 > p3:
            self.sell()

    # 📈 TrendFollower Strategy (ML Based)
    def trend_logic(self):
        """ML-based trend prediction."""

        current_df = pd.DataFrame(
            [
                {
                    "open": self.model.open,
                    "high": self.model.high,
                    "low": self.model.low,
                    "close": self.model.close,
                    "volume": self.model.volume,
                }
            ]
        )

        prediction = Trader.trend_model.predict(current_df)[-1]

        if prediction == 1:
            self.buy()
        else:
            self.sell()

    # 🛑 Risk Averse Strategy
    def risk_averse_logic(self):
        """Sell quickly on loss, buy cautiously."""

        price = self.model.share_price

        if len(self.memory) > 1 and price < self.memory[-1]:
            self.sell()
            return

        if self.amount > price:
            small_volume = 1
            self.amount -= small_volume * price
            self.volume += small_volume
            self.model.total_demand += small_volume

    def buy(self):
        price = self.model.share_price
        max_buy = int(self.amount / price)

        if max_buy <= 0:
            return

        volume = random.randint(1, max_buy)

        self.amount -= volume * price
        self.volume += volume
        self.model.total_demand += volume

    def sell(self):
        if self.volume <= 0:
            return

        volume = random.randint(1, self.volume)

        self.amount += volume * self.model.share_price
        self.volume -= volume
        self.model.total_supply += volume
