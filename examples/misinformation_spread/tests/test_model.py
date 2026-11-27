import pytest
from model import RuleBasedMisinformationModel
from rulebased_agents import RuleBasedBeliever, RuleBasedSkeptic, RuleBasedSpreader


# Fixtures
@pytest.fixture
def small_model():
    """Small rule-based model for fast testing."""
    return RuleBasedMisinformationModel(
        n_believers=3,
        n_skeptics=2,
        n_spreaders=1,
        connectivity=0.3,
        rng=42,
    )


@pytest.fixture
def default_model():
    """Default param rule-based model matching run.py test config."""
    return RuleBasedMisinformationModel(
        n_believers=4,
        n_skeptics=3,
        n_spreaders=2,
        connectivity=0.3,
        rng=42,
    )


# Initialization
def test_model_initializes(small_model):
    """Model creates without errors."""
    assert small_model is not None


def test_agent_counts(small_model):
    """Correct number of each agent type is created."""
    believers = [a for a in small_model.agents if isinstance(a, RuleBasedBeliever)]
    skeptics = [a for a in small_model.agents if isinstance(a, RuleBasedSkeptic)]
    spreaders = [a for a in small_model.agents if isinstance(a, RuleBasedSpreader)]

    assert len(believers) == 3
    assert len(skeptics) == 2
    assert len(spreaders) == 1


def test_total_agent_count(small_model):
    """Total agent count matches n_believers + n_skeptics + n_spreaders."""
    assert len(list(small_model.agents)) == 6


def test_spread_count_starts_at_zero(small_model):
    """spread_count is 0 before any steps."""
    assert small_model.spread_count == 0


def test_network_created(small_model):
    """Network grid is created with correct number of nodes."""
    assert small_model.grid is not None
    assert len(list(small_model.grid.all_cells)) == 6


# DataCollector
def test_datacollector_keys(small_model):
    """DataCollector has all expected reporter keys."""
    df = small_model.datacollector.get_model_vars_dataframe()
    expected_keys = [
        "Spread Count",
        "Believers Convinced",
        "Skeptics Convinced",
        "Spreaders Active",
    ]
    for key in expected_keys:
        assert key in df.columns, f"Missing datacollector key: {key}"


def test_datacollector_initial_zeros(small_model):
    """All datacollector values are 0 at step 0."""
    df = small_model.datacollector.get_model_vars_dataframe()
    assert df["Spread Count"].iloc[0] == 0
    assert df["Believers Convinced"].iloc[0] == 0
    assert df["Skeptics Convinced"].iloc[0] == 0
    assert df["Spreaders Active"].iloc[0] == 0


# Stepping
def test_dataframe_grows_with_steps(small_model):
    """DataCollector adds one row per step."""
    for _ in range(3):
        small_model.step()
    df = small_model.datacollector.get_model_vars_dataframe()
    assert len(df) == 4  # step 0 + 3 steps


def test_spread_count_nonnegative(small_model):
    """spread_count never goes negative after stepping."""
    for _ in range(5):
        small_model.step()
    assert small_model.spread_count >= 0


def test_spread_count_increases_after_steps(default_model):
    """spread_count is greater than 0 after several steps (probabilistic agents)."""
    for _ in range(5):
        default_model.step()
    assert default_model.spread_count > 0


def test_believers_convinced_bounded(default_model):
    """Believers Convinced never exceeds total number of believers."""
    for _ in range(5):
        default_model.step()
    df = default_model.datacollector.get_model_vars_dataframe()
    assert df["Believers Convinced"].max() <= 4


def test_skeptics_convinced_bounded(default_model):
    """Skeptics Convinced never exceeds total number of skeptics."""
    for _ in range(5):
        default_model.step()
    df = default_model.datacollector.get_model_vars_dataframe()
    assert df["Skeptics Convinced"].max() <= 3


def test_spreaders_active_bounded(default_model):
    """Spreaders Active never exceeds total number of spreaders."""
    for _ in range(5):
        default_model.step()
    df = default_model.datacollector.get_model_vars_dataframe()
    assert df["Spreaders Active"].max() <= 2


# Edge Cases
def test_zero_connectivity_initializes():
    """Model initializes cleanly with no edges in the network."""
    model = RuleBasedMisinformationModel(
        n_believers=2,
        n_skeptics=2,
        n_spreaders=1,
        connectivity=0.0,
        rng=42,
    )
    assert model is not None
    assert len(list(model.agents)) == 5


def test_custom_claim():
    """Model accepts a custom misinformation claim."""
    model = RuleBasedMisinformationModel(
        n_believers=2,
        n_skeptics=1,
        n_spreaders=1,
        misinformation_claim="The moon is made of cheese.",
        rng=42,
    )
    assert model.misinformation_claim == "The moon is made of cheese."


def test_reproducibility():
    """Same seed produces same spread_count after identical steps."""
    model_a = RuleBasedMisinformationModel(
        n_believers=4, n_skeptics=3, n_spreaders=2, connectivity=0.3, rng=99
    )
    model_b = RuleBasedMisinformationModel(
        n_believers=4, n_skeptics=3, n_spreaders=2, connectivity=0.3, rng=99
    )
    for _ in range(3):
        model_a.step()
        model_b.step()

    assert model_a.spread_count == model_b.spread_count
