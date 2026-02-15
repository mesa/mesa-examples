import gymnasium as gym
import mesa
import numpy as np
from agent import CitizenRL, CopRL
from mesa.examples.advanced.epstein_civil_violence.model import EpsteinCivilViolence
from ray.rllib.env import MultiAgentEnv

from .utility import create_initial_agents, grid_to_observation


class EpsteinCivilViolenceRL(EpsteinCivilViolence, MultiAgentEnv):
    """Custom environment class for the Epstein Civil Violence model with reinforcement learning.
    Inherits from EpsteinCivilViolence and MultiAgentEnv.
    """

    def __init__(
        self,
        width=20,
        height=20,
        citizen_density=0.5,
        cop_density=0.05,
        citizen_vision=4,
        cop_vision=4,
        legitimacy=0.8,
        max_jail_term=30,
        arrest_prob_constant=2.3,
        movement=True,
        max_iters=200,
    ):
        """Initialize the EpsteinCivilViolenceRL environment.

        Parameters:
        - width: Width of the grid.
        - height: Height of the grid.
        - citizen_density: Density of citizens in the grid.
        - cop_density: Density of cops in the grid.
        - citizen_vision: Vision range of citizens.
        - cop_vision: Vision range of cops.
        - legitimacy: Legitimacy parameter of the model.
        - max_jail_term: Maximum jail term for arrested citizens.
        - arrest_prob_constant: Constant used in arrest probability calculation.
        - movement: Flag indicating whether agents can move or not.
        - max_iters: Maximum number of iterations for the model.
        """
        super().__init__(
            width,
            height,
            citizen_density,
            cop_density,
            citizen_vision,
            cop_vision,
            legitimacy,
            max_jail_term,
            0,
            arrest_prob_constant,
            movement,
            max_iters,
        )

        # Defining RL specific attributes
        # Observation space is a grid with agent information centered around each agent
        self.observation_space = gym.spaces.Box(
            low=0, high=4, shape=(((cop_vision * 2 + 1) ** 2 - 1),), dtype=np.float32
        )
        # Action space is a tuple of two discrete actions, one for movement and one for arrest/protest
        self.action_space = gym.spaces.Tuple(
            (gym.spaces.Discrete(8), gym.spaces.Discrete(5))
        )

    def step(self, action_dict):
        """Perform a step in the environment.

        Parameters:
        - action_dict: Dictionary containing actions for each agent.

        Returns:
        - observation: Current observation of the environment.
        - rewards: Dictionary containing rewards for each agent.
        - done: Dictionary indicating if each agent is done.
        - truncated: Dictionary indicating if each agent is truncated.
        - info: Additional information about the step.
        """
        # Update the action dictionary for step
        self.action_dict = action_dict

        # Step the model
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        # Calculate rewards
        rewards = self.cal_reward()

        # Update matrix for observation space
        grid_to_observation(self, CitizenRL)
        observation = {}
        for agent in self.schedule.agents:
            observation[agent.unique_id] = [
                self.obs_grid[neighbor[0]][neighbor[1]]
                for neighbor in agent.neighborhood
            ]  # Get the values from the observation grid for the neighborhood cells

        # RL specific outputs for the environment
        done = {a.unique_id: False for a in self.agents}
        truncated = {a.unique_id: False for a in self.agents}
        truncated["__all__"] = np.all(list(truncated.values()))
        if self.time > self.max_iters:
            done["__all__"] = True
        else:
            done["__all__"] = False

        return observation, rewards, done, truncated, {}

    def cal_reward(self):
        rewards = {}
        for agent in self.agents:
            if isinstance(agent, CopRL):
                if agent.arrest_made:
                    # Cop is rewarded for making an arrest
                    rewards[agent.unique_id] = 1
                else:
                    rewards[agent.unique_id] = 0
            else:
                # An active agent is rewarded for its grievance
                # A jailed agent is penalized for its risk aversion
                if agent.jail_sentence > 0:
                    rewards[agent.unique_id] = -agent.risk_aversion
                else:
                    rewards[agent.unique_id] = (
                        0 if agent.condition == "Quiescent" else agent.grievance * 3
                    )

        return rewards

    def reset(self, *, seed=None, options=None):
        """Reset the environment after each episode.

        Parameters:
        - seed: Seed for random number generation.
        - options: Additional options for resetting the environment.

        Returns:
        - observation: Initial observation of the environment.
        - info: Additional information about the reset.
        """
        super().reset()
        self.grid = mesa.space.SingleGrid(self.width, self.height, torus=True)
        create_initial_agents(self)
        grid_to_observation(self)
        # Initialize action dictionary with no action
        self.action_dict = {a.unique_id: (0, 0) for a in self.agents}
        # Update neighbors for observation space
        for agent in self.agents:
            agent.update_neighbors()
        self.agents.shuffle_do("step")
        observation = {}
        for agent in self.agents:
            observation[agent.unique_id] = [
                self.obs_grid[neighbor[0]][neighbor[1]]
                for neighbor in agent.neighborhood
            ]  # Get the values from the observation grid for the neighborhood cells
        return observation, {}
