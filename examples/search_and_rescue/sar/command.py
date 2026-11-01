"""Command structure for the search and rescue model.

These classes supply *behaviour* for meta-agents. They are passed to
``model.meta_agents.create(..., mesa_agent_type=Crew)``, which builds a
dynamic class deriving from both ``MetaAgent`` and the class given here. They
must therefore not define ``__init__`` — ``MetaAgent`` owns construction.

The hierarchy is::

    IncidentCommand
      ├── TaskForce ── Crew ── Responder
      └── Crew ── Responder            (a crew that has not joined a task force)

so ``at_level(1, root=incident_command)`` is exactly the set of units the
commander is directly tracking, i.e. their span of control.
"""

from __future__ import annotations

import numpy as np
from mesa.agent import Agent

from .agents import Responder

MEMBER = "member"
ATTACHED = "attached"
ON_CALL = "on_call"


class IncidentCommand(Agent):
    """Root of the command hierarchy. Structural only."""


class MedicalPool(Agent):
    """The roster of every medic, regardless of crew. Structural only."""


class TaskForce(Agent):
    """Two or more crews working a shared cluster of victims."""

    def crews(self) -> list:
        """Return the crews under this task force."""
        return list(self.model.meta_agents.members_of(self, relation=MEMBER))


class Crew(Agent):
    """A small team of responders working one victim at a time."""

    def responders(self) -> list[Responder]:
        """Return the responders this crew actually commands right now.

        A medic has three concurrent memberships — ``member`` of its home
        crew, ``on_call`` to the pool, and while seconded, ``attached`` to a
        borrowing crew. Only one crew may command it at a time, so a permanent
        member that is currently attached elsewhere is excluded here.
        """
        membership = self.model.meta_agents
        people = list(membership.members_of(self, relation=ATTACHED))
        people.extend(
            agent
            for agent in membership.members_of(self, relation=MEMBER)
            if len(membership.query_memberships(agent, relation=ATTACHED)) == 0
        )
        return [agent for agent in people if isinstance(agent, Responder)]

    def has_medic(self) -> bool:
        """Whether this crew currently has a medic available to it."""
        return any(responder.is_medic for responder in self.responders())

    def centroid(self) -> np.ndarray | None:
        """Mean position of the crew, or None if it has no members."""
        squad = self.responders()
        if not squad:
            return None
        return np.mean([responder.position for responder in squad], axis=0)

    def advance(self) -> None:
        """Claim a victim, call for a medic if needed, close on the target.

        Deliberately not named ``step``: meta-agent classes are built as
        ``type(name, (MetaAgent, *mesa_agent_type))``, so ``MetaAgent.step``
        precedes this class in the MRO and would silently shadow a ``step``
        defined here.
        """
        model = self.model
        squad = self.responders()
        if not squad:
            return

        target = self.target
        if target is not None and (
            target.assigned_crew is not self or target.is_expired
        ):
            model.release_medic(self)
            self.target = target = None

        if target is None:
            self.target = target = model.claim_victim(self)

        if target is None:
            for responder in squad:
                responder.wander()
            return

        if target.needs_medic and not self.has_medic():
            model.request_medic(self)
            squad = self.responders()

        for responder in squad:
            responder.move_towards(target.position)

        model.attempt_rescue(self, target, squad)


def pair_score(crews: tuple) -> float | None:
    """Score a candidate task force by how close its crews' targets are.

    Returned to ``MetaAgents.find_combinations`` as the evaluation function.
    ``None`` rejects the candidate outright.
    """
    targets = [crew.target for crew in crews]
    if any(target is None for target in targets):
        return None
    positions = [target.position for target in targets]
    spread = float(np.linalg.norm(np.asarray(positions[0]) - np.asarray(positions[1])))
    return -spread


def best_disjoint_pairs(scored: list) -> list:
    """Keep the highest-scoring candidates that share no crew.

    Returned to ``find_combinations`` as the filter function.
    """
    taken: set = set()
    kept = []
    for crews, score in sorted(scored, key=lambda item: item[1], reverse=True):
        if any(crew.unique_id in taken for crew in crews):
            continue
        taken.update(crew.unique_id for crew in crews)
        kept.append((crews, score))
    return kept
