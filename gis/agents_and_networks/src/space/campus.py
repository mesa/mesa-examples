import random
from collections import defaultdict
from typing import DefaultDict

import mesa_geo as mg
from shapely.geometry import Point

from ..agent.building import Building
from ..agent.commuter import Commuter

FloatCoordinate = tuple[float, float]


class Campus(mg.GeoSpace):
    homes: tuple[Building]
    works: tuple[Building]
    other_buildings: tuple[Building]
    home_counter: DefaultDict[FloatCoordinate, int]
    _buildings: dict[int, Building]
    _commuters_pos_map: DefaultDict[FloatCoordinate, set[Commuter]]
    _commuter_id_map: dict[int, Commuter]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.homes = ()
        self.works = ()
        self.other_buildings = ()
        self.home_counter = defaultdict(int)
        self._buildings = {}
        self._commuters_pos_map = defaultdict(set)
        self._commuter_id_map = {}

    def get_random_home(self) -> Building:
        return random.choice(self.homes)

    def get_random_work(self) -> Building:
        return random.choice(self.works)

    def get_building_by_id(self, unique_id: int) -> Building:
        return self._buildings[unique_id]

    def add_buildings(self, agents) -> None:
        super().add_agents(agents)
        homes, works, other_buildings = [], [], []
        for agent in agents:
            if isinstance(agent, Building):
                self._buildings[agent.unique_id] = agent
                if agent.function == 0.0:
                    other_buildings.append(agent)
                elif agent.function == 1.0:
                    works.append(agent)
                elif agent.function == 2.0:
                    homes.append(agent)
        self.other_buildings = self.other_buildings + tuple(other_buildings)
        self.works = self.works + tuple(works)
        self.homes = self.homes + tuple(homes)

    def get_commuters_by_pos(self, float_pos: FloatCoordinate) -> set[Commuter]:
        return self._commuters_pos_map[float_pos]

    def get_commuter_by_id(self, commuter_id: int) -> Commuter:
        return self._commuter_id_map[commuter_id]

    def add_commuter(self, agent: Commuter) -> None:
        super().add_agents([agent])
        self._commuters_pos_map[(agent.geometry.x, agent.geometry.y)].add(agent)
        self._commuter_id_map[agent.unique_id] = agent

    def update_home_counter(
        self,
        old_home_pos: FloatCoordinate | None,
        new_home_pos: FloatCoordinate,
    ) -> None:
        if old_home_pos is not None:
            self.home_counter[old_home_pos] -= 1
        self.home_counter[new_home_pos] += 1

    def move_commuter(self, commuter: Commuter, pos: FloatCoordinate) -> None:
        self.__remove_commuter(commuter)
        commuter.geometry = Point(pos)
        self.add_commuter(commuter)

    def __remove_commuter(self, commuter: Commuter) -> None:
        super().remove_agent(commuter)
        del self._commuter_id_map[commuter.unique_id]
        self._commuters_pos_map[(commuter.geometry.x, commuter.geometry.y)].remove(
            commuter
        )
