from mesa import Agent


class InvestorAgent(Agent):
    """
    While Banerjee’s Herding Effect highlights how investors blindly follow the crowd, Barber & Odean’s Overconfidence
    Theory explains their stubborn reliance on flawed personal judgment; together, they amplify irrational market
    volatility and pricing inefficiencies.
    """

    def __init__(self, model, opinion, confidence):
        super().__init__(model)
        self.opinion = opinion
        self.confidence = confidence
        """
        The core of the Barber & Odean theory lies in the critical distinction between gross returns
        and net returns, demonstrating how overconfident investors' excessive trading costs erode potential gains.
        """
        self.gross_wealth = (
            1000.0  # Theoretical Market Wealth Under a Buy-and-Hold Strategy (Gross)
        )
        self.net_wealth = 1000.0  # Actual Wealth After Deducting Frequent Trading Commissions and Fees (Net)
        self.trades = 0

    def update_opinion(self, other_opinion, mu):
        # The more inflated the confidence, the more stubborn the bias (resulting in a smaller effective mu
        effective_mu = mu / self.confidence
        self.opinion += effective_mu * (other_opinion - self.opinion)

    def execute_trade(self):
        # Barber & Odean: Overconfidence leads to excessive turnover rates.
        trade_prob = 0.05 * self.confidence
        if self.random.random() < trade_prob:
            self.trades += 1
            # Only net wealth accounts for the deduction of transaction friction costs.
            self.net_wealth -= self.model.transaction_cost
