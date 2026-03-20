import matplotlib.pyplot as plt

from misinformation_spread.model import MisinformationModel


def main():
    print("Starting Misinformation Spread Simulation...")
    model = MisinformationModel()

    num_steps = 5
    for i in range(num_steps):
        print(f"\n--- Step {i + 1} ---")
        model.step()

        for agent in model.agents:
            print(f"  {agent.name:8s} | stance: {agent.stance:8s} | belief: {agent.belief_score:.2f}")

        believers = sum(1 for a in model.agents if a.stance == "believer")
        skeptics = sum(1 for a in model.agents if a.stance == "skeptic")
        neutrals = sum(1 for a in model.agents if a.stance == "neutral")
        print(f"\n  Summary: {believers} believers, {skeptics} skeptics, {neutrals} neutrals")

    # Plot model-level results
    model_data = model.datacollector.get_model_vars_dataframe()

    plt.figure(figsize=(10, 6))
    plt.plot(model_data["believers"], color="red", label="Believers", marker="o")
    plt.plot(model_data["skeptics"], color="blue", label="Skeptics", marker="s")
    plt.plot(model_data["neutrals"], color="gray", label="Neutrals", marker="^")
    plt.xlabel("Step")
    plt.ylabel("Number of Agents")
    plt.title("Misinformation Spread Over Time")
    plt.legend()
    plt.grid(True)
    plt.savefig("results.png")
    print("\nPlot saved to results.png")
    plt.show()

    # Print final agent belief scores
    agent_data = model.datacollector.get_agent_vars_dataframe()
    print("\n--- Final Belief Scores ---")
    last_step = agent_data.xs(num_steps - 1, level="Step")
    for agent_id, row in last_step.iterrows():
        print(f"  Agent {agent_id:3d} | stance: {row['stance']:8s} | belief: {row['belief_score']:.2f}")


if __name__ == "__main__":
    main()
