from mesa import Agent, Model
from mesa.space import MultiGrid


class EnergyAgent(Agent):
    # --- Tunable Parameters ---
    LOW_ENERGY_THRESHOLD = 4
    MOVE_DECAY = 1.0
    REST_DECAY = 0.4

    def __init__(self, model, energy=10):
        super().__init__(model)
        self.energy = energy
        self.alive = True

    def step(self):
        if not self.alive:
            return

        is_resting = self.energy < self.LOW_ENERGY_THRESHOLD

        if is_resting:
            self.rest()
            decay = self.REST_DECAY
        else:
            self.move()
            decay = self.MOVE_DECAY

        self.energy = max(self.energy - decay, 0)

        if self.energy == 0:
            self._die()

    def move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        if neighbors:
            new_pos = self.random.choice(neighbors)
            self.model.grid.move_agent(self, new_pos)

    def rest(self):
        pass

    def _die(self):
        self.alive = False
        self.model.grid.remove_agent(self)
        self.remove()  # deregisters from model AgentSet


class EnergyModel(Model):
    def __init__(self, n=10, width=10, height=10):
        super().__init__()
        self.num_agents = n
        self.grid = MultiGrid(width, height, torus=True)

        for _ in range(self.num_agents):
            agent = EnergyAgent(self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

        self.running = True

    def step(self):
        # RandomActivation replacement in Mesa 3.x
        self.agents.shuffle_do("step")

        if len(self.agents) == 0:
            self.running = False
