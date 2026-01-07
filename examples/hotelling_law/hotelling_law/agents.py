import math
import random

import numpy as np
from mesa.discrete_space import CellAgent


class StoreAgent(CellAgent):
    """An agent representing a store with a price and ability to move
    and adjust prices.
    """

    def __init__(self, model, cell, price=10, can_move=True, strategy="Budget"):
        # Initializes the store agent with a unique ID,
        # the model it belongs to,its initial price,
        # and whether it can move.
        super().__init__(model)
        self.price = price  # Initial price of the store.
        self.can_move = can_move  # Indicates if the agent can move.
        self.market_share = 0  # Initialize market share
        self.previous_market_share = 0  # Initialize previous market share
        self.strategy = strategy  # Store can be low cost (Budget)
        # / differential (Premium)
        self.cell = cell

    @property
    def pos(self):
        # Return the coordinate from the cell if it exists
        if hasattr(self, "cell") and self.cell is not None:
            return self.cell.coordinate
        return None

    @pos.setter
    def pos(self, new_pos):
        # The base Agent class attempts to set self.pos = None during __init__.
        # We can simply pass here, as position is now managed by the Grid/Cell.
        pass

    def estimate_market_share(self, new_position=None):
        position = new_position if new_position else self.cell
        nearby_consumers = position.get_neighborhood(radius=8).agents

        # Filter nearby agents to include only ConsumerAgents.
        nearby_consumers = [
            agent for agent in nearby_consumers if isinstance(agent, ConsumerAgent)
        ]
        market_share = len(nearby_consumers)
        return market_share

    def estimate_revenue(self, new_price=None):
        # Estimate revenue as product of price and market share
        price = new_price if new_price is not None else self.price
        estimated_market_share = self.estimate_market_share()
        return price * estimated_market_share

    def move(self):
        # Defines how the store agent moves in the environment.
        if not self.can_move:
            return

        best_position = self.cell
        best_market_share = self.estimate_market_share()

        for neighbor in self.cell.neighborhood:
            potential_market_share = self.estimate_market_share(new_position=neighbor)
            if potential_market_share >= best_market_share:
                best_market_share = potential_market_share
                best_position = neighbor

        self.cell = best_position

    def adjust_price(self):
        # Calculate competitor prices and the average competitor price
        competitor_prices = [
            store.price
            for store in self.model.agents_by_type[StoreAgent]
            if store is not self
        ]
        average_competitor_price = (
            np.mean(competitor_prices) if competitor_prices else self.price
        )

        # Calculate the current and average market share
        current_market_share = self.market_share
        all_market_shares = [
            store.market_share for store in self.model.agents_by_type[StoreAgent]
        ]
        average_market_share = np.mean(all_market_shares) if all_market_shares else 0

        # Calculate the market share change
        market_share_change = (
            (current_market_share - self.previous_market_share)
            / self.previous_market_share
            if self.previous_market_share > 0
            else 0
        )

        # Determine if the store's market share
        # significantly exceeds the average
        is_significantly_above_average = (
            current_market_share > average_market_share * 1.3
        )

        target_price = average_competitor_price
        # Base adjustment based on strategy
        if self.strategy == "Budget":
            target_price = average_competitor_price * 0.9
        elif self.strategy == "Premium":
            target_price = average_competitor_price * 1.1

        # Adjust price based on market share dynamics
        # and significant performance
        if market_share_change <= 0:
            adjustment_factor = 0.95 if self.strategy == "Budget" else 0.98
        elif is_significantly_above_average:
            # Increase price more aggressively if
            # significantly above average market share
            adjustment_factor = 1.2 if self.strategy == "Budget" else 1.1
        else:
            adjustment_factor = 1.02 if self.strategy == "Budget" else 1.05

        # Apply adjustments
        adjusted_price = self.price * adjustment_factor
        self.price = max(5.0, min(15.0, adjusted_price))
        # Ensure price within bounds
        # Ensure adherence to strategy
        self.price = max(5.0, min(self.price, target_price))

        # Update previous market share for next comparison
        self.previous_market_share = current_market_share

    def identify_competitors(self):
        competitors = []
        for agent in self.model.agents_by_type[StoreAgent]:
            if agent is not self:
                # Estimate market overlap as a measure of competition
                overlap = self.estimate_market_overlap(agent)
                if overlap > 0:  # If there's any market overlap,
                    # consider them competitors
                    competitors.append(agent)
        return competitors

    def estimate_market_overlap(self, other_store):
        """Estimate market overlap between this store and another store.
        This could be based on shared consumer base or other factors.
        """
        overlap = 0

        for consumer in self.model.agents_by_type[ConsumerAgent]:
            preferred_store = consumer.determine_preferred_store()
            if preferred_store in (self, other_store):
                overlap += 1

        return overlap

    def step(self):
        # Defines the actions the store agent takes
        # in each step of the simulation.
        if self.model.mode == "default":
            # In default mode, the agent can move and
            # adjust prices if allowed.
            self.move()
            self.adjust_price()
        elif self.model.mode == "moving_only":
            # In moving_only mode, the agent only moves if it can.
            self.move()
        elif self.model.mode == "pricing_only":
            # In pricing_only mode, the agent only adjusts its price.
            self.adjust_price()


class ConsumerAgent(CellAgent):
    """A consumer agent that chooses a store
    based on price and distance.
    """

    def __init__(self, model, cell, consumer_preferences):
        super().__init__(model)
        self.preferred_store = None
        self.cell = cell
        self.preference = consumer_preferences

    @property
    def pos(self):
        # Return the coordinate from the cell if it exists
        if hasattr(self, "cell") and self.cell is not None:
            return self.cell.coordinate
        return None

    @pos.setter
    def pos(self, new_pos):
        # The base Agent class attempts to set self.pos = None during __init__.
        # We can simply pass here, as position is now managed by the Grid/Cell.
        pass

    def determine_preferred_store(self):
        stores = self.model.agents_by_type[StoreAgent]

        if len(stores) == 0:  # Check if the stores AgentSet is empty
            return None

        min_score_stores = []
        min_score = float("inf")

        for store in stores:
            # Calculate score based on consumer preference
            if self.preference == "proximity":
                score = self.euclidean_distance(
                    self.cell.coordinate, store.cell.coordinate
                )
            elif self.preference == "price":
                score = store.price
            else:  # Default case includes both proximity and price
                score = store.price + self.euclidean_distance(
                    self.cell.coordinate, store.cell.coordinate
                )

            # Update the list of best stores if a new minimum score is found
            if score < min_score:
                min_score = score
                min_score_stores = [store]
            elif score == min_score:
                min_score_stores.append(store)

        # Randomly choose one of the best stores
        return random.choice(min_score_stores) if min_score_stores else None

    @staticmethod
    def euclidean_distance(pos1, pos2):
        """Calculate the Euclidean distance between two points."""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)

    def step(self):
        self.preferred_store = self.determine_preferred_store()
