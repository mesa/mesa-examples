import mesa
from mesa.discrete_space import OrthogonalMooreGrid
from mesa_llm.reasoning.cot import CoTReasoning

from .agent import SchellingAgent


class LLMSchellingModel(mesa.Model):
    """
    An LLM-powered Schelling Segregation model.

    The classical Schelling (1971) segregation model shows that even mild
    individual preferences for same-group neighbors lead to strong global
    segregation. In the classical model, agents move if fewer than a fixed
    threshold fraction of their neighbors share their group.

    This model replaces the threshold rule with LLM reasoning: agents
    describe their neighborhood in natural language and decide whether they
    feel comfortable staying or want to move. This produces richer dynamics
    where the decision depends on framing, context, and reasoning — not
    just a number.

    Reference:
        Schelling, T.C. (1971). Dynamic models of segregation.
        Journal of Mathematical Sociology, 1(2), 143-186.

    Args:
        width (int): Grid width.
        height (int): Grid height.
        density (float): Fraction of cells that are occupied.
        minority_fraction (float): Fraction of agents in group 1 (minority).
        llm_model (str): LLM model string in 'provider/model' format.
        rng: Random number generator.
    """

    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        density: float = 0.8,
        minority_fraction: float = 0.4,
        llm_model: str = "gemini/gemini-2.0-flash",
        rng=None,
    ):
        super().__init__(rng=rng)

        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, random=self.random
        )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "happy": lambda m: sum(
                    1 for a in m.agents if a.is_happy
                ),
                "unhappy": lambda m: sum(
                    1 for a in m.agents if not a.is_happy
                ),
                "segregation_index": lambda m: self._segregation_index(m),
            }
        )

        # Place agents on grid
        for cell in self.grid.all_cells:
            if self.random.random() < density:
                group = 1 if self.random.random() < minority_fraction else 0
                agent = SchellingAgent(
                    model=self,
                    reasoning=CoTReasoning,
                    group=group,
                )
                agent.cell = cell
                agent.pos = cell.coordinate

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        # Stop if everyone is happy
        if all(a.is_happy for a in self.agents):
            self.running = False

    @staticmethod
    def _segregation_index(model):
        """
        Measure segregation as the average fraction of same-group neighbors.
        Higher values indicate more segregation.
        """
        scores = []
        for agent in model.agents:
            neighbors = list(agent.cell.neighborhood.agents)
            if not neighbors:
                continue
            same = sum(1 for n in neighbors if n.group == agent.group)
            scores.append(same / len(neighbors))
        return sum(scores) / len(scores) if scores else 0.0
