import mesa

# We use mesa.Agent for now to ensure it runs on your current version
class OpinionAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)

    def process_opinion(self, msg):
        # This is your reactive trigger
        print(f"Agent {self.unique_id} reacting to info: {msg}")

class ReactiveLLMModel(mesa.Model):
    def __init__(self):
        super().__init__()
        # Creating 5 agents
        for _ in range(5):
            OpinionAgent(self)

    def step(self):
        # 1. Trigger the reactive LLM reasoning every 5 steps
        if self.steps % 5 == 0:
            msg = "New architectural standard in Mesa 4.0!"
            self.agents.do("process_opinion", msg)
        
        # 2. Tell all agents to move or update (if you have a step method in OpinionAgent)
        # Since your OpinionAgent doesn't have a 'step' method yet, 
        # you can just let the model handle the 'do' logic above.
        # If you add a 'step' method to OpinionAgent later, use:
        # self.agents.do("step")

# This block allows you to run it directly in your terminal
if __name__ == "__main__":
    model = ReactiveLLMModel()
    print("Starting Model Simulation...")
    for i in range(11):
        print(f"--- Step {i} ---")
        model.step()