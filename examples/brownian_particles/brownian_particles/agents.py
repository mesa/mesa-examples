import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class Particle(ContinuousSpaceAgent):
    """
    A particle that moves around randomly (Brownian motion) and
    gently pushes away from nearby particles so they don't pile up.
    """

    def __init__(self, model, space, position, diffusion_rate=0.5, vision=3.0):
        super().__init__(space, model)
        self.position = np.array(position, dtype=float)
        self.diffusion_rate = diffusion_rate
        self.vision = vision
        self.n_neighbors = 0  # how many particles are nearby, used for coloring

    def step(self):
        # random kick - this is the Brownian part
        noise = self.model.rng.uniform(-1, 1, size=2) * self.diffusion_rate

        # soft repulsion: push away from particles that are too close
        neighbors, distances = self.get_neighbors_in_radius(radius=self.vision)
        neighbors = [n for n in neighbors if n is not self]
        self.n_neighbors = len(neighbors)

        repulsion = np.zeros(2)
        if neighbors:
            diff = self.space.calculate_difference_vector(
                self.position, agents=neighbors
            )
            # closer particles push harder
            for i, d in enumerate(distances[1:]):  # skip self (distance=0)
                if d > 0:
                    repulsion -= diff[i] / (d**2 + 0.1)
            repulsion *= 0.05

        self.position = self.position + noise + repulsion
