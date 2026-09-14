"""Tests for the search and rescue model and its scenario wiring."""

from __future__ import annotations

import pytest
from sar import SARScenario, SearchAndRescueModel
from sar.agents import Victim


def test_constructs_with_no_arguments():
    """The repo test harness instantiates every model with no arguments."""
    model = SearchAndRescueModel()
    model.run_for(10)
    assert model.time == 10.0


def test_scenario_seed_is_a_generator_not_an_int():
    """Guards the trap of declaring rng as a Scenario class attribute.

    Declaring ``rng`` on a Scenario subclass shadows the slot and leaves the
    literal seed in place of the numpy Generator.
    """
    scenario = SARScenario(rng=42)
    assert not isinstance(scenario.rng, int)
    assert hasattr(scenario.rng, "random")


def test_runs_are_reproducible_for_a_fixed_seed():
    """Same seed, same outcome."""
    results = []
    for _ in range(2):
        model = SearchAndRescueModel(scenario=SARScenario(rng=3))
        model.run_for(60)
        results.append((model.rescued, model.lost, model.medic_handoffs))
    assert results[0] == results[1]


def test_different_seeds_diverge():
    """The model is actually stochastic."""
    outcomes = set()
    for seed in range(4):
        model = SearchAndRescueModel(scenario=SARScenario(rng=seed))
        model.run_for(60)
        outcomes.add((model.rescued, model.lost))
    assert len(outcomes) > 1


def test_victims_arrive_on_the_scheduled_interval():
    """Victim arrivals come from a recurring event, not the step loop."""
    model = SearchAndRescueModel(
        scenario=SARScenario(rng=1, victim_interval=5.0, n_initial_victims=0)
    )
    assert len(model.victims) == 0
    model.run_for(20)
    # Arrivals at t=5,10,15,20 minus anyone already rescued or lost.
    assert model.rescued + model.lost + len(model.victims) == 4


def test_every_victim_is_accounted_for():
    """No victim silently disappears: rescued + lost + waiting is conserved."""
    model = SearchAndRescueModel(
        scenario=SARScenario(rng=5, victim_interval=2.0, n_initial_victims=10)
    )
    model.run_for(100)
    expected_arrivals = 10 + int(100 / 2.0)
    assert model.rescued + model.lost + len(model.victims) == expected_arrivals


def test_critical_victims_require_a_medic():
    """A crew with no medic cannot complete a critical rescue."""
    model = SearchAndRescueModel(scenario=SARScenario(rng=2, pooled_specialists=False))
    crew = next(c for c in model.crews if not c.has_medic())
    squad = crew.responders()

    victim = Victim(
        model.space,
        model,
        squad[0].position.copy(),
        severity=0.99,
        deadline=100.0,
        critical_severity=0.5,
    )
    assert victim.needs_medic

    assert model.attempt_rescue(crew, victim, squad) is False
    assert model.rescued == 0


def test_non_critical_victim_can_be_rescued_without_a_medic():
    """The converse: generalists handle non-critical casualties."""
    model = SearchAndRescueModel(scenario=SARScenario(rng=2))
    crew = model.crews[0]
    squad = crew.responders()

    victim = Victim(
        model.space,
        model,
        squad[0].position.copy(),
        severity=0.01,
        deadline=100.0,
        critical_severity=0.5,
    )
    assert not victim.needs_medic
    assert model.attempt_rescue(crew, victim, squad) is True
    assert model.rescued == 1


def test_embedded_policy_never_borrows_a_medic():
    """The policy switch genuinely disables reallocation."""
    model = SearchAndRescueModel(scenario=SARScenario(rng=4, pooled_specialists=False))
    model.run_for(120)
    assert model.medic_handoffs == 0
    assert model.borrowed_medics == 0


def test_pooled_policy_borrows_medics():
    """Under pooling, crews without a medic do call for one."""
    model = SearchAndRescueModel(scenario=SARScenario(rng=4, pooled_specialists=True))
    model.run_for(120)
    assert model.medic_handoffs > 0


@pytest.mark.parametrize("seed", range(6))
def test_pooling_rescues_at_least_as_many_as_embedding(seed):
    """The headline claim, checked per seed rather than only on the mean."""
    pooled = SearchAndRescueModel(
        scenario=SARScenario(rng=seed, pooled_specialists=True)
    )
    embedded = SearchAndRescueModel(
        scenario=SARScenario(rng=seed, pooled_specialists=False)
    )
    pooled.run_for(150)
    embedded.run_for(150)
    assert pooled.rescued >= embedded.rescued


def test_data_recorder_exposes_the_sweep_outcome():
    """RunConfiguration.extract_output reads these frames."""
    model = SearchAndRescueModel(scenario=SARScenario(rng=1))
    model.run_for(20)

    frame = model.data_recorder.get_table_dataframe("response")
    assert len(frame) == 21
    for column in ("rescued", "lost", "span_of_control", "medic_handoffs", "time"):
        assert column in frame.columns
    assert frame["rescued"].is_monotonic_increasing
