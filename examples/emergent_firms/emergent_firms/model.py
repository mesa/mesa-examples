from collections import defaultdict

import mesa
import numpy as np
import pandas as pd
from mesa.experimental.meta_agents import MetaAgents
from mesa.experimental.scenarios import Scenario

from .agents import Firm, Worker


class FirmScenario(Scenario):
    """Scenario parameters for the Endogenous Firm Formation model."""

    num_agents: int = 1000
    a: float = 1.0
    b: float = 1.0
    beta: float = 2.0
    num_friends: int = 2
    make_friends: bool = False
    max_friends: int = 10


# --- Model Reporters ---
def get_firms(model):
    living = getattr(model, "_living_firms", None)
    if living is not None:
        return list(living)
    return [a for a in model.agents if isinstance(a, Firm)]


def get_workers(model):
    workers = getattr(model, "_workers", None)
    if workers is not None:
        return workers
    return [a for a in model.agents if isinstance(a, Worker)]


def num_firms(model):
    if hasattr(model, "_stats"):
        return model._stats["num_firms"]
    return len(get_firms(model))


def new_firms(model):
    return model.new_firms_count


def avg_firm_size(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_firm_size"]
    firms = get_firms(model)
    return np.mean([f.size for f in firms]) if firms else 0.0


def max_firm_size(model):
    if hasattr(model, "_stats"):
        return model._stats["max_firm_size"]
    firms = get_firms(model)
    return max(f.size for f in firms) if firms else 0


def avg_effort(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_effort"]
    workers = get_workers(model)
    return np.mean([w.effort for w in workers]) if workers else 0.0


def avg_effort_largest(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_effort_largest"]
    firms = get_firms(model)
    if not firms:
        return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.effort for w in largest.workers]) if largest.size > 0 else 0.0


def total_effort(model):
    if hasattr(model, "_stats"):
        return model._stats["total_effort"]
    return sum(w.effort for w in get_workers(model))


def total_effort_largest(model):
    if hasattr(model, "_stats"):
        return model._stats["total_effort_largest"]
    firms = get_firms(model)
    if not firms:
        return 0.0
    largest = max(firms, key=lambda f: f.size)
    return sum(w.effort for w in largest.workers) if largest.size > 0 else 0.0


def total_output(model):
    if hasattr(model, "_stats"):
        return model._stats["total_output"]
    return sum(f.output for f in get_firms(model))


def max_firm_output(model):
    if hasattr(model, "_stats"):
        return model._stats["max_firm_output"]
    firms = get_firms(model)
    return max(firms, key=lambda f: f.size).output if firms else 0.0


def avg_income(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_income"]
    workers = get_workers(model)
    return np.mean([w.income for w in workers]) if workers else 0.0


def avg_income_largest(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_income_largest"]
    firms = get_firms(model)
    if not firms:
        return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.income for w in largest.workers]) if largest.size > 0 else 0.0


def avg_utility(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_utility"]
    workers = get_workers(model)
    return np.mean([w.utility for w in workers]) if workers else 0.0


def avg_utility_largest(model):
    if hasattr(model, "_stats"):
        return model._stats["avg_utility_largest"]
    firms = get_firms(model)
    if not firms:
        return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.utility for w in largest.workers]) if largest.size > 0 else 0.0


class FirmModel(mesa.Model):
    def __init__(self, scenario: FirmScenario = FirmScenario):
        raw_rng = (
            getattr(scenario, "rng", 42)
            if not isinstance(scenario, type)
            else 42
        )
        super().__init__(scenario=scenario)
        self.num_agents = max(2, int(self.scenario.num_agents))
        self.a = max(0.0, float(self.scenario.a))
        self.b = max(0.0, float(self.scenario.b))
        self.beta = max(1.0, float(self.scenario.beta))
        self.num_friends = max(
            0, min(int(self.scenario.num_friends), self.num_agents - 1)
        )
        self.make_friends = bool(self.scenario.make_friends)
        self.max_friends = max(
            self.num_friends, min(int(self.scenario.max_friends), self.num_agents - 1)
        )
        self.initial_seed = raw_rng if isinstance(raw_rng, int) else 42

        if not hasattr(self, "steps"):
            self.steps = 0
        self._period = 0
        self.new_firms_count = 0
        self._living_firms: dict[Firm, None] = {}
        self.firms_by_id: dict[int, Firm] = {}
        self._stats: dict[str, float | int] = {}
        # Per-firm history: firm_id -> {size: [], output: [], free_riders: [], avg_effort: [], step: []}
        self.firm_history = defaultdict(
            lambda: {
                "size": [],
                "output": [],
                "free_riders": [],
                "avg_effort": [],
                "step": [],
            }
        )
        self.firm_peaks: dict[int, list] = {}
        self.rank_snapshots = {"size": [], "output": []}
        self._dissolved_step_buf: list[int] = []
        self.dissolved_by_step: list[list[int]] = []

        # Initialize the MetaAgents membership manager
        MetaAgents(self)

        # 1. Initialize homogeneous initial state: agents starting lone singleton firms
        workers = []
        for _ in range(self.num_agents):
            theta = self.random.random()
            w = Worker(self, theta)
            # Create a singleton firm for this worker via the membership manager
            self.meta_agents.create("Firm", [w], mesa_agent_type=Firm)
            f = w.firm
            self._living_firms[f] = None
            self.firms_by_id[f.unique_id] = f
            f._size = 1
            f._total_effort = 0.0
            f.peak_size = 1
            workers.append(w)

        self._workers: list[Worker] = workers
        self.workers_by_id: dict[int, Worker] = {w.unique_id: w for w in workers}

        # 2. Create social network
        n_workers = len(workers)
        k_friends = self.num_friends
        if k_friends > 0 and n_workers > 1:
            pool = range(n_workers - 1)
            for i, w in enumerate(workers):
                w.friends = [
                    workers[j + 1 if j >= i else j]
                    for j in self.random.sample(pool, k_friends)
                ]
                w._friends_set = set(w.friends)

        # 3. Initial evaluation of states
        for w in workers:
            e, _, _ = w.evaluate_firm(w.firm)
            w.effort = e
            if w.firm is not None:
                w.firm._total_effort = e

        for f in get_firms(self):
            f.compute_output()
            f.allocate_income()

        # 4. Bind hooks for Section 3 Analytics Data Collection
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Number of Firms": num_firms,
                "New Firms": new_firms,
                "Average Firm Size": avg_firm_size,
                "Largest Firm Size": max_firm_size,
                "Average Effort Overall": avg_effort,
                "Average Effort Largest Firm": avg_effort_largest,
                "Total Effort": total_effort,
                "Total Effort Largest Firm": total_effort_largest,
                "Total Output": total_output,
                "Output Largest Firm": max_firm_output,
                "Average Income Overall": avg_income,
                "Average Income Largest Firm": avg_income_largest,
                "Average Utility Overall": avg_utility,
                "Average Utility Largest Firm": avg_utility_largest,
            },
        )
        self._collect_step_data()

    def step(self):
        self.new_firms_count = 0
        self._dissolved_step_buf = []
        workers = get_workers(self)

        # Asynchronous Poisson activation: draw K ~ Poisson(N) sequential activations per period
        num_activations = int(self.rng.poisson(self.num_agents))
        active_workers = self.random.choices(workers, k=num_activations)
        for w in active_workers:
            w.step()

        # Step trailing update computations across Meta-Agents
        for f in get_firms(self):
            f.age += 1
            f.compute_output()
            f.allocate_income()

        self._period += 1
        self.dissolved_by_step.append(self._dissolved_step_buf)
        self._collect_step_data()

    def _collect_step_data(self):
        """Single-pass aggregation of model metrics, worker histories, firm histories, and top-100 ranks."""
        firms = get_firms(self)
        workers = get_workers(self)

        n_firms = len(firms)
        n_workers = len(workers)

        tot_size = 0
        tot_output = 0.0
        largest: Firm | None = None
        max_size = 0

        for f in firms:
            s = f.size
            tot_size += s
            tot_output += f.output
            if largest is None or s > max_size:
                largest = f
                max_size = s

        tot_effort = 0.0
        tot_income = 0.0
        tot_utility = 0.0
        for w in workers:
            e = w.effort
            inc = w.income
            tot_effort += e
            tot_income += inc
            tot_utility += w.utility
            w.effort_history.append(round(e, 4))
            w.income_history.append(round(inc, 4))

        if largest is not None and max_size > 0:
            l_tot_e = largest.total_effort
            l_avg_e = l_tot_e / max_size
            l_avg_inc = largest.output / max_size
            l_workers = largest.workers
            l_avg_u = sum(w.utility for w in l_workers) / max_size
            l_out = largest.output
        else:
            l_tot_e = 0.0
            l_avg_e = 0.0
            l_avg_inc = 0.0
            l_avg_u = 0.0
            l_out = 0.0

        self._stats = {
            "num_firms": n_firms,
            "avg_firm_size": (tot_size / n_firms) if n_firms else 0.0,
            "max_firm_size": max_size,
            "avg_effort": (tot_effort / n_workers) if n_workers else 0.0,
            "avg_effort_largest": l_avg_e,
            "total_effort": tot_effort,
            "total_effort_largest": l_tot_e,
            "total_output": tot_output,
            "max_firm_output": l_out,
            "avg_income": (tot_income / n_workers) if n_workers else 0.0,
            "avg_income_largest": l_avg_inc,
            "avg_utility": (tot_utility / n_workers) if n_workers else 0.0,
            "avg_utility_largest": l_avg_u,
        }

        self.datacollector.collect(self)
        self._record_firm_history(firms)

    def _record_firm_history(self, firms=None):
        """Snapshot each living firm's size, output, free-rider count, avg effort, and top-100 ranks."""
        if firms is None:
            firms = get_firms(self)

        step_num = getattr(self, "_period", self.steps)
        firm_history = self.firm_history
        firm_peaks = self.firm_peaks

        for f in firms:
            fid = f.unique_id
            size = f.size
            out_r = round(f.output, 4)
            # Support both live Firm (precomputed in allocate_income) and minimal test mocks
            if f._total_effort is not None:
                avg_e = (f._total_effort / size) if size > 0 else 0.0
                free_riders = getattr(f, "free_riders", 0)
            else:
                w_list = list(f.workers)
                effs = [w.effort for w in w_list]
                avg_e = (sum(effs) / len(effs)) if effs else 0.0
                free_riders = sum(1 for e in effs if e < 0.01)

            h = firm_history[fid]
            h["size"].append(size)
            h["output"].append(out_r)
            h["free_riders"].append(free_riders)
            h["avg_effort"].append(round(avg_e, 4))
            h["step"].append(step_num)

            pk = firm_peaks.get(fid)
            if pk is None:
                firm_peaks[fid] = [size, out_r, 1]
            else:
                if size > pk[0]:
                    pk[0] = size
                if out_r > pk[1]:
                    pk[1] = out_r
                pk[2] += 1

        if step_num >= 1:
            max_k = 100
            by_size = sorted(
                firms,
                key=lambda f: (f.size, f.output, -f.unique_id),
                reverse=True,
            )[:max_k]
            by_output = sorted(
                firms,
                key=lambda f: (f.output, f.size, -f.unique_id),
                reverse=True,
            )[:max_k]
            self.rank_snapshots["size"].append(
                [(f.unique_id, f.size, round(f.output, 4), f.age) for f in by_size]
            )
            self.rank_snapshots["output"].append(
                [(f.unique_id, f.size, round(f.output, 4), f.age) for f in by_output]
            )

    def get_network_df(self):
        """Retrieve fixed Agent-to-Agent Social Network Edges"""
        edges = []
        for w in get_workers(self):
            for friend in w.friends:
                edges.append({"Source": w.unique_id, "Target": friend.unique_id})
        return pd.DataFrame(edges)
