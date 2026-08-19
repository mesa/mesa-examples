from rumor_mill.model import RumorMillModel


def test_zero_recovery_is_monotonic():
    """With recovery_rate=0.0 (the default), spread should behave like the
    original model: the informed percentage never decreases."""
    model = RumorMillModel(
        width=6,
        height=6,
        know_rumor_ratio=0.1,
        rumor_spread_chance=0.6,
        recovery_rate=0.0,
        rng=1,
    )
    percentages = [model.compute_percentage_knowing_rumor()]
    for _ in range(15):
        model.step()
        percentages.append(model.compute_percentage_knowing_rumor())

    assert all(
        percentages[i] <= percentages[i + 1] for i in range(len(percentages) - 1)
    )


def test_full_recovery_resets_population():
    """With recovery_rate=1.0, every informed agent forgets on its very next
    step, before it gets a chance to tell anyone -- so after exactly one
    model step nobody should know the rumor anymore."""
    model = RumorMillModel(
        width=6,
        height=6,
        know_rumor_ratio=0.3,
        rumor_spread_chance=0.9,
        recovery_rate=1.0,
        rng=2,
    )
    assert model.compute_percentage_knowing_rumor() > 0

    model.step()

    assert model.compute_percentage_knowing_rumor() == 0


def test_recovery_rate_is_passed_to_every_agent():
    """The model should thread its recovery_rate through to each Person."""
    model = RumorMillModel(width=4, height=4, recovery_rate=0.25, rng=3)
    assert all(agent.recovery_rate == 0.25 for agent in model.agents)


def test_recovered_agents_are_tracked():
    """Recoveries should show up in the datacollector, and only when
    recovery_rate > 0."""
    recovering_model = RumorMillModel(
        width=6,
        height=6,
        know_rumor_ratio=0.4,
        recovery_rate=1.0,
        rng=4,
    )
    initial_pct = recovering_model.compute_percentage_knowing_rumor()
    recovering_model.step()
    assert recovering_model.compute_recovered_ratio() == initial_pct

    static_model = RumorMillModel(
        width=6,
        height=6,
        know_rumor_ratio=0.4,
        recovery_rate=0.0,
        rng=4,
    )
    for _ in range(10):
        static_model.step()
        assert static_model.compute_recovered_ratio() == 0


def test_model_runs_with_defaults():
    """Sanity check mirroring the repo-wide smoke test: the model must be
    constructible with no arguments and run for a number of steps."""
    model = RumorMillModel()
    model.run_for(10)
    assert model.time == 10.0


def test_recovered_agents_are_not_double_counted_as_new():
    """An agent that forgets and is later re-told the rumor must not be
    counted again by New_People_Knowing_Rumor -- only genuine first-time
    learners should ever count toward that metric."""
    model = RumorMillModel(
        width=8,
        height=8,
        know_rumor_ratio=0.2,
        rumor_spread_chance=0.6,
        recovery_rate=0.3,
        rng=3,
    )
    never_informed_at_start = sum(1 for a in model.agents if not a.knows_rumor)

    cumulative_new_learners = 0
    for _ in range(200):
        model.step()
        cumulative_new_learners += (
            model.compute_new_people_ratio_knowing_rumor()
            / 100
            * model.number_of_agents
        )

    assert cumulative_new_learners <= never_informed_at_start


def test_no_crash_with_empty_neighborhood():
    """A 1x1 grid has no neighbors at all; stepping an informed agent must
    not raise (guards against referencing an unassigned neighbor)."""
    model = RumorMillModel(
        width=1, height=1, know_rumor_ratio=1.0, rumor_spread_chance=1.0, rng=1
    )
    for _ in range(5):
        model.step()


def test_positional_arguments_stay_backward_compatible():
    """recovery_rate must be appended at the end of the signature, not
    inserted in the middle -- otherwise existing positional calls like
    RumorMillModel(10, 10, 0.1, 0.5, True, 1) would silently reinterpret
    True as recovery_rate and 1 as eight_neightborhood, and drop rng
    entirely."""
    model = RumorMillModel(10, 10, 0.1, 0.5, True, 1)

    assert model.number_of_agents == 100
    assert model.know_rumor_ratio == 0.1
    assert model.rumor_spread_chance == 0.5
    assert model.recovery_rate == 0.0  # untouched by the trailing True/1

    # rng=1 must still actually seed the model (not get silently dropped)
    other = RumorMillModel(10, 10, 0.1, 0.5, True, 1)
    assert [model.random.random() for _ in range(5)] == [
        other.random.random() for _ in range(5)
    ]
