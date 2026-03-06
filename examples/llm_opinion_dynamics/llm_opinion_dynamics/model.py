import mesa
from mesa.discrete_space import OrthogonalMooreGrid
from mesa_llm.reasoning.cot import CoTReasoning

from .agent import OpinionAgent


class LLMOpinionDynamicsModel(mesa.Model):
    """
    An agent-based model of opinion dynamics powered by LLM agents.

    Unlike classical opinion dynamics models (e.g. Deffuant-Weisbuch) that use
    mathematical convergence rules, this model lets agents genuinely reason about
    their neighbors' arguments using a large language model, producing more
    nuanced and emergent opinion change patterns.

    Each agent holds a numeric opinion score (0-10) on a given topic.
    At each step, agents observe their neighbors and decide whether to update
    their opinion based on LLM-driven reasoning about the arguments presented.

    Args:
        n_agents (int): Number of agents in the simulation.
        width (int): Width of the grid.
        height (int): Height of the grid.
        topic (str): The debate topic agents will discuss.
        llm_model (str): LLM model string in 'provider/model' format.
        rng: Random number generator seed.
    """

    def __init__(
        self,
        n_agents: int = 9,
        width: int = 5,
        height: int = 5,
        topic: str = "Should artificial intelligence be regulated by governments?",
        llm_model: str = "gemini/gemini-2.0-flash",
        rng=None,
    ):
        super().__init__(rng=rng)

        self.topic = topic
        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        self.datacollector = mesa.DataCollector(
            agent_reporters={"opinion": "opinion"},
            model_reporters={
                "mean_opinion": lambda m: sum(a.opinion for a in m.agents)
                / len(m.agents),
                "opinion_variance": lambda m: self._variance(m),
            },
        )

        # Place agents on random cells
        cells = list(self.grid.all_cells)
        self.random.shuffle(cells)
        selected_cells = cells[:n_agents]

        for cell in enumerate(selected_cells):
            initial_opinion = self.random.uniform(0.0, 10.0)
            agent = OpinionAgent(
                model=self,
                reasoning=CoTReasoning,
                opinion=initial_opinion,
                topic=topic,
            )
            agent.cell = cell
            agent.pos = cell.coordinate

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

    @staticmethod
    def _variance(model):
        """Calculate opinion variance across all agents."""
        opinions = [a.opinion for a in model.agents]
        if not opinions:
            return 0.0
        mean = sum(opinions) / len(opinions)
        return sum((o - mean) ** 2 for o in opinions) / len(opinions)
