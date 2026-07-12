import mesa

from .agents import Buyer, Seller
from .order_book import OrderBook


class DoubleAuctionModel(mesa.Model):
    """Continuous double-auction model with zero-intelligence buyers and sellers."""

    def __init__(
        self,
        n_buyers: int = 25,
        n_sellers: int = 25,
        max_valuation: float = 100.0,
        mean_interarrival: float = 1.0,
        rng: int | None = None,
    ):
        """Create traders, the order book, and the model data collector."""

        super().__init__(rng=rng)

        self.max_valuation = max_valuation
        self.mean_interarrival = mean_interarrival
        self.order_book = OrderBook()

        self.clearing_price: float | None = None
        self.cumulative_volume: int = 0
        self.price_history: list[tuple[float, float]] = []  # (time, price)

        self._volume_since_last_tick: int = 0
        reservation_prices = self.rng.uniform(0, max_valuation, size=n_buyers).tolist()
        Buyer.create_agents(
            model=self, n=n_buyers, reservation_price=reservation_prices
        )

        costs = self.rng.uniform(0, max_valuation, size=n_sellers).tolist()
        Seller.create_agents(model=self, n=n_sellers, cost=costs)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "ClearingPrice": lambda m: m.clearing_price,
                "Volume": lambda m: m._volume_since_last_tick,
                "CumulativeVolume": lambda m: m.cumulative_volume,
                "Spread": lambda m: m.order_book.spread(),
                "BestBid": lambda m: (
                    m.order_book.best_bid().price if m.order_book.best_bid() else None
                ),
                "BestAsk": lambda m: (
                    m.order_book.best_ask().price if m.order_book.best_ask() else None
                ),
            },
            agent_reporters={
                "Wealth": lambda a: a.wealth(),
                "Cash": lambda a: a.cash,
                "Inventory": lambda a: a.inventory,
                "PrivateValue": lambda a: a.private_value,
                "Type": lambda a: type(a).__name__,
                "DoneTrading": lambda a: a.done_trading,
            },
        )

    def handle_arrival(self):
        """Settle trades while the book remains crossed after an order arrival."""

        agents_by_id = {a.unique_id: a for a in self.agents}
        while True:
            trade = self.order_book.try_match(self.time)
            if trade is None:
                break

            buyer = agents_by_id[trade.buyer_id]
            seller = agents_by_id[trade.seller_id]
            buyer.settle_purchase(trade.price)
            seller.settle_sale(trade.price)

            self.clearing_price = trade.price
            self.price_history.append((trade.time, trade.price))
            self.cumulative_volume += 1
            self._volume_since_last_tick += 1

    def step(self):
        """Collect one tick of data and reset the per-tick volume counter."""

        self.datacollector.collect(self)
        self._volume_since_last_tick = 0
