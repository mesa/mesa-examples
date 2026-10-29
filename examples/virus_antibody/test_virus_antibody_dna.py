"""Regression tests for virus dna ownership on duplication."""

import mesa
from mesa.experimental.continuous_space import ContinuousSpace
from virus_antibody.agents import VirusAgent


def make_virus(dna, mutation_rate=1.0):
    """Build a single virus in a bare model, bypassing VirusAntibodyModel."""
    model = mesa.Model(rng=1)
    space = ContinuousSpace([[0, 10], [0, 10]], torus=True, random=model.random)
    return VirusAgent(
        model,
        space,
        mutation_rate=mutation_rate,
        duplication_rate=0.0,
        position=(1.0, 1.0),
        dna=dna,
    )


def test_generate_dna_does_not_rewrite_the_genome_it_is_given():
    """generate_dna() must leave its argument alone.

    duplicate() calls self.generate_dna(self.dna), so mutating in place would
    rewrite the parent's own genome every time it reproduces.
    """
    virus = make_virus([1, 2, 3])
    parent_dna = virus.dna
    before = list(parent_dna)

    child_dna = virus.generate_dna(parent_dna)

    assert parent_dna == before, "parent genome was mutated in place"
    assert child_dna is not parent_dna, "child shares the parent's dna list"


def test_duplication_gives_the_child_its_own_dna():
    """A child must not alias its parent's dna list."""
    parent = make_virus([4, 5, 6])
    before = list(parent.dna)

    parent.duplicate()

    children = [
        agent
        for agent in parent.model.agents_by_type[VirusAgent]
        if agent is not parent
    ]
    assert len(children) == 1
    child = children[0]

    assert parent.dna == before, "spawning a child rewrote the parent's genome"
    assert child.dna is not parent.dna, "parent and child share one dna list"

    child.dna[0] = (child.dna[0] + 1) % 10
    assert parent.dna == before, "mutating the child changed the parent"
