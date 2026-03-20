import matplotlib.pyplot as plt

from misinformation_spread.model import RuleBasedModel


def main():
    print("Starting Rule-Based Misinformation Simulation...")
    print("(No LLM required — runs instantly)\n")

    model = RuleBasedModel()
    num_steps = 10

    for i in range(num_steps):
        print(f"--- Step {i + 1} ---")
        model.step()

        for agent in model.agents:
            print(
                f"  {agent.name:8s} | stance: {agent.stance:8s} | belief: {agent.belief_score:.2f}"
            )

        believers = sum(1 for a in model.agents if a.stance == "believer")
        skeptics = sum(1 for a in model.agents if a.stance == "skeptic")
        neutrals = sum(1 for a in model.agents if a.stance == "neutral")
        print(f"  Summary: {believers} believers, {skeptics} skeptics, {neutrals} neutrals\n")

    # Plot results
    model_data = model.datacollector.get_model_vars_dataframe()

    plt.figure(figsize=(10, 6))
    plt.plot(model_data["believers"], color="red", label="Believers", marker="o")
    plt.plot(model_data["skeptics"], color="blue", label="Skeptics", marker="s")
    plt.plot(model_data["neutrals"], color="gray", label="Neutrals", marker="^")
    plt.xlabel("Step")
    plt.ylabel("Number of Agents")
    plt.title("Rule-Based Misinformation Spread Over Time")
    plt.legend()
    plt.grid(True)
    plt.savefig("results_rulebased.png")
    print("Plot saved to results_rulebased.png")
    plt.show()

    # Print final agent belief scores
    agent_data = model.datacollector.get_agent_vars_dataframe()
    print("\n--- Final Belief Scores ---")
    last_step = agent_data.xs(num_steps - 1, level="Step")
    for agent_id, row in last_step.iterrows():
        print(
            f"  Agent {agent_id:3d} | stance: {row['stance']:8s} | belief: {row['belief_score']:.2f}"
        )

    # Comparison note
    print("\n" + "=" * 60)
    print("COMPARISON: Rule-Based vs LLM-Based Model")
    print("=" * 60)
    print(
        "Rule-based model: Agents follow fixed mathematical rules.\n"
        "  - Believers increase neighbors' belief by 0.1*(1-score)\n"
        "  - Skeptics decrease neighbors' belief by 0.1*score\n"
        "  - Neutral neighbors add small random noise (+/-0.02)\n"
        "  - Deterministic (aside from grid placement and neutral noise)\n"
        "  - Runs instantly, good for parameter sweeps\n"
        "\n"
        "LLM-based model: Agents use an LLM to reason about actions.\n"
        "  - Each agent has a unique persona influencing decisions\n"
        "  - Agents choose whether to spread or challenge the rumor\n"
        "  - Emergent behavior from natural language reasoning\n"
        "  - Non-deterministic, slower, but captures richer dynamics\n"
        "\n"
        "Run 'python run.py' to compare with the LLM version."
    )


if __name__ == "__main__":
    main()
