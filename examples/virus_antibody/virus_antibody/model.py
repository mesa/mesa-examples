"""
Virus/Antibody Model
===================
A mesa implementation of the Virus/Antibody model, where antibodies and viruses interact in a continuous space.
"""

import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.experimental.continuous_space import ContinuousSpace

from .agents import AntibodyAgent, VirusAgent


class VirusAntibodyModel(Model):
    """
    Virus/Antibody model.

    Handles agent creation, placement and scheduling.
    """

    def __init__(
        # General parameters
        self,
        seed=None,
        initial_antibody=20,
        initial_viruses=20,
        width=100,
        height=100,
        # Antibody parameters
        antibody_duplication_rate=0.01,
        # Virus parameters
        virus_duplication_rate=0.01,
        virus_mutation_rate=0.01,
    ):
        """Create a new Virus/Antibody  model.

        Args:
            seed: Random seed for reproducibility
            initial_antibody: Number of Antibodies in the simulation
            initial_viruses: Number of viruses in the simulation
            width: Width of the space
            height: Height of the space
            antibody_duplication_rate: Probability of duplication for antibodies
            virus_duplication_rate: Probability of duplication for viruses
            virus_mutation_rate: Probability of mutation for viruses

        Indirect Args (not chosen in the graphic interface for clarity reasons):
            antibody_memory_capacity: Number of virus DNA an antibody can remember
            antibody_ko_timeout : Number of step after which an antibody can move after a KO

        """

        super().__init__(seed=seed)

        # Model parameters
        self.initial_antibody = initial_antibody
        self.initial_viruses = initial_viruses
        self.width = width
        self.height = height

        # antibody parameters
        self.antibody_duplication_rate = antibody_duplication_rate

        # virus parameters
        self.virus_duplication_rate = virus_duplication_rate
        self.virus_mutation_rate = virus_mutation_rate

        # Statistics
        self.antibodies_killed = 0
        self.virus_killed = 0
        self.running = True

        # Set up data collection
        model_reporters = {
            "Antibodies": lambda m: len(m.agents_by_type[AntibodyAgent]),
            "Viruses": lambda m: len(m.agents_by_type[VirusAgent]),
        }

        self.datacollector = DataCollector(model_reporters=model_reporters)

        # Set up the space
        self.space = ContinuousSpace(
            [[0, width], [0, height]],
            torus=True,  # change to false and make checks (currently fails)
            random=self.random,
            # n_agents=initial_antibody + initial_viruses,
        )

        # Create and place the Antibody agents
        antibodies_positions = self.rng.random(
            size=(self.initial_antibody, 2)
        ) * np.array(self.space.size)
        directions = self.rng.uniform(-1, 1, size=(self.initial_antibody, 2))
        AntibodyAgent.create_agents(
            self,
            self.initial_antibody,
            self.space,
            initial_position=antibodies_positions,
            direction=directions,
            duplication_rate=self.antibody_duplication_rate,
        )

        # Create and place the Virus agents
        dna = [self.random.randint(0, 9) for _ in range(3)]
        viruses_positions = self.rng.random(size=(self.initial_viruses, 2)) * np.array(
            self.space.size
        )
        directions = self.rng.uniform(-1, 1, size=(self.initial_viruses, 2))

        VirusAgent.create_agents(
            self,
            self.initial_viruses,
            self.space,
            position=viruses_positions,
            duplication_rate=self.virus_duplication_rate,
            mutation_rate=self.virus_mutation_rate,
            dna=dna,
        )

        self.datacollector.collect(self)

    def step(self):
        """Run one step of the model."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        if (
            len(self.agents_by_type[AntibodyAgent]) > 200
            or len(self.agents_by_type[VirusAgent]) > 200
        ):
            print("Too many agents, stopping the simulation")
            self.running = False
        elif len(self.agents_by_type[AntibodyAgent]) == 0:
            self.running = False
            print("All antibodies are dead")
        elif len(self.agents_by_type[VirusAgent]) == 0:
            self.running = False
            print("All viruses are dead")
