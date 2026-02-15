import os

import mesa
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from model import BoltzmannWealthModelRL
from stable_baselines3 import PPO


# Modify the MoneyModel class to take actions from the RL model
class MoneyModelRL(BoltzmannWealthModelRL):
    def __init__(self, n, width, height):
        super().__init__(n, width, height)
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "model", "boltzmann_money.zip"
        )
        self.rl_model = PPO.load(model_path)
        self.reset()

    def step(self):
        # Collect data
        self.datacollector.collect(self)

        # Get observations which is the wealth of each agent and their position
        obs = self._get_obs()

        action, _states = self.rl_model.predict(obs)
        self.action_dict = action
        self.schedule.step()


# Define the agent portrayal with different colors for different wealth levels
def agent_portrayal(agent):
    if agent.wealth > 10:
        color = "purple"
    elif agent.wealth > 7:
        color = "red"
    elif agent.wealth > 5:
        color = "orange"
    elif agent.wealth > 3:
        color = "yellow"
    else:
        color = "blue"

    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "Color": color,
        "r": 0.5,
    }
    return portrayal


if __name__ == "__main__":
    # Define a grid visualization
    grid = mesa.visualization.CanvasGrid(agent_portrayal, 10, 10, 500, 500)

    # Define a chart visualization
    chart = ChartModule(
        [{"Label": "Gini", "Color": "Black"}], data_collector_name="datacollector"
    )

    # Create a modular server
    server = ModularServer(
        MoneyModelRL, [grid, chart], "Money Model", {"N": 10, "width": 10, "height": 10}
    )
    server.port = 8521  # The default
    server.launch()
