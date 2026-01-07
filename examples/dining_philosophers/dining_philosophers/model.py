import mesa
import networkx as nx

from .agent import ForkAgent, PhilosopherAgent, State


class DiningPhilosophersModel(mesa.Model):
    def __init__(
        self,
        num_philosophers=5,
        strategy="Naive",
        hungry_chance=0.1,
        full_chance=0.2,
    ):
        super().__init__()

        self.strategy = strategy
        self.hungry_chance = hungry_chance
        self.full_chance = full_chance
        self.num_nodes = num_philosophers * 2

        self.G = nx.circulant_graph(self.num_nodes, [1])
        self.grid = mesa.space.NetworkGrid(self.G)

        philosophers_list = []

        for node_id in range(self.num_nodes):
            if node_id % 2 == 0:
                p = PhilosopherAgent(self, node_id)
                self.grid.place_agent(p, node_id)
                philosophers_list.append(p)
            else:
                f = ForkAgent(self, node_id)
                self.grid.place_agent(f, node_id)

        self.philosophers = mesa.agent.AgentSet(philosophers_list, random=self.random)

        model_reporters = {
            "Eating": lambda m: len(
                [p for p in m.philosophers if p.state == State.EATING]
            ),
            "Hungry": lambda m: len(
                [p for p in m.philosophers if p.state == State.HUNGRY]
            ),
            "Thinking": lambda m: len(
                [p for p in m.philosophers if p.state == State.THINKING]
            ),
            "Avg Wait Time": lambda m: (
                (
                    sum(p.total_wait_time for p in m.philosophers)
                    / sum(p.eating_count for p in m.philosophers)
                )
                if sum(p.eating_count for p in m.philosophers) > 0
                else 0
            ),
            "Throughput": lambda m: (
                (sum(p.total_eaten for p in m.philosophers) / m.steps)
                if m.steps > 0
                else 0
            ),
        }

        # Add reporters for individual philosopher's consumption
        # Max 10 philosophers as per slider
        for i in range(10):
            # i-th philosopher has node_id = i * 2
            p_id = i * 2

            # Use default argument in lambda to capture the current value of p_id
            model_reporters[f"P{i}"] = lambda m, pid=p_id: (
                next((p.total_eaten for p in m.philosophers if p.position == pid), 0)
            )

        self.datacollector = mesa.DataCollector(model_reporters=model_reporters)

    def step(self):
        self.philosophers.shuffle_do("step")
        self.datacollector.collect(self)
