"""Tests for the meta-agent command structure.

These are the claims the example exists to demonstrate: memberships overlap,
relation labels partition them, the hierarchy is queryable by depth, and
teardown leaves no dangling edges.
"""

from __future__ import annotations

import pytest
from sar import ATTACHED, MEMBER, ON_CALL, Crew, SARScenario, SearchAndRescueModel
from sar.command import TaskForce


@pytest.fixture
def model():
    """A freshly built model with a deterministic seed."""
    return SearchAndRescueModel(scenario=SARScenario(rng=7))


def test_every_responder_belongs_to_exactly_one_crew(model):
    """Crew formation partitions the responders."""
    crewed = [
        responder
        for crew in model.crews
        for responder in model.meta_agents.members_of(crew, relation=MEMBER)
    ]
    assert sorted(a.unique_id for a in crewed) == sorted(
        a.unique_id for a in model.responders
    )


def test_medics_belong_to_a_crew_and_the_pool_simultaneously(model):
    """The overlapping membership the model is built around."""
    medics = [r for r in model.responders if r.is_medic]
    assert medics, "expected at least one medic"

    pool_members = {
        a.unique_id
        for a in model.meta_agents.members_of(model.medical_pool, relation=ON_CALL)
    }
    for medic in medics:
        groups = model.meta_agents.groups_of(medic)
        assert any(isinstance(g, Crew) for g in groups), "medic has no home crew"
        assert medic.unique_id in pool_members, "medic is not on call"
        # Two groups at once, under two different relation labels.
        assert len(groups) >= 2


def test_relation_labels_partition_a_medics_memberships(model):
    """Filtering by relation returns disjoint views of the same agent."""
    medic = next(r for r in model.responders if r.is_medic)
    membership = model.meta_agents

    as_member = {g.unique_id for g in membership.groups_of(medic, relation=MEMBER)}
    as_on_call = {g.unique_id for g in membership.groups_of(medic, relation=ON_CALL)}

    assert as_member and as_on_call
    assert as_member.isdisjoint(as_on_call)
    assert as_member | as_on_call == {g.unique_id for g in membership.groups_of(medic)}


def test_borrowed_medic_holds_three_memberships_then_returns(model):
    """A seconded medic gains a third edge and loses it on release."""
    membership = model.meta_agents
    medic = next(r for r in model.responders if r.is_medic)
    home = next(g for g in membership.groups_of(medic, relation=MEMBER))
    borrower = next(c for c in model.crews if c is not home)

    before = len(membership.query_memberships(medic))
    membership.add_member(borrower, medic, relation=ATTACHED)

    assert len(membership.query_memberships(medic)) == before + 1
    assert medic in borrower.responders(), "borrowing crew should command the medic"
    assert medic not in home.responders(), "home crew must not also command it"
    # The permanent edge survives the secondment.
    assert home in membership.groups_of(medic, relation=MEMBER)

    model.release_medic(borrower)
    assert len(membership.query_memberships(medic)) == before
    assert medic in home.responders()


def test_at_level_walks_the_command_hierarchy(model):
    """at_level reports structural depth below incident command."""
    membership = model.meta_agents
    command = model.incident_command

    assert list(membership.at_level(0, root=command)) == [command]

    level_one = {a.unique_id for a in membership.at_level(1, root=command)}
    assert level_one == {c.unique_id for c in model.crews}
    assert model.span_of_control == len(level_one)

    # Responders sit one level below their crews.
    level_two = {a.unique_id for a in membership.at_level(2, root=command)}
    assert level_two == {r.unique_id for r in model.responders}


def test_task_force_deepens_the_hierarchy(model):
    """Crews placed under a task force move a level further from command."""
    membership = model.meta_agents
    command = model.incident_command
    first, second = model.crews[0], model.crews[1]

    task_force = membership.create(
        "TaskForce_test", [first, second], mesa_agent_type=TaskForce
    )
    membership.remove_member(command, first, relation=MEMBER)
    membership.remove_member(command, second, relation=MEMBER)
    membership.add_member(command, task_force, relation=MEMBER)

    assert task_force in membership.at_level(1, root=command)
    assert first not in membership.at_level(1, root=command)
    assert first in membership.at_level(2, root=command)
    assert set(task_force.crews()) == {first, second}


def test_dissolving_a_task_force_leaves_no_dangling_edges(model):
    """dissolve removes the group and every edge incident to it."""
    membership = model.meta_agents
    first, second = model.crews[0], model.crews[1]
    task_force = membership.create(
        "TaskForce_test", [first, second], mesa_agent_type=TaskForce
    )
    task_force_id = task_force.unique_id

    membership.dissolve(task_force)
    membership.backend.assert_invariants()

    remaining = membership.backend.as_triplets()
    assert not any(task_force_id in (agent, group) for agent, group, _ in remaining), (
        "dissolved group still referenced by an edge"
    )
    # The member crews outlive the group they were in.
    assert first in model.crews
    assert second in model.crews


def test_removing_an_agent_cascades_to_its_memberships(model):
    """Agent removal is cleaned up by the manager's lifecycle hook."""
    membership = model.meta_agents
    responder = model.responders[0]
    responder_id = responder.unique_id
    assert membership.query_memberships(responder_id)

    responder.remove()

    membership.backend.assert_invariants()
    assert not membership.query_memberships(responder_id)
    assert not any(
        responder_id == agent for agent, _, _ in membership.backend.as_triplets()
    )


def test_backend_invariants_hold_through_a_full_run(model):
    """The membership indexes stay consistent while structure churns."""
    for _ in range(60):
        model.step()
        model.meta_agents.backend.assert_invariants()
    assert model.rescued > 0, "expected the response to rescue somebody"
