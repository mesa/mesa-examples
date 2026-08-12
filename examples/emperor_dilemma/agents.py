from mesa.discrete_space import FixedAgent


class EmperorAgent(FixedAgent):
    """A citizen in the Emperor's Dilemma model.

    Inherits from FixedAgent because citizens do not move — they're embedded
    in a social structure (grid or network) and only influence their neighbors.

    Each agent has a private belief they keep to themselves and a public
    behavior they show the world. These two things can be — and often are —
    completely different. That gap is the whole point of the model.
    """

    def __init__(self, model, private_belief, conviction, k):
        super().__init__(model)
        self.private_belief = private_belief
        self.conviction = conviction
        self.k = k
        self.agent_type = "citizen"

        self.compliance = self.private_belief
        self.enforcement = 0

    def step(self):
        neighbors = self._get_neighbors()
        num_neighbors = len(neighbors)

        if num_neighbors == 0:
            return

        sum_enforcement = sum(n.enforcement for n in neighbors)
        pressure = (-self.private_belief / num_neighbors) * sum_enforcement

        if pressure > self.conviction:
            self.compliance = -self.private_belief
        else:
            self.compliance = self.private_belief

        deviant_neighbors = sum(
            1 for n in neighbors if n.compliance != self.private_belief
        )
        w_i = deviant_neighbors / num_neighbors

        if (self.compliance != self.private_belief) and (
            pressure > (self.conviction + self.k)
        ):
            self.enforcement = -self.private_belief
        elif (self.compliance == self.private_belief) and (
            (self.conviction * w_i) > self.k
        ):
            self.enforcement = self.private_belief
        else:
            self.enforcement = 0

    def _get_neighbors(self):
        if self.cell is not None:
            return list(self.cell.neighborhood.agents)
        return []

    @property
    def belief_gap(self):
        return 0 if self.compliance == self.private_belief else 1


class WhistleblowerAgent(EmperorAgent):
    """A citizen who has decided they're done pretending.

    Always acts on private belief publicly regardless of social pressure.
    The key question: how many whistleblowers trigger a cascade collapse?
    """

    def __init__(self, model, private_belief, conviction, k):
        super().__init__(model, private_belief, conviction, k)
        self.agent_type = "whistleblower"
        self.compliance = self.private_belief
        self.enforcement = 0

    def step(self):
        neighbors = self._get_neighbors()
        num_neighbors = len(neighbors)

        # always act on private belief — pressure doesn't change this
        self.compliance = self.private_belief

        if num_neighbors == 0:
            return

        deviant_neighbors = sum(
            1 for n in neighbors if n.compliance != self.private_belief
        )
        w_i = deviant_neighbors / num_neighbors

        if (self.conviction * w_i) > self.k:
            self.enforcement = self.private_belief
        else:
            self.enforcement = 0
