from mesa import Agent


class DecisionAgent(Agent):
    """
    Agent that can be temporarily interrupted (jailed)
    and later resume normal behavior.
    """

    def __init__(self, model):
        super().__init__(model)
        self.status = "FREE"
        self.release_time = None

    def act(self):
        """Normal agent behavior when free."""
        # placeholder for real logic

    def get_arrested(self, sentence: int, current_time: int):
        """
        Interrupt the agent for a fixed duration.
        """
        self.status = "IN_JAIL"
        self.release_time = current_time + sentence

    def step(self, current_time: int):
        """
        Either remain inactive if jailed or act normally.
        """
        if self.status == "IN_JAIL":
            if current_time >= self.release_time:
                self.status = "FREE"
                self.release_time = None
            return

        self.act()
