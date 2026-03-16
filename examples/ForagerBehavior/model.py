import random

import mesa


class ForagerAgent(mesa.Agent):
    def __init__(self, model, energy=50.0):
        super().__init__(model)
        self.energy = energy
        self.state = "searching"

    def step(self):
        if self.state == "searching" and self.energy <= 20:
            self.state = "resting"
        elif self.state == "resting" and self.energy >= 80:
            self.state = "searching"

        self.energy = max(0, self.energy - 2.0)

        if self.state == "searching":
            self._move()
            self._forage()
        elif self.state == "resting":
            self._rest()

    def _move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        if neighbors:
            self.model.grid.move_agent(self, random.choice(neighbors))

    def _forage(self):
        if self.pos in self.model.resources and self.model.resources[self.pos] > 0:
            collected = min(15.0, self.model.resources[self.pos])
            self.model.resources[self.pos] -= collected
            self.energy = min(100, self.energy + collected)

    def _rest(self):
        self.energy = min(100, self.energy + 8.0)


class ForagerModel(mesa.Model):
    def __init__(self, n_agents=10, width=20, height=20, resource_density=0.3, seed=42):
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.resources = {}
        for x in range(width):
            for y in range(height):
                if self.random.random() < resource_density:
                    self.resources[(x, y)] = 20.0
        for _ in range(n_agents):
            agent = ForagerAgent(self)
            self.grid.place_agent(
                agent,
                (
                    self.random.randrange(width),
                    self.random.randrange(height),
                ),
            )
        self.datacollector = mesa.DataCollector(
            agent_reporters={"energy": "energy", "state": "state"},
            model_reporters={
                "searching": lambda m: sum(
                    1 for a in m.agents if a.state == "searching"
                ),
                "resting": lambda m: sum(1 for a in m.agents if a.state == "resting"),
                "total_resources": lambda m: sum(m.resources.values()),
            },
        )

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
        for pos in self.resources:
            self.resources[pos] = min(20.0, self.resources[pos] + 0.2)
