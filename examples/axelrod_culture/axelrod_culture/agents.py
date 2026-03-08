from mesa import Agent


class CultureAgent(Agent):
    def __init__(self, model, culture):
        super().__init__(model)
        self.culture = list(culture)

    def similarity(self, other):
        matches = sum(a == b for a, b in zip(self.culture, other.culture))
        return matches / len(self.culture)

    def interact_with(self, other):
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
