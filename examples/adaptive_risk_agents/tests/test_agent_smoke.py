from examples.adaptive_risk_agents.model import AdaptiveRiskModel


def test_agent_methods_execute():
    model = AdaptiveRiskModel(n_agents=1, seed=1)
    agent = next(iter(model.agents))

    action = agent.choose_action()
    assert action in {"safe", "risky"}

    agent.step()  # should not crash
