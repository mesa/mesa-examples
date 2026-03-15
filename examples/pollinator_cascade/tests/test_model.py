import pytest
from agents import Pollinator, Plant
from model import PollinatorCascadeModel


@pytest.fixture
def basic_model():
    """Small model used across multiple tests."""
    return PollinatorCascadeModel(
        n_pollinators=10,
        n_plants=15,
        connectivity=0.5,
        extinction_schedule=[],
        rng=42,
    )


@pytest.fixture
def extinction_model():
    """Model with extinction schedule for cascade tests."""
    return PollinatorCascadeModel(
        n_pollinators=10,
        n_plants=15,
        connectivity=0.5,
        extinction_schedule=[1, 2, 3],
        rng=42,
    )


# Initialization tests


def test_correct_agent_counts(basic_model):
    """Model should create the right number of each agent type."""
    pollinators = [a for a in basic_model.agents if isinstance(a, Pollinator)]
    plants = [a for a in basic_model.agents if isinstance(a, Plant)]
    assert len(pollinators) == 10
    assert len(plants) == 15


def test_agents_start_alive(basic_model):
    """All agents should be alive at initialization."""
    for agent in basic_model.agents:
        assert agent.alive is True


def test_agents_start_at_full_health(basic_model):
    """Pollinators start at energy 1.0, plants at health 1.0."""
    for agent in basic_model.agents:
        if isinstance(agent, Pollinator):
            assert agent.energy == 1.0
        elif isinstance(agent, Plant):
            assert agent.health == 1.0


def test_agents_placed_on_network(basic_model):
    """Every agent should have a cell assigned."""
    for agent in basic_model.agents:
        assert agent.cell is not None


def test_death_counters_start_at_zero(basic_model):
    """Death counters should be zero before any steps run."""
    assert basic_model.total_plant_deaths == 0
    assert basic_model.total_pollinator_deaths == 0


def test_datacollector_initialized(basic_model):
    """DataCollector should exist and have step 0 data."""
    df = basic_model.datacollector.get_model_vars_dataframe()
    assert len(df) == 1
    assert "Alive Pollinators" in df.columns
    assert "Alive Plants" in df.columns
    assert "Cascade Depth" in df.columns


# Step tests


def test_step_advances_counter(basic_model):
    """current_step should increment by 1 each step."""
    assert basic_model.current_step == 0
    basic_model.step()
    assert basic_model.current_step == 1
    basic_model.step()
    assert basic_model.current_step == 2


def test_datacollector_records_each_step(basic_model):
    """DataCollector should have one row per step plus step 0."""
    for _ in range(5):
        basic_model.step()
    df = basic_model.datacollector.get_model_vars_dataframe()
    assert len(df) == 6  # step 0 + 5 steps


def test_energy_declines_over_steps(basic_model):
    """Pollinator energy should decline as steps progress."""
    initial_energy = sum(
        a.energy for a in basic_model.agents if isinstance(a, Pollinator)
    )
    for _ in range(10):
        basic_model.step()
    later_energy = sum(
        a.energy for a in basic_model.agents if isinstance(a, Pollinator) and a.alive
    )
    assert later_energy < initial_energy


# Extinction tests


def test_forced_extinction_removes_pollinator(extinction_model):
    """A forced extinction should reduce alive pollinator count."""
    initial_count = sum(
        1 for a in extinction_model.agents if isinstance(a, Pollinator) and a.alive
    )
    extinction_model.step()  # extinction scheduled at step 1
    after_count = sum(
        1 for a in extinction_model.agents if isinstance(a, Pollinator) and a.alive
    )
    assert after_count < initial_count


def test_death_counter_tracks_removals(extinction_model):
    """total_pollinator_deaths should increase after forced extinction."""
    extinction_model.step()
    assert extinction_model.total_pollinator_deaths >= 1


def test_cascade_depth_increases_after_collapse():
    """After enough extinctions, plants should start dying."""
    model = PollinatorCascadeModel(
        n_pollinators=10,
        n_plants=15,
        connectivity=0.5,
        extinction_schedule=list(range(1, 11)),  # remove one per step
        rng=42,
    )
    for _ in range(80):
        model.step()
    assert model.total_plant_deaths > 0


# Reproducibility tests


def test_same_seed_same_results():
    """Two models with the same seed should produce identical results."""
    model_a = PollinatorCascadeModel(
        n_pollinators=10, n_plants=15, connectivity=0.5, rng=42
    )
    model_b = PollinatorCascadeModel(
        n_pollinators=10, n_plants=15, connectivity=0.5, rng=42
    )
    for _ in range(20):
        model_a.step()
        model_b.step()

    deaths_a = model_a.total_plant_deaths
    deaths_b = model_b.total_plant_deaths
    assert deaths_a == deaths_b


def test_different_seeds_different_results():
    """Two models with different seeds should diverge over time."""
    model_a = PollinatorCascadeModel(
        n_pollinators=10,
        n_plants=15,
        connectivity=0.5,
        extinction_schedule=[5, 10, 15],
        rng=42,
    )
    model_b = PollinatorCascadeModel(
        n_pollinators=10,
        n_plants=15,
        connectivity=0.5,
        extinction_schedule=[5, 10, 15],
        rng=99,
    )
    for _ in range(50):
        model_a.step()
        model_b.step()

    energy_a = sum(a.energy for a in model_a.agents if isinstance(a, Pollinator))
    energy_b = sum(a.energy for a in model_b.agents if isinstance(a, Pollinator))
    assert energy_a != energy_b
