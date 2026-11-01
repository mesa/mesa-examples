# Search and Rescue (Overlapping Meta-Agents + Scenario Sweep)

## Overview

Responders sweep a disaster area in continuous space looking for casualties.
Each casualty has a severity and a survival deadline, and critical casualties
can only be saved by a medic. Medics are scarce, so the interesting question is
not how the responders move but **how they are organised**.

This example puts Mesa 4's command-structure machinery to work on that
question. It demonstrates three things no other example in this repository
covers:

- **Overlapping membership with relation labels.** A medic is permanently a
  `member` of its home crew *and* `on_call` to the medical pool. When another
  crew borrows it, a third `attached` edge appears. Three concurrent groups,
  three different meanings.
- **A nested, queryable hierarchy.** Crews merge into task forces under a
  single incident command, and `at_level()` reports depth structurally rather
  than from any stored attribute.
- **A real parameter sweep.** `run_scenarios` runs the design across a
  pluggable execution backend, so the same experiment runs sequentially or on a
  process pool with identical results.

None of the group structure is stored on the agents. It all lives in the
membership backend and is queried through `model.meta_agents`.

## How It Works

**Space and agents.** Responders and victims are `ContinuousSpaceAgent`s in a
non-toroidal 100×100 space. Victims arrive on a recurring event
(`model.schedule_recurring`) rather than from the step loop.

**Command structure.** All of this is membership state, not agent attributes:

| Group | Members | Relation | What it shows |
|---|---|---|---|
| `Crew` | responders | `member` | groups formed from spatial proximity |
| `MedicalPool` | every medic | `on_call` | **overlap** — medics are also in a crew |
| a borrowing crew | one medic | `attached` | a third, temporary edge |
| `TaskForce_<n>` | crews | `member` | nesting: groups whose members are groups |
| `IncidentCommand` | task forces and loose crews | `member` | root of the hierarchy |

**The step.** Victims past their deadline are lost; responders search their
radius; nearby crews working close targets are merged into task forces via
`find_combinations`; each crew claims a victim, calls for a medic if the
casualty is critical, and closes on it; task forces whose crews are idle are
dissolved.

**The policy switch.** `pooled_specialists` decides whether a crew that lacks a
medic may borrow one. Under pooling it takes the nearest unattached medic,
preferring a sibling crew in its own task force before reaching across the
whole incident. Under the embedded policy it must make do with its own people.

Exactly one crew commands a medic at a time: `Crew.responders()` excludes a
permanent member that is currently attached elsewhere. The three edges describe
*relationships*; command is singular.

## Installation

```bash
pip install -r requirements.txt
```

Mesa 4 is currently a pre-release, so you may need:

```bash
pip install --pre "mesa[rec]>=4.0.0a0"
```

## Running the Model

Interactive dashboard:

```bash
solara run app.py
```

Responders are coloured by the crew commanding them, so a borrowed medic
visibly changes colour and changes back when released. Victims are grey until
discovered, then amber, or red if critical. The side panel lists which medics
are currently seconded and from where.

The parameter sweep:

```bash
python experiment.py                 # process pool, writes results/policy_comparison.png
python experiment.py --sequential    # identical sweep, single process
python experiment.py --compare       # runs both backends and asserts they agree
```

Tests:

```bash
pytest tests/
```

## Project Structure

```
search_and_rescue/
├── app.py                       # Solara dashboard
├── experiment.py                # scenario sweep + figure
├── requirements.txt
├── results/
│   └── policy_comparison.png    # produced by experiment.py
├── sar/
│   ├── agents.py                # Responder, Victim
│   ├── command.py               # Crew / TaskForce / pool behaviour, scoring functions
│   └── model.py                 # SARScenario, SearchAndRescueModel
└── tests/
    ├── test_membership.py       # the meta-agent claims
    └── test_model.py            # model behaviour and scenario wiring
```

## Parameters

| Parameter | Default | Meaning |
|---|---:|---|
| `n_responders` | 40 | Responders in the incident |
| `medic_fraction` | 0.12 | Share of responders who are medics |
| `crew_size` | 4 | Target responders per crew |
| `pooled_specialists` | `True` | May a crew borrow a medic it does not own? |
| `width`, `height` | 100.0 | Extent of the search area |
| `responder_speed` | 2.0 | Distance covered per tick |
| `search_radius` | 7.0 | Detection radius for undiscovered victims |
| `reach_radius` | 2.0 | Distance at which a rescue can be completed |
| `n_initial_victims` | 12 | Casualties present at t=0 |
| `victim_interval` | 2.0 | Time between new arrivals |
| `victim_deadline` | 80.0 | Survival window per casualty |
| `critical_severity` | 0.5 | Severity at or above which a medic is required |
| `taskforce_candidate_cap` | 8 | Crews considered per merge round |
| `taskforce_radius` | 25.0 | Max target separation for merging two crews |

## Results

From `python experiment.py` — 6 crew sizes × 2 policies × 20 replications,
240 runs to t=150.

**Pooling scarce medics beats embedding them, at every crew size.** Extra
victims rescued when crews may borrow:

| crew size | 2 | 3 | 4 | 5 | 6 | 8 |
|---|---:|---:|---:|---:|---:|---:|
| additional rescues | +12.9 | +12.3 | +8.8 | +7.1 | +8.1 | +5.7 |

The advantage is largest with small crews, which are least likely to contain a
medic of their own.

**Smaller crews rescue more but widen span of control.** At crew size 2 the
incident commander is tracking about 15 units directly; at size 8, about 4.
More, smaller crews search better but produce exactly the coordination load
that real incident command systems are designed to bound.

## Verification

Each test backs a specific claim:

| Claim | Test |
|---|---|
| Crews partition the responders | `test_every_responder_belongs_to_exactly_one_crew` |
| Membership genuinely overlaps | `test_medics_belong_to_a_crew_and_the_pool_simultaneously` |
| Relation labels give disjoint views | `test_relation_labels_partition_a_medics_memberships` |
| Secondment adds a third edge and reverses cleanly | `test_borrowed_medic_holds_three_memberships_then_returns` |
| Hierarchy depth is queryable | `test_at_level_walks_the_command_hierarchy`, `test_task_force_deepens_the_hierarchy` |
| Teardown leaves no dangling edges | `test_dissolving_a_task_force_leaves_no_dangling_edges`, `test_removing_an_agent_cascades_to_its_memberships` |
| Backend indexes stay consistent under churn | `test_backend_invariants_hold_through_a_full_run` |
| No casualty is silently dropped | `test_every_victim_is_accounted_for` |
| Critical casualties need a medic | `test_critical_victims_require_a_medic` |
| The policy switch is real | `test_embedded_policy_never_borrows_a_medic`, `test_pooled_policy_borrows_medics` |
| The headline result holds per seed | `test_pooling_rescues_at_least_as_many_as_embedding` |

`python experiment.py --compare` additionally checks all 240 runs agree between
the sequential and process-pool execution backends.

## Notes on the Mesa 4 APIs

Things worth knowing if you are building on the same machinery.

- **Never declare `rng` on a `Scenario` subclass.** It shadows the slot and
  leaves the literal seed where the numpy `Generator` should be. Pass it at
  construction: `SARScenario(rng=42)`. Guarded by
  `test_scenario_seed_is_a_generator_not_an_int`.
- **`MetaAgent.step` shadows your class's `step`.** Group classes are built as
  `type(name, (MetaAgent, *mesa_agent_type))`, so `MetaAgent`'s no-op `step`
  wins the MRO over a `step` on the class you pass as `mesa_agent_type`. Crew
  behaviour is named `advance()` here for that reason.
- **Reusing a group name after dissolving every group of that name raises.**
  `extract_class` does `next(iter(agents_by_type[cls]))` on a bucket that is
  retained but empty, so it raises `StopIteration`. Task forces use unique
  names to avoid it.
- **`TableDataSet` is a poor fit for a recorder.** Its `data` property returns
  the whole accumulated row list on every collection, so registering one with a
  recorder re-snapshots the entire table each tick. This example records a
  model-level time series instead.
- **Portrayal fields must be set consistently.** Mesa's matplotlib backend
  masks each portrayal field against all agents, so setting `edgecolors` on
  only some of them yields a ragged array and an `IndexError` at draw time.
- **The model is never pickled by the sweep.** Only the scenario, config and
  writer cross into a worker; the model is built there. Dynamically created
  meta-agent classes are therefore fine on a `ProcessPoolExecutor`, but
  `extract_output` must return dataframes, not agents.

## Further Reading

- Mesa meta-agents API: `mesa.meta_agents.MetaAgents` and
  `mesa.meta_agents.backend.MembershipBackend`
- Mesa scenarios: `mesa.experimental.scenarios` (`Scenario`,
  `RunConfiguration`, `run_scenarios`)
- The `alliance_formation` example in Mesa core, for meta-agent formation via
  `find_combinations`, and `warehouse` in this repository, for relation labels
  on a static structure
- On bounded span of control in emergency response: the US National Incident
  Management System's Incident Command System, which recommends a span of
  roughly three to seven direct reports
