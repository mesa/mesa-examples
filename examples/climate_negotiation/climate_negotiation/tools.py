"""Custom negotiation tools for the Climate Negotiation example.

These four tools are registered into `country_tool_manager` (from agents.py)
via the @tool(tool_manager=...) decorator.  They are NOT added to the global
tool registry, so only CountryAgents can call them.

The inbuilt `speak_to` tool (global registry) is also available to every
CountryAgent because ToolManager copies global tools at construction time.
"""

from typing import TYPE_CHECKING

from .agents import country_tool_manager
from mesa_llm.tools.tool_decorator import tool

if TYPE_CHECKING:
    from mesa_llm.llm_agent import LLMAgent


@tool(tool_manager=country_tool_manager)
def make_proposal(
    agent: "LLMAgent",
    target_reduction_percent: float,
    target_year: int,
    justification: str,
) -> str:
    """Formally propose an emissions reduction target to all negotiating parties.

    Args:
        target_reduction_percent: Proposed percentage emissions reduction (0-100).
        target_year: The year by which the reduction should be achieved (e.g. 2035).
        justification: The diplomatic argument or reasoning behind this proposal.
        agent: Provided automatically.

    Returns:
        Confirmation string describing the proposal that was broadcast.
    """
    target_reduction_percent = float(target_reduction_percent or 25.0)
    target_year = int(target_year or 2035)
    agent.current_pledge = target_reduction_percent
    agent.proposals_made += 1

    broadcast = (
        f"[FORMAL PROPOSAL] {agent.country_name} proposes a "
        f"{target_reduction_percent:.1f}% emissions reduction by {target_year}. "
        f"Justification: {justification}"
    )
    all_others = [a for a in agent.model.agents if a is not agent]
    agent.send_message(broadcast, all_others)
    agent.model.total_proposals += 1

    return (
        f"Proposal broadcast to {len(all_others)} parties: "
        f"{target_reduction_percent:.1f}% reduction by {target_year}."
    )


@tool(tool_manager=country_tool_manager)
def accept_proposal(
    agent: "LLMAgent",
    proposer_id: int,
    agreed_reduction_percent: float,
    acceptance_message: str,
) -> str:
    """Formally accept another country's emissions reduction proposal.

    Args:
        proposer_id: Unique ID of the country whose proposal you are accepting.
        agreed_reduction_percent: The reduction percentage you commit to.
        acceptance_message: A diplomatic statement explaining your acceptance.
        agent: Provided automatically.

    Returns:
        Confirmation of the acceptance and updated pledge.
    """
    agreed_reduction_percent = float(agreed_reduction_percent or 25.0)
    proposer_id = int(proposer_id or 0)
    agent.accepted_treaty = True
    agent.current_pledge = max(float(agent.current_pledge), agreed_reduction_percent)
    agent.proposals_accepted += 1
    agent.model.total_acceptances += 1

    proposer = next(
        (a for a in agent.model.agents if a.unique_id == proposer_id), None
    )
    if proposer:
        agent.send_message(
            f"[ACCEPTANCE] {agent.country_name} formally accepts the proposal. "
            f"We commit to {agreed_reduction_percent:.1f}% reduction. "
            f"{acceptance_message}",
            [proposer],
        )

    return (
        f"{agent.country_name} accepted proposal from agent {proposer_id}. "
        f"Pledged {agreed_reduction_percent:.1f}%."
    )


@tool(tool_manager=country_tool_manager)
def form_coalition(
    agent: "LLMAgent",
    partner_ids: list[int],
    coalition_name: str,
) -> str:
    """Form or join a coalition with other countries to strengthen a shared position.

    Args:
        partner_ids: List of unique IDs of countries to invite into the coalition.
        coalition_name: Short descriptive label (e.g. 'High Ambition Coalition').
        agent: Provided automatically.

    Returns:
        Confirmation of coalition formation and the partners notified.
    """
    for pid in (partner_ids or []):
        if pid not in agent.coalition_members:
            agent.coalition_members.append(pid)

    partner_agents = [a for a in agent.model.agents if a.unique_id in (partner_ids or [])]

    # Mutually add the initiating agent to each partner's coalition list
    for partner in partner_agents:
        if (
            hasattr(partner, "coalition_members")
            and agent.unique_id not in partner.coalition_members
        ):
            partner.coalition_members.append(agent.unique_id)

    member_names = (
        [getattr(a, "country_name", str(a.unique_id)) for a in partner_agents]
        + [agent.country_name]
    )

    agent.send_message(
        f"[COALITION] {agent.country_name} proposes the '{coalition_name}'. "
        f"Current members: {member_names}",
        partner_agents,
    )

    return f"Coalition '{coalition_name}' formed. Members: {member_names}."


@tool(tool_manager=country_tool_manager)
def reject_and_counter(
    agent: "LLMAgent",
    proposer_id: int,
    counter_reduction_percent: float,
    reason: str,
) -> str:
    """Reject another country's proposal and broadcast a counter-proposal to all parties.

    Args:
        proposer_id: Unique ID of the country whose proposal you are rejecting.
        counter_reduction_percent: Your alternative reduction percentage.
        reason: Explanation of why you reject the original and what you offer instead.
        agent: Provided automatically.

    Returns:
        Confirmation of the rejection and counter-proposal broadcast.
    """
    counter_reduction_percent = float(counter_reduction_percent or 20.0)
    proposer_id = int(proposer_id or 0)
    proposer = next(
        (a for a in agent.model.agents if a.unique_id == proposer_id), None
    )
    proposer_name = (
        getattr(proposer, "country_name", str(proposer_id)) if proposer else str(proposer_id)
    )

    counter_msg = (
        f"[COUNTER-PROPOSAL] {agent.country_name} cannot accept {proposer_name}'s proposal. "
        f"Counter-offer: {counter_reduction_percent:.1f}% reduction. "
        f"Reason: {reason}"
    )
    all_others = [a for a in agent.model.agents if a is not agent]
    agent.send_message(counter_msg, all_others)

    agent.current_pledge = counter_reduction_percent
    agent.proposals_made += 1
    agent.model.total_proposals += 1

    return (
        f"{agent.country_name} rejected {proposer_name}'s proposal. "
        f"Counter-proposal ({counter_reduction_percent:.1f}%) broadcast to all."
    )
