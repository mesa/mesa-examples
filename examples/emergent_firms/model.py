import mesa
import pandas as pd
import numpy as np
from collections import defaultdict
from mesa.meta_agents import MetaAgents
from mesa.experimental.scenarios import Scenario
from agents import Worker, Firm


class FirmScenario(Scenario):
    """Scenario parameters for the Endogenous Firm Formation model."""

    num_agents: int = 1000
    a: float = 1.0
    b: float = 1.0
    beta: float = 2.0
    num_friends: int = 2
    make_friends: bool = False

# --- Model Reporters ---
def get_firms(model): return [a for a in model.agents if isinstance(a, Firm)]
def get_workers(model): return [a for a in model.agents if isinstance(a, Worker)]

def num_firms(model): return len(get_firms(model))
def new_firms(model): return model.new_firms_count
def avg_firm_size(model):
    firms = get_firms(model)
    return np.mean([f.size for f in firms]) if firms else 0.0
def max_firm_size(model):
    firms = get_firms(model)
    return max([f.size for f in firms]) if firms else 0
def avg_effort(model):
    workers = get_workers(model)
    return np.mean([w.effort for w in workers]) if workers else 0.0
def avg_effort_largest(model):
    firms = get_firms(model)
    if not firms: return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.effort for w in largest.workers]) if largest.size > 0 else 0.0
def total_effort(model):
    return sum(w.effort for w in get_workers(model))
def total_effort_largest(model):
    firms = get_firms(model)
    if not firms: return 0.0
    largest = max(firms, key=lambda f: f.size)
    return sum(w.effort for w in largest.workers) if largest.size > 0 else 0.0
def total_output(model): return sum([f.output for f in get_firms(model)])
def max_firm_output(model):
    firms = get_firms(model)
    return max(firms, key=lambda f: f.size).output if firms else 0.0
def avg_income(model):
    workers = get_workers(model)
    return np.mean([w.income for w in workers]) if workers else 0.0
def avg_income_largest(model):
    firms = get_firms(model)
    if not firms: return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.income for w in largest.workers]) if largest.size > 0 else 0.0
def avg_utility(model):
    workers = get_workers(model)
    return np.mean([w.utility for w in workers]) if workers else 0.0
def avg_utility_largest(model):
    firms = get_firms(model)
    if not firms: return 0.0
    largest = max(firms, key=lambda f: f.size)
    return np.mean([w.utility for w in largest.workers]) if largest.size > 0 else 0.0


class FirmModel(mesa.Model):
    def __init__(self, scenario: FirmScenario = FirmScenario):
        super().__init__(scenario=scenario)
        self.num_agents = self.scenario.num_agents
        self.a = self.scenario.a
        self.b = self.scenario.b
        self.beta = self.scenario.beta
        self.num_friends = self.scenario.num_friends
        self.make_friends = self.scenario.make_friends

        self.steps = 0
        self.new_firms_count = 0
        # Per-firm history: firm_id -> {output: [], free_riders: [], avg_effort: [], step: []}
        self.firm_history = defaultdict(lambda: {"output": [], "free_riders": [], "avg_effort": [], "step": []})

        # Initialize the MetaAgents membership manager
        MetaAgents(self)

        # 1. Initialize homogenous initial state: agents starting lone singleton firms
        workers = []
        for _ in range(self.num_agents):
            theta = self.random.random()
            w = Worker(self, theta)
            # Create a singleton firm for this worker via the membership manager
            self.meta_agents.create("Firm", [w], mesa_agent_type=Firm)
            workers.append(w)

        # 2. Wire static social network (random reference representing bounds of information topology)
        for w in workers:
            candidates = [other for other in workers if other != w]
            w.friends = self.random.sample(candidates, self.num_friends)

        # 3. Initial evaluation of states
        for f in get_firms(self):
            f.compute_output()
            f.allocate_income()

        for w in workers:
            e, u, _ = w.evaluate_firm(w.firm)
            w.effort = e

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
            agenttype_reporters={
                Worker: {
                    "Effort": "effort",
                    "Income": "income",
                },
            },
        )
        self.datacollector.collect(self)
        self._record_firm_history()

    def step(self):
        self.new_firms_count = 0
        workers = get_workers(self)

        # Asynchronous random activation
        # A Period mapping Ch. 3 = 'N sequential random agent activations'
        active_workers = self.random.choices(workers, k=self.num_agents)
        for w in active_workers:
            w.step()

        # Step trailing update computations across Meta-Agents
        for f in get_firms(self):
            f.age += 1
            f.compute_output()
            f.allocate_income()

        self.steps += 1
        self.datacollector.collect(self)
        self._record_firm_history()

    def _record_firm_history(self):
        """Snapshot each living firm's output, free-rider count, and avg effort."""
        for f in get_firms(self):
            workers = list(f.workers)
            efforts = [w.effort for w in workers]
            avg_e = float(np.mean(efforts)) if efforts else 0.0
            free_riders = sum(1 for e in efforts if e < 0.01)
            h = self.firm_history[f.unique_id]
            h["output"].append(round(f.output, 4))
            h["free_riders"].append(free_riders)
            h["avg_effort"].append(round(avg_e, 4))
            h["step"].append(self.steps)

    def get_network_df(self):
        """Retrieve fixed Agent-to-Agent Social Network Edges"""
        edges = []
        for w in get_workers(self):
            for friend in w.friends:
                edges.append({"Source": w.unique_id, "Target": friend.unique_id})
        return pd.DataFrame(edges)