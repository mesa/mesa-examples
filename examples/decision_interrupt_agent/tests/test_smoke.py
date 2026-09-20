from examples.decision_interrupt_agent.model import DecisionModel


def test_decision_interrupt_model_runs():
    """
    Smoke test: model should run without errors
    while handling agent interruptions.
    """
    model = DecisionModel(n_agents=3)

    for _ in range(15):
        model.step()
