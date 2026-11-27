import mesa
import numpy as np
from brownian_particles.agents import Particle
from mesa.experimental.continuous_space import ContinuousSpace
from mesa.experimental.scenarios import Scenario


class BrownianScenario(Scenario):
    """
    Parameters for the Brownian particle model.
    These show up as sliders in the UI.
    """

    n_particles: int = 80
    width: float = 50.0
    height: float = 50.0
    diffusion_rate: float = 0.5  # how much each particle jumps per step
    vision: float = 4.0  # radius in which particles sense neighbors


class BrownianModel(mesa.Model):
    """
    A simple model where particles diffuse through a 2D continuous space.
    They follow Brownian motion with a soft repulsion to avoid overlapping.

    This is a basic example of continuous space in Mesa - good for understanding
    how agents move in non-grid environments.
    """

    def __init__(self, scenario=None):
        if scenario is None:
            scenario = BrownianScenario()

        super().__init__(scenario=scenario)

        self.space = ContinuousSpace(
            [[0, scenario.width], [0, scenario.height]],
            torus=True,
            random=self.random,
            n_agents=scenario.n_particles,
        )

        # scatter particles randomly across the space
        positions = self.rng.random(size=(scenario.n_particles, 2)) * np.array(
            [scenario.width, scenario.height]
        )

        Particle.create_agents(
            self,
            scenario.n_particles,
            self.space,
            position=positions,
            diffusion_rate=scenario.diffusion_rate,
            vision=scenario.vision,
        )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Avg Neighbors": lambda m: np.mean([a.n_neighbors for a in m.agents])
            }
        )

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
