"""
Axelrod Culture Model
=====================
Models how local cultural interactions produce global polarization.
Each agent has F features, each with Q possible traits. Agents interact
with neighbors with probability equal to cultural similarity, copying
one differing trait if interaction occurs.

Reference:
    Axelrod, R. (1997). The dissemination of culture.
    Journal of Conflict Resolution, 41(2), 203-226.
"""

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid

from axelrod_culture.agents import CultureAgent


def number_of_cultural_regions(model):
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
                if npos not in visited and npos in agent_by_pos:
                    if agent_by_pos[npos].culture == agent_by_pos[(cx, cy)].culture:
                        visited.add(npos)
                        queue.append(npos)
        regions += 1
    return regions


class AxelrodModel(Model):
    def __init__(self, width=10, height=10, F=3, Q=3, rng=None):
        super().__init__(rng=rng)
        self.width = width
        self.height = height
        self.F = F
        self.Q = Q

        self.grid = OrthogonalVonNeumannGrid(
            (width, height), torus=False, random=self.random
        )

        cultures = [
            [self.random.randrange(Q) for _ in range(F)] for _ in range(width * height)
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
        # Run N random pairwise interactions per step (one per agent on average)
        for _ in range(self.width * self.height):
            agent = self.random.choice(agent_list)
            neighbors = [a for a in agent.cell.neighborhood.agents if a is not agent]
            if neighbors:
                neighbor = self.random.choice(neighbors)
                agent.interact_with(neighbor)

        self.datacollector.collect(self)
