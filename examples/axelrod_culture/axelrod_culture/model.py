"""
Axelrod Culture Model
=====================

Models how local cultural interactions can produce global polarization.
Each agent has a "culture" consisting of f features, each taking one of
q possible integer traits. At each step, an agent picks a random neighbor
and interacts with probability equal to their cultural similarity. If they
interact, the agent copies one of the neighbor's differing traits.

Despite the tendency toward local convergence, stable cultural regions
can persist -- a phenomenon Axelrod called the "culture problem":
local homogenization coexisting with global diversity.

Key result: the number of stable cultural regions decreases with f
(more features -> more convergence) and increases with q (more traits
per feature -> more diversity and fragmentation).

Reference:
    Axelrod, R. (1997). The dissemination of culture: A model with local
    convergence and global polarization. Journal of Conflict Resolution,
    41(2), 203-226.
"""

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid

from axelrod_culture.agents import CultureAgent


def number_of_cultural_regions(model):
    """Count distinct stable cultural regions using flood fill on the grid."""
    visited = set()
    regions = 0
    agent_by_pos = {
        (int(a.cell.coordinate[0]), int(a.cell.coordinate[1])): a for a in model.agents
    }
    for pos in agent_by_pos:
        if pos in visited:
            continue
        queue = [pos]
        visited.add(pos)
        while queue:
            cx, cy = queue.pop()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                npos = (cx + dx, cy + dy)
                if (
                    npos not in visited
                    and npos in agent_by_pos
                    and agent_by_pos[npos].culture == agent_by_pos[(cx, cy)].culture
                ):
                    visited.add(npos)
                    queue.append(npos)
        regions += 1
    return regions


class AxelrodModel(Model):
    """Axelrod's model of cultural dissemination on a grid.

    Attributes:
        width (int): Grid width
        height (int): Grid height
        f (int): Number of cultural features per agent
        q (int): Number of possible traits per feature
        grid: OrthogonalVonNeumannGrid containing agents
    """

    def __init__(self, width=10, height=10, f=3, q=3, rng=None):
        super().__init__(rng=rng)

        self.width = width
        self.height = height
        self.f = f
        self.q = q

        self.grid = OrthogonalVonNeumannGrid(
            (width, height), torus=False, random=self.random
        )

        cultures = [
            [self.random.randrange(q) for _ in range(f)] for _ in range(width * height)
        ]

        CultureAgent.create_agents(self, width * height, cultures)

        for agent, cell in zip(self.agents, self.grid.all_cells.cells):
            agent.cell = cell

        self.datacollector = DataCollector(
            model_reporters={"Cultural Regions": number_of_cultural_regions}
        )
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        agent_list = list(self.agents)
        for _ in range(self.width * self.height):
            agent = self.random.choice(agent_list)
            neighbors = [a for a in agent.cell.neighborhood.agents if a is not agent]
            if neighbors:
                neighbor = self.random.choice(neighbors)
                agent.interact_with(neighbor)
        self.datacollector.collect(self)
