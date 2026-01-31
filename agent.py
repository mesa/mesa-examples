from mesa import Agent


class GamblingAgent(Agent):

    def __init__(self, model, skill, wealth, bet_size):
        super().__init__(model)
        self.skill = skill
        self.wealth = wealth
        self.bet_size = bet_size

    def step(self):
        p_win = 0.5 + self.model.alpha * self.skill
        if self.model.random.random() < p_win:
            self.wealth += self.bet_size
        else:
            self.wealth -= self.bet_size
