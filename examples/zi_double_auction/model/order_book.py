from dataclasses import dataclass


@dataclass
class Order:
    """A resting bid or ask submitted by one trader."""

    agent_id: int
    price: float
    side: str  # "bid" or "ask"
    timestamp: float  # model.time at submission; used for FIFO tie-breaks


@dataclass
class Trade:
    """A matched buyer/seller pair and the surplus implied by the clearing price."""

    time: float
    price: float
    buyer_id: int
    seller_id: int
    buyer_surplus: float
    seller_surplus: float


class OrderBook:
    """Minimal limit order book for a single-unit continuous double auction."""

    def __init__(self):
        """Create an empty bid and ask book."""

        self.bids: list[Order] = []
        self.asks: list[Order] = []

    def submit_bid(self, agent_id: int, price: float, time: float) -> None:
        """Add a bid order for the given agent."""

        self.bids.append(Order(agent_id, price, "bid", time))

    def submit_ask(self, agent_id: int, price: float, time: float) -> None:
        """Add an ask order for the given agent."""

        self.asks.append(Order(agent_id, price, "ask", time))

    def cancel_agent_order(self, agent_id: int, side: str) -> None:
        """Remove all resting orders for one agent on the requested side."""

        book = self.bids if side == "bid" else self.asks
        book[:] = [o for o in book if o.agent_id != agent_id]

    def best_bid(self) -> Order | None:
        """Return the highest bid, using earliest submission as the tie-breaker."""

        if not self.bids:
            return None
        # Highest price wins; earliest timestamp breaks ties (price-time priority)
        return max(self.bids, key=lambda o: (o.price, -o.timestamp))

    def best_ask(self) -> Order | None:
        """Return the lowest ask, using earliest submission as the tie-breaker."""

        if not self.asks:
            return None
        return min(self.asks, key=lambda o: (o.price, o.timestamp))

    def spread(self) -> float | None:
        """Return best ask minus best bid, or None when either side is empty."""

        bb, ba = self.best_bid(), self.best_ask()
        if bb is None or ba is None:
            return None
        return ba.price - bb.price

    def try_match(self, time: float) -> Trade | None:
        """Match the best bid and ask if they cross, clearing at their midpoint."""

        bb, ba = self.best_bid(), self.best_ask()
        if bb is None or ba is None:
            return None
        if bb.price < ba.price:
            return None  # no overlap, nothing to trade

        clearing_price = (bb.price + ba.price) / 2.0

        self.bids.remove(bb)
        self.asks.remove(ba)

        return Trade(
            time=time,
            price=clearing_price,
            buyer_id=bb.agent_id,
            seller_id=ba.agent_id,
            buyer_surplus=bb.price - clearing_price,
            seller_surplus=clearing_price - ba.price,
        )

    def clear_all_crosses(self, time: float) -> list[Trade]:
        """Repeatedly match crossing orders until the book no longer crosses."""

        trades = []
        while True:
            t = self.try_match(time)
            if t is None:
                break
            trades.append(t)
        return trades
