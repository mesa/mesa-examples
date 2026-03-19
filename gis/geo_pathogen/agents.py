import mesa_geo as mg
from shapely.geometry import Point
import random


class citizen(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)

        self.state = "healthy"
        self.stage = 0
        self.compliant = random.random() < self.model.compliance_rate

    def step(self):

        if self.model.quarantine_status and self.compliant:
            self.quarantine()
        else:
            self.move()

        if self.state == "infected":
            self.stage += 1
            if self.stage > 9:
                chance_of_death = random.random()

                if chance_of_death < 0.1:
                    self.state = "dead"
                    # self.remove()

                else:
                    self.state = "immune"

        cell_state = "healthy"

        cell_neigh = self.model.space.get_neighbors_within_distance(self, self.model.exposure)

        for i in cell_neigh:
            if isinstance(i, citizen) and i.state == "infected":
                cell_state = "infected"

        if self.state == "healthy" and cell_state == "infected":
            chances = random.random()
            if chances > 0.40:
                self.state = "infected"

    def quarantine(self):
       
        if self.state == "dead" or self.state == "infected":
            return
        infected = [
            a for a in self.model.agents
            if isinstance(a, citizen) and a.state == "infected"
        ]
        if not infected:
            self.move()
            return
        nearest = min(infected, key=lambda a: self.geometry.distance(a.geometry))
        dx = self.geometry.x - nearest.geometry.x
        dy = self.geometry.y - nearest.geometry.y
        dist = max((dx**2 + dy**2)**0.5, 1)
        scale = self.model.mobility_range / dist
        np = Point(
            self.geometry.x + dx * scale,
            self.geometry.y + dy * scale
        )
        if self.model.asia_boundary.contains(np):
                self.geometry = np

    def move(self):
        if self.state != "dead":

            change_x = self.random.randint(-self.model.mobility_range, self.model.mobility_range)
            change_y = self.random.randint(-self.model.mobility_range, self.model.mobility_range)
            np = Point(self.geometry.x + change_x, self.geometry.y + change_y)
            if self.model.asia_boundary.contains(np):
                self.geometry = np

class CountryAgent(mg.GeoAgent):
    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.atype = "safe"