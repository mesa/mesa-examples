from mesa_llm.tools.tool_decorator import tool


@tool
def check_neighbors(agent):
    """Check who is nearby and what they believe about the rumor.

    Returns a formatted list of neighboring agents with their current stance
    on the rumor (believer, skeptic, or neutral).
    """
    neighbors = []
    for cell in agent.cell.neighborhood:
        for neighbor in cell.agents:
            if neighbor is not agent:
                neighbors.append(neighbor)

    if not neighbors:
        return "No neighbors nearby."

    lines = []
    for n in neighbors:
        lines.append(f"- Agent {n.unique_id} ({n.name}): {n.stance}")
    return "Nearby agents:\n" + "\n".join(lines)


@tool
def spread_rumor(agent, target_id: int):
    """Spread the rumor to a specific agent to try to convince them.

    Args:
        target_id: The unique_id of the agent to spread the rumor to.
    """
    target = None
    for a in agent.model.agents:
        if a.unique_id == target_id:
            target = a
            break

    if target is None:
        return f"Could not find agent with id {target_id}."

    message = f"Have you heard? {agent.model.rumor}"
    agent.send_message(message, [target])
    return f"Spread the rumor to Agent {target_id} ({target.name})."


@tool
def challenge_rumor(agent, target_id: int):
    """Challenge the rumor by sending a counter-argument to a specific agent.

    Args:
        target_id: The unique_id of the agent to send the counter-argument to.
    """
    target = None
    for a in agent.model.agents:
        if a.unique_id == target_id:
            target = a
            break

    if target is None:
        return f"Could not find agent with id {target_id}."

    message = f"I don't believe the rumor: {agent.model.rumor}. I think it's false."
    agent.send_message(message, [target])
    return f"Challenged the rumor with Agent {target_id} ({target.name})."


@tool
def update_belief(agent, new_score: float):
    """Update personal belief score and stance based on new information.

    Args:
        new_score: The new belief score between 0.0 (disbelief) and 1.0 (full belief).
    """
    try:
        new_score = float(new_score)
    except (ValueError, TypeError):
        return f"Error: new_score must be a number, got {new_score}"

    clamped = max(0.0, min(1.0, new_score))
    agent.belief_score = clamped

    if clamped > 0.7:
        agent.stance = "believer"
    elif clamped < 0.3:
        agent.stance = "skeptic"
    else:
        agent.stance = "neutral"

    return f"Updated belief score to {clamped:.2f}. Stance is now: {agent.stance}."
