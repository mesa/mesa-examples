import mesa
import networkx as nx
from mesa.discrete_space import Network
from mesa_llm.reasoning.react import ReActReasoning

from agents import BelieverAgent, SkepticAgent, SpreaderAgent
from rulebased_agents import RuleBasedBeliever, RuleBasedSkeptic, RuleBasedSpreader


class MisinformationModel(mesa.Model):
    """
    Simulates misinformation spread across a social network.

    Agents reason using an LLM about whether to believe and share
    a claim based on their personality type and message history.

    Args:
        n_believers: Number of believer agents.
        n_skeptics: Number of skeptic agents.
        n_spreaders: Number of spreader agents.
        connectivity: Probability of a connection between any two agents.
        misinformation_claim: The claim being spread in the simulation.
        use_llm: If True use LLM agents, if False use rule-based agents.
        rng: Random seed for reproducibility.
    """

    DEFAULT_CLAIM = (
        "A new study shows that drinking cold water after meals "
        "significantly disrupts digestion and causes weight gain."
    )

    def __init__(
        self,
        n_believers=3,
        n_skeptics=3,
        n_spreaders=2,
        connectivity=0.3,
        misinformation_claim=None,
        use_llm=True,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.n_believers = n_believers
        self.n_skeptics = n_skeptics
        self.n_spreaders = n_spreaders
        self.misinformation_claim = misinformation_claim or self.DEFAULT_CLAIM
        self.use_llm = use_llm
        self.spread_count = 0

        n_total = n_believers + n_skeptics + n_spreaders
        graph = nx.erdos_renyi_graph(n_total, connectivity, seed=42)
        self.grid = Network(graph, random=self.random)

        all_cells = list(self.grid.all_cells)

        for cell in all_cells[:n_believers]:
            BelieverAgent.create_agents(
                model=self,
                n=1,
                reasoning=ReActReasoning,
                llm_model="ollama/llama3",
                system_prompt=(
                    "You are a social media user who tends to trust "
                    "information easily and share it with others."
                ),
                internal_state={"personality": "believer", "cell": cell},
            )

        for cell in all_cells[n_believers: n_believers + n_skeptics]:
            SkepticAgent.create_agents(
                model=self,
                n=1,
                reasoning=ReActReasoning,
                llm_model="ollama/llama3",
                system_prompt=(
                    "You are a social media user who questions everything. "
                    "You rarely believe or share without strong evidence."
                ),
                internal_state={"personality": "skeptic", "cell": cell},
            )

        for cell in all_cells[n_believers + n_skeptics:]:
            SpreaderAgent.create_agents(
                model=self,
                n=1,
                reasoning=ReActReasoning,
                llm_model="ollama/llama3",
                system_prompt=(
                    "You are a social media user who shares everything "
                    "to maximize engagement. You do not fact-check."
                ),
                internal_state={"personality": "spreader", "cell": cell},
            )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Spread Count": "spread_count",
                "Believers Convinced": lambda m: sum(
                    1 for a in m.agents if isinstance(a, BelieverAgent) and a.believes
                ),
                "Skeptics Convinced": lambda m: sum(
                    1 for a in m.agents if isinstance(a, SkepticAgent) and a.believes
                ),
                "Spreaders Active": lambda m: sum(
                    1 for a in m.agents if isinstance(a, SpreaderAgent) and a.shared
                ),
            }
        )
        self.datacollector.collect(self)
        self._seed_misinformation()

    def _seed_misinformation(self):
        """
        Spreaders send the misinformation claim to all agents
        in the model to start the simulation.
        """
        spreaders = [a for a in self.agents if isinstance(a, SpreaderAgent)]
        all_agents = list(self.agents)
        for spreader in spreaders:
            recipients = [a for a in all_agents if a is not spreader]
            if recipients:
                spreader.send_message(
                    f"Have you heard? {self.misinformation_claim}",
                    recipients,
                )

    def step(self):
        print(f"\n--- Model step {self.steps} ---")
        self.agents.shuffle_do("step")
        self._propagate_sharing()
        self.datacollector.collect(self)

    def _propagate_sharing(self):
        """
        Agents who decided to share send the claim to all
        other agents, simulating social media sharing.
        """
        all_agents = list(self.agents)
        for agent in self.agents:
            if agent.shared:
                recipients = [a for a in all_agents if a is not agent]
                if recipients:
                    agent.send_message(
                        f"You should know this: {self.misinformation_claim}",
                        recipients,
                    )


class RuleBasedMisinformationModel(mesa.Model):
    """
    Rule-based version of the misinformation model.
    Identical network structure to MisinformationModel but agents
    use fixed probabilities instead of LLM reasoning.
    Used to compare against LLM-driven behavior.
    """

    DEFAULT_CLAIM = MisinformationModel.DEFAULT_CLAIM

    def __init__(
        self,
        n_believers=3,
        n_skeptics=3,
        n_spreaders=2,
        connectivity=0.3,
        misinformation_claim=None,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.n_believers = n_believers
        self.n_skeptics = n_skeptics
        self.n_spreaders = n_spreaders
        self.misinformation_claim = misinformation_claim or self.DEFAULT_CLAIM
        self.spread_count = 0

        n_total = n_believers + n_skeptics + n_spreaders
        rgaph = nx.erdos_renyi_graph(n_total, connectivity, seed=42)
        self.grid = Network(graph, random=self.random)

        all_cells = list(self.grid.all_cells)

        for cell in all_cells[:n_believers]:
            RuleBasedBeliever(model=self, cell=cell)

        for cell in all_cells[n_believers: n_believers + n_skeptics]:
            RuleBasedSkeptic(model=self, cell=cell)

        for cell in all_cells[n_believers + n_skeptics:]:
            RuleBasedSpreader(model=self, cell=cell)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Spread Count": "spread_count",
                "Believers Convinced": lambda m: sum(
                    1
                    for a in m.agents
                    if isinstance(a, RuleBasedBeliever) and a.believes
                ),
                "Skeptics Convinced": lambda m: sum(
                    1
                    for a in m.agents
                    if isinstance(a, RuleBasedSkeptic) and a.believes
                ),
                "Spreaders Active": lambda m: sum(
                    1 for a in m.agents if isinstance(a, RuleBasedSpreader) and a.shared
                ),
            }
        )
        self.datacollector.collect(self)

    def step(self):
        print(f"\n--- Rule-based step {self.steps} ---")
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
