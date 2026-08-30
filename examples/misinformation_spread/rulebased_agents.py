import mesa


class RuleBasedBeliever(mesa.Agent):
    """
    Rule-based believer: believes and shares with fixed probability.
    No LLM reasoning, used as baseline comparison against LLMAgent version.
    """

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.believes = False
        self.shared = False

    def step(self):
        if self.random.random() < 0.8:
            self.believes = True
        if self.believes and self.random.random() < 0.8:
            self.shared = True
            self.model.spread_count += 1


class RuleBasedSkeptic(mesa.Agent):
    """
    Rule-based skeptic : rarely believes or shares.
    """

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.believes = False
        self.shared = False

    def step(self):
        if self.random.random() < 0.15:
            self.believes = True
        if self.believes and self.random.random() < 0.25:
            self.shared = True
            self.model.spread_count += 1


class RuleBasedSpreader(mesa.Agent):
    """
    Rule-based spreader: almost always believes and shares.
    """

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.believes = False
        self.shared = False

    def step(self):
        if self.random.random() < 0.95:
            self.believes = True
        if self.random.random() < 0.99:
            self.shared = True
            self.model.spread_count += 1
