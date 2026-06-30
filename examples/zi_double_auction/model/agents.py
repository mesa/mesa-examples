import mesa

class Trader(mesa.Agent):
    def __init__(self, model, private_value: float):
        super().__init__(model)
        self.private_value = private_value   # reservation price (buyer) or cost (seller)
        self.cash = 0.0
        self.inventory = 0
        self.done_trading = False             # True once this agent's single unit has traded
        self.side: str = ""        
        first_delay = self.model.rng.exponential(self.model.mean_interarrival)
        self.model.schedule_event(self.act, after=first_delay)

    def wealth(self) -> float:
        return self.cash + self.inventory * self.private_value
    
    def _schedule_next_arrival(self):
        if self.done_trading:
            return
        delay = self.model.rng.exponential(self.model.mean_interarrival)
        self.model.schedule_event(self.act, after=delay)

    def act(self):
        raise NotImplementedError
    
class Buyer(Trader):

    def __init__(self, model, reservation_price: float):
        super().__init__(model, private_value=reservation_price)
        self.side = "bid"

    def act(self):
        if self.done_trading:
            return

        self.model.order_book.cancel_agent_order(self.unique_id, "bid")
        bid_price = self.model.rng.uniform(0, self.private_value)
        self.model.order_book.submit_bid(self.unique_id, bid_price, self.model.time)
        self.model.handle_arrival()

        self._schedule_next_arrival()

    def settle_purchase(self, price: float):
        self.cash -= price
        self.inventory += 1
        self.done_trading = True


class Seller(Trader):

    def __init__(self, model, cost: float):
        super().__init__(model, private_value=cost)
        self.side = "ask"
        self.inventory = 1  # sellers start endowed with the one unit they intend to sell

    def act(self):
        if self.done_trading:
            return

        self.model.order_book.cancel_agent_order(self.unique_id, "ask")
        ask_price = self.model.rng.uniform(self.private_value, self.model.max_valuation)
        self.model.order_book.submit_ask(self.unique_id, ask_price, self.model.time)
        self.model.handle_arrival()

        self._schedule_next_arrival()

    def settle_sale(self, price: float):
        self.cash += price
        self.inventory -= 1
        self.done_trading = True
