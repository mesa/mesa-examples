import random

import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import ConsumerAgent, StoreAgent


# The main model class that sets up and runs the simulation.
class HotellingModel(Model):
    """A model simulating competition and pricing strategies among stores
    within a defined environment. This simulation
    explores the dynamics of market competition, specifically focusing
    on how pricing and location strategies affect
    market outcomes in accordance with Hotelling's Law.

    Parameters:
        n_stores (int): The number of store agents participating
        in the simulation.Each agent acts as an individual store competing
        in the market.
        width (int), height (int): The dimensions of the simulation grid.
        These dimensions define the size of the environment in which the
        store agents operate.
        mode (str): Defines the operation mode of the simulation,
        influencing agent behavior. The available modes are:
        - 'default': In this mode, agents have the ability to both move
        (if enabled) and adjust their pricing in response
        to market conditions.
        - 'pricing_only': Agents focus solely on adjusting their prices
        to optimize market positioning and do not move regardless of
        their mobility settings.
        - 'moving_only': Agents can change their locations if they are
        enabled to move but will not adjust their prices. This mode
        is useful for studying the effects of spatial distribution
        without pricing competition.
        consumer_preferences (str): Defines the consumer preferences
        influencing agent behavior. The available options are:
        - 'default': Consumers will choose store based on min proximity
        and price
        - 'proximity': Consumers choose store based on proximity
        - 'price': Consumers choose store based on min price
        mobility_rate (int): Represents the percentage of agents that
        are allowed to move in the simulation environment. This parameter
        is a percentage of the total number of agents (N),
        determining how many of them have the capability to relocate.
        For example, a mobility rate of 80 means 80% of the store agents
        can change their locations if the operation mode permits movement.
        This allows for the exploration of market dynamics under
        varying degrees of agent mobility.

    Key Components:
        HotellingModel: The class encapsulating the simulation environment,
        responsible for initializing the agents, setting up the grid,
        and managing data collection for analysis.
        compute_average_price(model),compute_total_revenue(model):
        Functions that calculate key economic metrics from the
        simulation data for analysis.

    The model leverages Mesa's framework capabilities to simulate agent
    interactions, environmental constraints,and the emergent phenomena
    resulting from individual agent strategies within the
    market context defined by Hotelling's Law.
    """

    def __init__(
        self,
        n_stores=20,
        n_consumers=100,
        width=50,
        height=50,
        mode="default",
        consumer_preferences="default",
        environment_type="grid",
        mobility_rate=80,
        rng=None,
    ):
        # Initialize the model with parameters for number of agents,
        # grid size, mode of operation,environment type,
        # and mobility rate.
        super().__init__(rng=rng)
        # Total number of store agents in the model.
        self.num_agents = n_stores
        # Total number of consumers
        self.num_consumers = n_consumers
        # Percentage of agents that can move.
        self.mobility_rate = mobility_rate
        # Operational mode of the simulation affects agents' behavior
        self.mode = mode
        # Consumer preferences default / proximity / price
        self.consumer_preferences = consumer_preferences
        # Type of environment ('grid' or 'line').
        self.environment_type = environment_type

        # Initialize the spatial grid based on the specified environment type.
        if environment_type == "grid":
            self.grid = OrthogonalMooreGrid(
                (width, height), torus=True, random=self.random
            )  # A grid where multiple agents can occupy the same cell.
        elif environment_type == "line":
            self.grid = OrthogonalMooreGrid(
                (1, height), torus=True, random=self.random
            )  # A grid representing a line (single occupancy per cell).

        self._initialize_agents()

        # Define model-level reporters
        model_reporters = {"Price Variance": self.compute_price_variance}

        # Dynamically generate store-specific price collectors
        store_price_collectors = {
            f"Store_{i}_Price": self.get_store_price_lambda(i) for i in range(n_stores)
        }

        # Dynamically generate store-specific market_share collectors
        store_market_share_collectors = {
            f"Store_{i}_Market Share": self.get_market_share_lambda(i)
            for i in range(n_stores)
        }

        # Dynamically generate store-specific revenue collectors
        store_revenue_collectors = {
            f"Store_{i}_Revenue": self.get_revenue_lambda(i) for i in range(n_stores)
        }

        # Combine the dictionaries and pass them to DataCollector
        all_reporters = {
            **model_reporters,
            **store_price_collectors,
            **store_market_share_collectors,
            **store_revenue_collectors,
        }
        self.datacollector = DataCollector(model_reporters=all_reporters)

    @staticmethod
    def get_store_price_lambda(unique_id):
        """Return a lambda function that gets the
        price of a store by its unique ID.
        """
        return lambda m: next(
            (
                agent.price
                for agent in m.agents_by_type[StoreAgent]
                if agent.unique_id == unique_id
            ),
            0,
        )

    @staticmethod
    def get_market_share_lambda(unique_id):
        """Return a lambda function that gets the
        market_share of a store by its unique ID.
        """
        return lambda m: next(
            (
                agent.market_share
                for agent in m.agents_by_type[StoreAgent]
                if agent.unique_id == unique_id
            ),
            0,
        )

    @staticmethod
    def get_revenue_lambda(unique_id):
        """Return a lambda function that calculates the
        revenue of a store by its unique ID.
        """
        return lambda m: next(
            (
                agent.market_share * agent.price
                for agent in m.agents_by_type[StoreAgent]
                if agent.unique_id == unique_id
            ),
            0,
        )

    # initialize and place agents on the grid.
    def _initialize_agents(self):
        num_mobile_agents = int(
            self.num_agents * (self.mobility_rate / 100)
        )  # Calculate number of mobile agents.
        mobile_agents_assigned = 0

        for _ in range(self.num_agents):
            strategy = random.choices(["Budget", "Premium"], weights=[70, 30], k=1)[0]
            can_move = mobile_agents_assigned < num_mobile_agents
            if can_move:
                mobile_agents_assigned += 1

            StoreAgent(
                self,
                self.grid.all_cells.select_random_cell(),
                can_move=can_move,
                strategy=strategy,
            )

        # Place consumer agents
        for _ in range(self.num_consumers):
            ConsumerAgent(
                self,
                self.grid.all_cells.select_random_cell(),
                self.consumer_preferences,
            )

    # Method to advance the simulation by one step.
    def step(self):
        """Advance the model by one step."""
        # Collect data for the current step.
        self.datacollector.collect(self)
        # Activate all agents in random order
        self.agents.shuffle_do("step")
        # Update market dynamics based on the latest actions
        self.recalculate_market_share()

    def recalculate_market_share(self):
        # Reset market share for all stores directly
        for store in self.agents_by_type[StoreAgent]:
            store.market_share = 0

        for consumer in self.agents_by_type[ConsumerAgent]:
            preferred_store = consumer.determine_preferred_store()
            if preferred_store:
                preferred_store.market_share += 1

    # Utility method to run the model for a specified number of steps.
    def run_model(self, step_count=200):
        """Run the model for a certain number of steps."""
        for _ in range(step_count):
            self.step()

    # Method to export collected data to CSV files for further analysis.
    def export_data(self):
        """Export collected data to a CSV file."""
        model_data = self.datacollector.get_model_vars_dataframe()
        agent_data = self.datacollector.get_agent_vars_dataframe()
        # Adjust the file paths if necessary to match your project structure
        model_data.to_csv("output/model_data.csv")
        agent_data.to_csv("output/agent_data.csv")

    # Function to compute the average price of all store agents in the model.
    def compute_average_price(self):
        if len(self.store_agents) == 0:
            return 0
        return np.mean([agent.price for agent in self.agents_by_type[StoreAgent]])

    # Function to compute the average market share for all store agents,
    def compute_average_market_share(self):
        if not self.store_agents:
            return 0

        total_consumers = sum(
            agent.market_share for agent in self.agents_by_type[StoreAgent]
        )
        average_market_share = total_consumers / len(self.agents_by_type[StoreAgent])
        return average_market_share

    def compute_price_variance(self):
        return np.var([agent.price for agent in self.agents_by_type[StoreAgent]])
