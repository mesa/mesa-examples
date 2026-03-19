from mesa.discrete_space import CellAgent


class CultureAgent(CellAgent):
    """An agent with a cultural profile made of f features, each with q possible traits.

    Two agents interact with probability equal to their cultural similarity
    (fraction of features they share). If they interact, the focal agent
    copies one randomly chosen differing feature from the neighbor.

    Attributes:
        culture (list[int]): List of f integers, each in range [0, q)
    """

    def __init__(self, model, culture, cell):
        super().__init__(model)
        self.culture = list(culture)
        self.cell = cell

    def similarity(self, other):
        """Return fraction of features shared with another agent (0.0 to 1.0)."""
        matches = sum(a == b for a, b in zip(self.culture, other.culture))
        return matches / len(self.culture)

    def interact_with(self, other):
        """Interact with another agent based on cultural similarity.

        Interaction probability equals cultural similarity. If interaction
        occurs, copy one differing feature from the other agent.

        Note: sim == 1.0 guard prevents IndexError from empty differing list.
        sim == 0.0 guard skips interactions with no common ground.
        """
        sim = self.similarity(other)
        if sim == 0.0 or sim == 1.0:
            return
        if self.random.random() < sim:
            differing = [
                i
                for i in range(len(self.culture))
                if self.culture[i] != other.culture[i]
            ]
            feature = self.random.choice(differing)
            self.culture[feature] = other.culture[feature]
