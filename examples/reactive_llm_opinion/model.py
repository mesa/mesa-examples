import mesa
import random

# -----------------------------
# Agent with Reactive LLM Logic

class ReactiveAgent(mesa.Agent):
    def __init__(self, model, threshold=0.2):
        super().__init__(model)
        self.opinion = random.uniform(0, 1)
        self.last_opinion = self.opinion
        self.threshold = threshold

    def mock_llm_call(self, new_info):
        """Simulate LLM reasoning"""
        return (self.opinion + new_info) / 2

    def process_opinion(self, new_info):
        """Trigger-based reasoning"""
        delta = abs(new_info - self.last_opinion)

        if delta > self.threshold:
            # Count LLM usage
            self.model.llm_calls += 1

            # Simulate LLM call
            updated = self.mock_llm_call(new_info)

            # Update state
            self.last_opinion = updated
            self.opinion = updated

            print(f"Agent {self.unique_id} USED LLM → New opinion: {self.opinion:.2f}")
        else:
            print(f"Agent {self.unique_id} skipped LLM (delta={delta:.2f})")


# -----------------------------
# Model

class ReactiveLLMModel(mesa.Model):
    def __init__(self, num_agents=10):
        super().__init__()

        self.num_agents = num_agents
        self.llm_calls = 0
        self.total_steps = 0

        # Create agents
        for _ in range(self.num_agents):
            ReactiveAgent(self)

    def step(self):
        """Simulate environment change"""
        self.total_steps += 1

        # Simulate new environmental signal
        new_info = random.uniform(0, 1)

        print(f"\n--- Step {self.total_steps} | New Info: {new_info:.2f} ---")

        # Agents react
        self.agents.do("process_opinion", new_info)


# -----------------------------
# Run Simulation

if __name__ == "__main__":
    model = ReactiveLLMModel(num_agents=10)

    STEPS = 20

    print("Starting Reactive LLM Simulation...\n")

    for _ in range(STEPS):
        model.step()

    # -----------------------------
    # FINAL METRICS 
    total_possible_calls = STEPS * model.num_agents

    print("\n========== RESULTS ==========")
    print(f"Total Agents: {model.num_agents}")
    print(f"Total Steps: {STEPS}")
    print(f"Max Possible LLM Calls: {total_possible_calls}")
    print(f"Actual LLM Calls: {model.llm_calls}")

    reduction = 100 * (1 - model.llm_calls / total_possible_calls)

    print(f"Reduction in LLM usage: {reduction:.2f}%")

    # Optional: token estimation
    tokens_per_call = 500
    total_tokens = model.llm_calls * tokens_per_call

    print(f"Estimated Token Usage: {total_tokens}")
    print("============================")
