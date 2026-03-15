import mesa
import networkx as nx
from agents import Plant, Pollinator
from mesa.discrete_space import Network


def compute_alive_pollinators(model):
    # Fraction of original pollinators still alive
    if model.n_pollinators == 0:
        return 0
    alive = sum(1 for a in model.agents if isinstance(a, Pollinator) and a.alive)
    return alive / model.n_pollinators


def compute_alive_plants(model):
    # Fraction of original plants still alive
    if model.n_plants == 0:
        return 0
    alive = sum(1 for a in model.agents if isinstance(a, Plant) and a.alive)
    return alive / model.n_plants


def compute_cascade_depth(model):
    # Total plants that have died across all steps
    return model.total_plant_deaths


class PollinatorCascadeModel(mesa.Model):
    """
    Simulates cascade extinctions in a bipartite pollinator-plant network.

    Pollinators and plants are connected in a bipartite network where
    edges only exist between the two types. When pollinators die,
    plants lose support and eventually collapse.

    Args:
        n_pollinators: Number of pollinator agents.
        n_plants: Number of plant agents.
        connectivity: Probability of a pollinator-plant connection existing.
        extinction_schedule: Steps at which a pollinator is forcibly removed.
        rng: Random seed for reproducibility.
    """

    def __init__(
        self,
        n_pollinators=20,
        n_plants=30,
        connectivity=0.35,
        extinction_schedule=None,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.n_pollinators = n_pollinators
        self.n_plants = n_plants
        self.extinction_schedule = extinction_schedule or []
        self.current_step = 0
        self.total_plant_deaths = 0
        self.total_pollinator_deaths = 0

        # Bipartite graph - pollinators in set 0, plants in set 1
        # Each pair is connected with probability - connectivity
        G = nx.bipartite.random_graph(
            n_pollinators,
            n_plants,
            connectivity,
            seed=42,
        )

        # Wrap the graph in Network space
        # This creates a Cell for every node that agents can live on
        self.grid = Network(G, random=self.random)

        # Place pollinators on the first n_pollinators cells
        # Place plants on the remaining cells
        all_cells = list(self.grid.all_cells)

        for cell in all_cells[:n_pollinators]:
            Pollinator(
                model=self,
                cell=cell,
                specialization=self.random.uniform(0, 1),
            )

        for cell in all_cells[n_pollinators:]:
            Plant(
                model=self,
                cell=cell,
                resilience=self.random.uniform(0, 1),
            )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Alive Pollinators": compute_alive_pollinators,
                "Alive Plants": compute_alive_plants,
                "Cascade Depth": compute_cascade_depth,
            },
            agent_reporters={
                "Energy": lambda a: (a.energy if isinstance(a, Pollinator) else None),
                "Health": lambda a: (a.health if isinstance(a, Plant) else None),
                "Alive": "alive",
            },
        )
        self.datacollector.collect(self)

    def step(self):
        self.current_step += 1

        if self.current_step in self.extinction_schedule:
            self._trigger_extinction()

        # Activate all agents in random order each step
        self.agents.shuffle_do("step")

        # Count deaths before removing so totals stay accurate
        dead_plants = list(
            self.agents.select(lambda a: isinstance(a, Plant) and not a.alive)
        )
        dead_pollinators = list(
            self.agents.select(lambda a: isinstance(a, Pollinator) and not a.alive)
        )

        self.total_plant_deaths += len(dead_plants)
        self.total_pollinator_deaths += len(dead_pollinators)

        for agent in dead_plants + dead_pollinators:
            agent.remove()

        self.datacollector.collect(self)

    def _trigger_extinction(self):
        # Forcibly kill one random alive pollinator
        # Simulates an external shock like pesticide use or habitat loss
        alive_pollinators = self.agents.select(
            lambda a: isinstance(a, Pollinator) and a.alive
        )
        if alive_pollinators:
            target = self.random.choice(alive_pollinators.to_list())
            target.alive = False
            target.energy = 0
            self.total_pollinator_deaths += 1
            print(
                f"Step {self.current_step}: "
                f"Pollinator {target.unique_id} forcibly removed"
            )
