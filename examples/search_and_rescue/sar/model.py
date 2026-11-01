"""Search and rescue with a dynamic command hierarchy.

The point of this example is that the *command structure* is the object of
study. Responders are organised into crews, crews into task forces, and task
forces under a single incident command. All of that structure lives in Mesa's
meta-agent membership backend rather than in agent attributes, which lets a
responder belong to several groups at once under different relation labels.

The scarce resource is medics. Every medic is permanently a ``member`` of its
home crew and simultaneously ``on_call`` to the medical pool. When some other
crew finds a critical victim it can borrow that medic, which adds a third,
temporary ``attached`` edge. That overlap is what the ``pooled_specialists``
policy switch turns on and off, and what the parameter sweep measures.
"""

from __future__ import annotations

import numpy as np
from mesa import Model
from mesa.experimental.continuous_space import ContinuousSpace
from mesa.experimental.data_collection import DataRecorder
from mesa.experimental.scenarios import Scenario
from mesa.meta_agents import MetaAgents
from mesa.time import Schedule

from .agents import GENERALIST, MEDIC, Responder, Victim
from .command import (
    ATTACHED,
    MEMBER,
    ON_CALL,
    Crew,
    IncidentCommand,
    MedicalPool,
    TaskForce,
    best_disjoint_pairs,
    pair_score,
)


class SARScenario(Scenario):
    """Parameters for the search and rescue model.

    Note that ``rng`` is deliberately not declared here. Declaring it as a
    class attribute shadows the ``Scenario`` slot and replaces the numpy
    Generator with the literal seed. Pass it at construction instead:
    ``SARScenario(rng=42)``.
    """

    n_responders: int = 40
    medic_fraction: float = 0.12
    crew_size: int = 4
    pooled_specialists: bool = True

    width: float = 100.0
    height: float = 100.0
    responder_speed: float = 2.0
    search_radius: float = 7.0
    reach_radius: float = 2.0

    n_initial_victims: int = 12
    victim_interval: float = 2.0
    victim_deadline: float = 80.0
    critical_severity: float = 0.5

    taskforce_candidate_cap: int = 8
    taskforce_radius: float = 25.0


class SearchAndRescueModel(Model):
    """Responders self-organise to reach victims before their deadlines."""

    def __init__(self, scenario: SARScenario = SARScenario):
        """Build the space, the responders and the initial command structure."""
        super().__init__(scenario=scenario)
        params = self.scenario

        self.space = ContinuousSpace(
            [[0, params.width], [0, params.height]],
            torus=False,
            random=self.random,
            n_agents=params.n_responders + 4 * params.n_initial_victims + 64,
        )
        self.meta_agents = MetaAgents(self)

        self.rescued = 0
        self.lost = 0
        self.medic_handoffs = 0
        self._task_force_counter = 0

        self._build_responders()
        self._build_command_structure()

        for _ in range(params.n_initial_victims):
            self._spawn_victim()

        self._victim_arrivals = self.schedule_recurring(
            self._spawn_victim,
            Schedule(interval=params.victim_interval, start=params.victim_interval),
        )

        self.data_registry.track_model(
            self,
            "response",
            fields=[
                "rescued",
                "lost",
                "outstanding",
                "n_crews",
                "n_task_forces",
                "span_of_control",
                "borrowed_medics",
                "medic_handoffs",
            ],
        )
        self.data_recorder = DataRecorder(self, {"response": {}})

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def _build_responders(self) -> None:
        """Create responders, a fraction of whom are medics."""
        params = self.scenario
        n_medics = round(params.n_responders * params.medic_fraction)
        positions = self.rng.random((params.n_responders, 2)) * self.space.size

        for index in range(params.n_responders):
            Responder(
                self.space,
                self,
                positions[index],
                MEDIC if index < n_medics else GENERALIST,
                params.responder_speed,
            )

    def _build_command_structure(self) -> None:
        """Create the incident command, the medical pool and the crews.

        Crews are created greedily from spatial proximity. Every crew shares
        the group name ``"Crew"``, so they share one dynamically built class
        while remaining distinct groups — the same pattern the warehouse
        example uses. Because the name is therefore ambiguous, groups are
        always addressed by object, never by name.
        """
        membership = self.meta_agents
        params = self.scenario

        self.incident_command = membership.create(
            "IncidentCommand", [], mesa_agent_type=IncidentCommand
        )
        self.medical_pool = membership.create(
            "MedicalPool", [], mesa_agent_type=MedicalPool
        )

        unassigned = list(self.responders)
        while unassigned:
            seed = unassigned.pop(0)
            squad = [seed]
            if unassigned:
                distances = np.linalg.norm(
                    np.array([r.position for r in unassigned]) - seed.position, axis=1
                )
                picks = sorted(np.argsort(distances)[: params.crew_size - 1])
                squad.extend(unassigned[i] for i in picks)
                for i in reversed(picks):
                    unassigned.pop(i)

            crew = membership.create(
                "Crew", squad, mesa_agent_type=Crew, meta_attributes={"target": None}
            )
            membership.add_member(self.incident_command, crew, relation=MEMBER)

        # Every medic is on call to the pool *in addition to* its home crew.
        # This is the overlapping membership the model is built around.
        for responder in self.responders:
            if responder.is_medic:
                membership.add_member(self.medical_pool, responder, relation=ON_CALL)

    # ------------------------------------------------------------------
    # views
    # ------------------------------------------------------------------

    @property
    def responders(self) -> list[Responder]:
        """Every responder currently in the model."""
        return [a for a in self.agents if isinstance(a, Responder)]

    @property
    def victims(self) -> list[Victim]:
        """Every victim still awaiting rescue."""
        return [a for a in self.agents if isinstance(a, Victim)]

    @property
    def crews(self) -> list:
        """Every crew group."""
        return [a for a in self.agents if isinstance(a, Crew)]

    @property
    def task_forces(self) -> list:
        """Every task force group."""
        return [a for a in self.agents if isinstance(a, TaskForce)]

    @property
    def outstanding(self) -> int:
        """Victims discovered but not yet reached."""
        return sum(1 for victim in self.victims if victim.discovered)

    @property
    def n_crews(self) -> int:
        """Number of crews."""
        return len(self.crews)

    @property
    def n_task_forces(self) -> int:
        """Number of task forces."""
        return len(self.task_forces)

    @property
    def span_of_control(self) -> int:
        """Units reporting directly to incident command.

        This deliberately mixes task forces and standalone crews, because that
        is exactly what a commander is tracking. It is computed structurally
        with ``at_level`` rather than stored anywhere.
        """
        return len(self.meta_agents.at_level(1, root=self.incident_command))

    @property
    def borrowed_medics(self) -> int:
        """Medics currently attached to a crew other than their own."""
        return sum(
            1
            for _, _, relation in self.meta_agents.backend.as_triplets()
            if relation == ATTACHED
        )

    # ------------------------------------------------------------------
    # victim lifecycle
    # ------------------------------------------------------------------

    def _spawn_victim(self) -> None:
        """Place a new victim. Called on a recurring schedule."""
        params = self.scenario
        Victim(
            self.space,
            self,
            self.rng.random(2) * self.space.size,
            float(self.rng.random()),
            params.victim_deadline,
            params.critical_severity,
        )

    def _expire_victims(self) -> None:
        """Remove victims whose survival window has closed."""
        for victim in self.victims:
            if not victim.is_expired:
                continue
            self.lost += 1
            crew = victim.assigned_crew
            if crew is not None:
                crew.target = None
                self.release_medic(crew)
            victim.assigned_crew = None
            victim.remove()

    def claim_victim(self, crew):
        """Assign the nearest unclaimed, discovered victim to ``crew``."""
        centroid = crew.centroid()
        if centroid is None:
            return None
        available = [
            victim
            for victim in self.victims
            if victim.discovered and victim.assigned_crew is None
        ]
        if not available:
            return None
        target = min(
            available,
            key=lambda victim: float(np.linalg.norm(victim.position - centroid)),
        )
        target.assigned_crew = crew
        return target

    def attempt_rescue(self, crew, victim, squad) -> bool:
        """Rescue ``victim`` if the crew has closed on it with the right people."""
        reach = self.scenario.reach_radius
        in_reach = [
            responder
            for responder in squad
            if float(np.linalg.norm(responder.position - victim.position)) <= reach
        ]
        if not in_reach:
            return False
        if victim.needs_medic and not any(r.is_medic for r in in_reach):
            return False

        self.rescued += 1
        victim.assigned_crew = None
        victim.remove()
        crew.target = None
        self.release_medic(crew)
        return True

    # ------------------------------------------------------------------
    # specialist reallocation — the overlapping-membership payoff
    # ------------------------------------------------------------------

    def request_medic(self, crew) -> bool:
        """Borrow a medic for ``crew`` from the pool.

        Under the embedded policy a crew may only use a medic that is already
        one of its own members, so this is a no-op. Under the pooled policy any
        unattached medic may be borrowed, preferring one from a sibling crew in
        the same task force before reaching across the whole incident.
        """
        if not self.scenario.pooled_specialists:
            return False

        centroid = crew.centroid()
        if centroid is None:
            return False

        membership = self.meta_agents
        available = [
            medic
            for medic in membership.members_of(self.medical_pool, relation=ON_CALL)
            if len(membership.query_memberships(medic, relation=ATTACHED)) == 0
        ]
        if not available:
            return False

        siblings = self._sibling_crews(crew)
        if siblings:
            local = [
                medic
                for medic in available
                if any(
                    sibling in membership.groups_of(medic, relation=MEMBER)
                    for sibling in siblings
                )
            ]
            available = local or available

        nearest = min(
            available,
            key=lambda medic: float(np.linalg.norm(medic.position - centroid)),
        )
        membership.add_member(crew, nearest, relation=ATTACHED)
        self.medic_handoffs += 1
        return True

    def release_medic(self, crew) -> None:
        """Return any borrowed medic to the pool."""
        membership = self.meta_agents
        for medic in list(membership.members_of(crew, relation=ATTACHED)):
            membership.remove_member(crew, medic, relation=ATTACHED)

    def _sibling_crews(self, crew) -> list:
        """Crews sharing a task force with ``crew``."""
        membership = self.meta_agents
        siblings = []
        for group in membership.groups_of(crew, relation=MEMBER):
            if isinstance(group, TaskForce):
                siblings.extend(
                    other
                    for other in membership.members_of(group, relation=MEMBER)
                    if other is not crew
                )
        return siblings

    # ------------------------------------------------------------------
    # task force formation and dissolution
    # ------------------------------------------------------------------

    def _form_task_forces(self) -> None:
        """Merge crews working nearby victims into task forces."""
        membership = self.meta_agents
        loose = [
            crew
            for crew in self.crews
            if crew.target is not None and not self._task_force_of(crew)
        ]
        if len(loose) < 2:
            return

        candidates = loose[: self.scenario.taskforce_candidate_cap]
        combinations = membership.find_combinations(
            candidates,
            size=2,
            evaluation_func=pair_score,
            filter_func=best_disjoint_pairs,
        )

        for crews, score in combinations:
            if -score > self.scenario.taskforce_radius:
                continue
            # Task forces get unique names. Reusing one name would both risk
            # silently merging into a surviving group and trip mesa's
            # extract_class, which raises StopIteration when every group of a
            # given name has been dissolved but its agents_by_type bucket is
            # retained empty.
            self._task_force_counter += 1
            task_force = membership.create(
                f"TaskForce_{self._task_force_counter}",
                list(crews),
                mesa_agent_type=TaskForce,
            )
            for crew in crews:
                membership.remove_member(self.incident_command, crew, relation=MEMBER)
            membership.add_member(self.incident_command, task_force, relation=MEMBER)

    def _dissolve_idle_task_forces(self) -> None:
        """Dissolve task forces whose crews have nothing left to do."""
        membership = self.meta_agents
        for task_force in self.task_forces:
            crews = task_force.crews()
            if not crews or any(crew.target is not None for crew in crews):
                continue
            for crew in crews:
                membership.add_member(self.incident_command, crew, relation=MEMBER)
            membership.dissolve(task_force)

    def _task_force_of(self, crew):
        """Return the task force containing ``crew``, or None."""
        for group in self.meta_agents.groups_of(crew, relation=MEMBER):
            if isinstance(group, TaskForce):
                return group
        return None

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance the response by one tick."""
        self._expire_victims()

        for responder in self.responders:
            responder.search(self.scenario.search_radius)

        self._form_task_forces()

        for crew in self.crews:
            crew.advance()

        self._dissolve_idle_task_forces()
