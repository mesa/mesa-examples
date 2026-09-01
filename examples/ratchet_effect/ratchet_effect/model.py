from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import WorkerAgent


class RatchetEffectModel(Model):
    """The Ratchet Effect Model — Remote Work Edition.

    Demonstrates the ratchet effect in labor markets: workers can easily shift
    to remote work but strongly resist returning to the office once adapted.

    The asymmetry has two reinforcing mechanisms:
    1. Structural: adaptation_rate >> return_rate (going remote is faster)
    2. Lock-in: p_return is multiplied by (1 - lock_in), so each step spent
       remote makes returning harder — home office investments, habit formation,
       and residential relocation accumulate and resist reversal.

    An optional external shock (e.g. a pandemic) can trigger a rapid shift
    toward remote work, demonstrating path dependency: the post-shock
    equilibrium is permanently different from the pre-shock state even after
    the shock ends.

    Reference: https://github.com/projectmesa/mesa-examples/issues/249
    """

    def __init__(
        self,
        n_workers: int = 100,
        width: int = 15,
        height: int = 15,
        initial_remote_fraction: float = 0.05,
        adaptation_rate: float = 0.025,
        return_rate: float = 0.35,
        social_influence: float = 0.35,
        employer_remote_openness: float = 0.2,
        shock_step: int = 30,
        shock_duration: int = 8,
        rng=None,
    ):
        """Initialize the RatchetEffectModel.

        Args:
            n_workers: Number of worker agents. Must not exceed width * height.
            width: Grid width.
            height: Grid height.
            initial_remote_fraction: Fraction of workers starting remote.
            adaptation_rate: How fast lock-in accumulates each step remote.
                Higher = faster adaptation, stronger ratchet.
            return_rate: Structural asymmetry factor for returning to office.
                Lower = stronger ratchet (harder to return).
            social_influence: Weight of neighbors' work mode on own decision.
            employer_remote_openness: How remote-friendly the employer is (0-1).
                Higher = more permissive, less pressure to return.
            shock_step: Step at which an external shock hits (0 = no shock).
            shock_duration: How many steps the shock lasts.
            rng: Random seed for reproducibility.
        """
        super().__init__(rng=rng)

        self.n_workers = n_workers
        self.width = width
        self.height = height
        self.adaptation_rate = adaptation_rate
        self.return_rate = return_rate
        self.social_influence = social_influence
        self.employer_remote_openness = employer_remote_openness
        self.shock_step = shock_step
        self.shock_duration = shock_duration
        self.shock_active = False

        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, capacity=1, random=self.random
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Remote Workers (%)": _pct_remote,
                "Avg Lock-in": _avg_lock_in,
                "Return Resistance": _return_resistance,
                "Shock": lambda m: 1 if m.shock_active else 0,
            }
        )

        self._place_workers(initial_remote_fraction)
        self.running = True
        self.datacollector.collect(self)

    def _place_workers(self, initial_remote_fraction: float):
        """Place workers randomly on the grid with heterogeneous preferences."""
        all_cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        max_workers = min(self.n_workers, len(all_cells))
        chosen = self.random.sample(all_cells, max_workers)
        n_initial_remote = int(max_workers * initial_remote_fraction)

        for i, (x, y) in enumerate(chosen):
            # Slight bias toward remote preference — reflects real-world surveys
            preference = self.random.gauss(0.15, 0.45)
            preference = max(-1.0, min(1.0, preference))
            mode = "remote" if i < n_initial_remote else "office"

            agent = WorkerAgent(self, remote_preference=preference, work_mode=mode)
            agent.cell = self.grid[(x, y)]
            agent.pos = (x, y)
            self.agents.add(agent)

    def step(self):
        """Execute one model step: update shock state, step agents, collect data."""
        t = self.time
        self.shock_active = (
            self.shock_step > 0
            and self.shock_step <= t < self.shock_step + self.shock_duration
        )
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


# --- Model-level reporter functions ---


def _pct_remote(model: RatchetEffectModel) -> float:
    """Percentage of workers currently working remotely."""
    if not model.agents:
        return 0.0
    return (
        sum(1 for a in model.agents if a.work_mode == "remote")
        / len(model.agents)
        * 100
    )


def _avg_lock_in(model: RatchetEffectModel) -> float:
    """Average lock-in level across all workers (0 to 1)."""
    if not model.agents:
        return 0.0
    return sum(a.lock_in for a in model.agents) / len(model.agents)


def _return_resistance(model: RatchetEffectModel) -> float:
    """Average lock-in among currently remote workers only.

    Represents how difficult it would be to return this cohort to the office.
    A high value (close to 1.0) means the remote shift is effectively permanent.
    """
    remote_agents = [a for a in model.agents if a.work_mode == "remote"]
    if not remote_agents:
        return 0.0
    return sum(a.lock_in for a in remote_agents) / len(remote_agents)
