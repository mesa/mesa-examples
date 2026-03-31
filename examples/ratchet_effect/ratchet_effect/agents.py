from mesa.discrete_space import FixedAgent


class WorkerAgent(FixedAgent):
    """A worker who can work from office or remotely.

    The ratchet effect is embedded in the lock_in attribute:
    - lock_in accumulates quickly when going remote (adaptation_rate)
    - lock_in decays very slowly when returning to office
    - the probability of returning to office is multiplied by (1 - lock_in),
      making it exponentially harder to reverse the transition the longer
      a worker has been remote.
    """

    def __init__(self, model, remote_preference: float, work_mode: str = "office"):
        """Initialize a WorkerAgent.

        Args:
            model: The RatchetEffectModel instance.
            remote_preference: Personal pull toward remote work, from -1.0
                (strongly prefers office) to 1.0 (strongly prefers remote).
            work_mode: Starting work arrangement, "office" or "remote".
        """
        super().__init__(model)
        self.remote_preference = remote_preference
        self.work_mode = work_mode
        # Workers who start remote begin with partial lock-in already built up
        self.lock_in = 0.25 if work_mode == "remote" else 0.0

    def step(self):
        """Execute one step: decide whether to switch work mode."""
        neighbors = list(self.cell.neighborhood.agents)
        n = len(neighbors)
        remote_fraction = (
            sum(1 for nb in neighbors if nb.work_mode == "remote") / n
            if n > 0
            else 0.0
        )

        if self.work_mode == "office":
            self._consider_going_remote(remote_fraction)
        else:
            self._accumulate_lock_in()
            if not self.model.shock_active:
                self._consider_returning_to_office()

    def _consider_going_remote(self, remote_fraction: float):
        """Decide whether to switch to remote work.

        Probability is driven by social contagion, personal preference,
        employer openness, and an external shock (e.g. pandemic).
        Going remote is relatively fast — this is the easy direction.
        """
        # Workers go remote when social pressure + preference exceeds a personal threshold.
        # The threshold creates genuine stability — not just slow convergence.
        social_pull = remote_fraction * self.model.social_influence
        pref_pull = max(0.0, self.remote_preference) * 0.04
        shock_boost = 0.9 if self.model.shock_active else 0.0

        net = social_pull + pref_pull + shock_boost
        # Only cross the threshold probabilistically
        p_go_remote = min(1.0, max(0.0, net - 0.12)) if not self.model.shock_active else min(1.0, net)

        if self.model.random.random() < p_go_remote:
            self.work_mode = "remote"
            self.lock_in = min(1.0, self.lock_in + self.model.adaptation_rate)

    def _accumulate_lock_in(self):
        """Accumulate lock-in each step spent remote.

        Represents home-office investment, habit formation, and relocation
        that build up over time and resist reversal.
        """
        self.lock_in = min(1.0, self.lock_in + self.model.adaptation_rate)

    def _consider_returning_to_office(self):
        """Decide whether to return to office work.

        THIS IS THE RATCHET: the probability of returning is multiplied by
        (1 - lock_in), so the more invested a worker is in remote work,
        the harder it becomes to reverse. Even strong institutional pressure
        cannot overcome high lock-in — the system resists going back.
        """
        institutional_pressure = max(0.0, 1.0 - self.model.employer_remote_openness)
        pref_push = max(0.0, -self.remote_preference) * 0.15

        # The ratchet: (1 - lock_in) makes return probability collapse
        # as lock_in approaches 1.0
        p_return = (
            (institutional_pressure + pref_push)
            * (1.0 - self.lock_in)
            * self.model.return_rate
        )
        p_return = max(0.0, min(1.0, p_return))

        if self.model.random.random() < p_return:
            self.work_mode = "office"
            # Partial release of lock_in — slow and incomplete (ratchet)
            self.lock_in = max(0.0, self.lock_in - 0.04)
