from pathlib import Path

import mesa
import mesa_geo as mg
from shapely.geometry import Point

from .agents import NeighbourhoodAgent, PersonAgent

script_directory = Path(__file__).resolve().parent


class GeoSir(mesa.Model):
    """Model class for a simplistic infection model."""

    # Geographical parameters for desired map
    geojson_regions = script_directory / "../data/TorontoNeighbourhoods.geojson"
    unique_id = "HOODNUM"

    def __init__(
        self, pop_size=30, init_infected=0.2, exposure_distance=500, infection_risk=0.2
    ):
        """Create a new InfectedModel
        :param pop_size:        Size of population
        :param init_infected:   Probability of a person agent to start as infected
        :param exposure_distance:   Proximity distance between agents
                                    to be exposed to each other
        :param infection_risk:      Probability of agent to become infected,
                                    if it has been exposed to another infected
        """
        super().__init__()
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.time = 0
        self.counts = None
        self.reset_counts()

        # SIR model parameters
        self.pop_size = pop_size
        self.counts["susceptible"] = pop_size
        self.exposure_distance = exposure_distance
        self.infection_risk = infection_risk

        self.running = True
        self.datacollector = mesa.DataCollector(
            {
                "infected": get_infected_count,
                "susceptible": get_susceptible_count,
                "recovered": get_recovered_count,
                "dead": get_dead_count,
            }
        )

        # Set up the Neighbourhood patches for every region in file
        ac = mg.AgentCreator(NeighbourhoodAgent, model=self)
        neighbourhood_agents = ac.from_file(self.geojson_regions)
        self.space.add_agents(neighbourhood_agents)

        # Generate PersonAgent population
        ac_population = mg.AgentCreator(
            PersonAgent,
            model=self,
            crs=self.space.crs,
            agent_kwargs={"init_infected": init_infected},
        )
        # Generate random location and add agent to grid
        for _ in range(pop_size):
            this_neighbourhood = self.random.randint(
                0, len(neighbourhood_agents) - 1
            )  # Region where agent starts
            center_x, center_y = neighbourhood_agents[
                this_neighbourhood
            ].geometry.centroid.coords.xy
            this_bounds = neighbourhood_agents[this_neighbourhood].geometry.bounds
            spread_x = int(
                this_bounds[2] - this_bounds[0]
            )  # Heuristic for agent spread in region
            spread_y = int(this_bounds[3] - this_bounds[1])
            this_x = center_x[0] + self.random.randint(0, spread_x) - spread_x / 2
            this_y = center_y[0] + self.random.randint(0, spread_y) - spread_y / 2
            this_person = ac_population.create_agent(Point(this_x, this_y))
            self.space.add_agents(this_person)

        self.datacollector.collect(self)

    def reset_counts(self):
        self.counts = {
            "susceptible": 0,
            "infected": 0,
            "recovered": 0,
            "dead": 0,
            "safe": 0,
            "hotspot": 0,
        }

    def step(self):
        """Run one step of the model."""
        self.reset_counts()

        # Activate PersonAgents in random order
        self.agents_by_type[PersonAgent].shuffle_do("step")
        # For NeighbourhoodAgents the order doesn't matter, since they update independently from each other
        self.agents_by_type[NeighbourhoodAgent].do("step")

        self.datacollector.collect(self)

        # Run until no one is infected
        if self.counts["infected"] == 0:
            self.running = False


# Functions needed for datacollector
def get_infected_count(model):
    return model.counts["infected"]


def get_susceptible_count(model):
    return model.counts["susceptible"]


def get_recovered_count(model):
    return model.counts["recovered"]


def get_dead_count(model):
    return model.counts["dead"]
