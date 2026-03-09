import mesa
import networkx as nx
from mesa.datacollection import DataCollector
from mesa.discrete_space import Network

from .agent import PersonAgent, State


class IllnessModel(mesa.Model):
    """
    A network model for simulating disease spread with dynamic link behavior.
    """

    steps = 0

    def __init__(
        self,
        *,
        num_nodes: int = 100,
        avg_degree: int = 4,
        p_transmission: float = 0.2,
        p_recovery: float = 0.1,
        p_mortality: float = 0.05,
        initial_infected: int = 5,
        link_dynamics: bool = True,
        seed=None,
        **kwargs,
    ) -> None:
        """
        Args:
            num_nodes: Number of agents.
            avg_degree: Average edges per node.
            p_transmission: Base probability of infecting a neighbor.
            p_recovery: Base probability of recovering.
            p_mortality: Base probability of dying.
            initial_infected: Number of agents starting as Infected.
            rng: Random number generator.
        """
        super().__init__(seed=seed)
        self.num_nodes = num_nodes
        self.pt = p_transmission
        self.pr = p_recovery
        self.pm = p_mortality

        # Probability that a link is active (starts at 1.0)
        self.link_dynamics = link_dynamics
        self.link_activity = 1.0

        # Initialize graph (Erdos-Renyi)
        prob_link = avg_degree / num_nodes
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=prob_link)
        nx.set_edge_attributes(self.G, True, "active")

        self.grid = Network(self.G, random=self.random)

        # For visualization
        self.pos = nx.spring_layout(
            self.G, k=0.01 / (num_nodes**0.5), iterations=100, seed=42
        )

        # Create and place agents
        for cell in self.grid.all_cells:
            # Generate random modifiers
            mod_infect = self.random.uniform(0.8, 1.2)
            mod_recover = self.random.uniform(0.8, 1.2)
            mod_caution = self.random.gauss(1.0, 0.35)  # Caution modifier

            agent = PersonAgent(
                model=self,
                mod_infect=mod_infect,
                mod_recover=mod_recover,
                mod_caution=mod_caution,
            )

            # Move agent to its cell
            agent.move_to(cell)

            # Initial infection
            if cell.coordinate < initial_infected:
                agent.state = State.INFECTED

        # Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Susceptible": lambda m: m.get_state_count(State.SUSCEPTIBLE),
                "Recovered": lambda m: m.get_state_count(State.RECOVERED),
                "Infected": lambda m: m.get_state_count(State.INFECTED),
                "Dead": lambda m: m.get_state_count(State.DEAD),
                "Active_Links": lambda m: m.count_active_links(),
                "Global_Caution": lambda m: m.link_activity,
            }
        )

        self.update_state_counts()
        self.datacollector.collect(self)

    def update_state_counts(self) -> None:
        """Helper to count agents in a specific state."""
        counts = dict.fromkeys(State, 0)
        for agent in self.agents:
            counts[agent.state] += 1
        self._current_state_counts = counts

    def get_state_count(self, state: State) -> int:
        """Retrieve cached state counts."""
        return self._current_state_counts.get(state, 0)

    def count_active_links(self) -> int:
        """Helper to count active edges."""
        return sum(1 for _, _, data in self.G.edges(data=True) if data.get("active"))

    def step(self) -> None:
        # Update global awareness
        infected = self.get_state_count(State.INFECTED)
        dead = self.get_state_count(State.DEAD)

        risk_factor = (infected + dead) / self.num_nodes
        self.link_activity = max(0.0, 1.0 - (risk_factor) * 3)

        # Update links
        if self.link_dynamics:
            for agent in self.agents:
                agent.update_link_opinions(self.link_activity)

        # Update network edges
        for u, v in self.G.edges():
            # Direct indexing on the space returns the Cell object
            cell_u = self.grid[u]
            cell_v = self.grid[v]

            if cell_u.agents and cell_v.agents:
                agent_u = cell_u.agents[0]
                agent_v = cell_v.agents[0]

                # Logic: Link is active only if both consent
                op_u = agent_u.link_opinions.get(v, True)
                op_v = agent_v.link_opinions.get(u, True)

                self.G[u][v]["active"] = op_u and op_v

        # Step
        self.agents.shuffle_do("step")

        self.update_state_counts()
        self.datacollector.collect(self)
