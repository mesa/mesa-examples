from pathlib import Path

import mesa_geo as mg
from agents import Citizen, CountryAgent
from mesa import DataCollector, Model
from shapely.geometry import Point
from shapely.ops import unary_union


def c_healthy(model):
    return sum(
        1 for i in model.agents if isinstance(i, Citizen) and i.state == "healthy"
    )


def c_infected(model):
    return sum(
        1 for i in model.agents if isinstance(i, Citizen) and i.state == "infected"
    )


def c_immune(model):
    return sum(
        1 for i in model.agents if isinstance(i, Citizen) and i.state == "immune"
    )


def c_dead(model):
    return sum(1 for i in model.agents if isinstance(i, Citizen) and i.state == "dead")


class GeoModel(Model):
    def __init__(
        self,
        n=100,
        infn=5,
        quarantine_threshold_strt=25,
        quarantine_threshold_stp=5,
        compliance=0.25,
        exposure_distance=5,
        mobility_range=5,
    ):
        super().__init__()
        self.compliance_rate = compliance
        self.quarantine_thresh_up = quarantine_threshold_strt
        self.quarantine_thresh_lw = quarantine_threshold_stp
        self.infected_count = 0
        self.quarantine_status = False
        self.exposure = exposure_distance
        self.space = mg.GeoSpace(crs="EPSG:4326", warn_crs_conversion=False)
        self.mobility_range = mobility_range
        self.datacollector = DataCollector(
            model_reporters={
                "healthy": c_healthy,
                "immune": c_immune,
                "infected": c_infected,
                "dead": c_dead,
                "quarantine": lambda i: int(i.quarantine_status),
            }
        )

        ac_countries = mg.AgentCreator(CountryAgent, model=self)
        self.countries = ac_countries.from_file(
            Path(__file__).resolve().parent
            / "country_data/ne_110m_admin_0_countries.shp"
        )

        self.countries = [
            c for c in self.countries if c.CONTINENT in ["Asia", "Europe"]
        ]

        for _ in range(n):
            country = self.random.choice(self.countries)
            bounds = country.geometry.bounds
            x = self.random.uniform(bounds[0], bounds[2])
            y = self.random.uniform(bounds[1], bounds[3])
            agent = Citizen(self, Point(x, y), self.space.crs)
            self.space.add_agents(agent)
        self.asia_boundary = unary_union([c.geometry for c in self.countries])
        self.space.add_agents(self.countries)
        citizens = [a for a in self.agents if isinstance(a, Citizen)]
        toinfect = min(infn, len(citizens))
        for i in range(toinfect):
            citizens[i].state = "infected"

    def step(self):
        self.infected_count = c_infected(self)

        if self.infected_count > self.quarantine_thresh_up:
            self.quarantine_status = True
        elif self.infected_count < self.quarantine_thresh_lw:
            self.quarantine_status = False

        self.datacollector.collect(self)

        self.agents_by_type[Citizen].shuffle_do("step")
