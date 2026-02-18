from __future__ import annotations

import random

import mesa
import mesa_geo as mg
import numpy as np
import pyproj
from shapely.geometry import LineString, Point

from ..space.utils import UnitTransformer, redistribute_vertices
from .building import Building

FloatCoordinate = tuple[float, float]


class Commuter(mg.GeoAgent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: mesa.Model
    geometry: Point
    crs: pyproj.CRS
    origin: Building  # where he begins his trip
    destination: Building  # the destination he wants to arrive at
    my_path: list[
        FloatCoordinate
    ]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    my_home: Building
    my_work: Building
    start_time_h: int  # time to start going to work, hour and minute
    start_time_m: int
    end_time_h: int  # time to leave work, hour and minute
    end_time_m: int
    work_friends_id: list[int]  # set of friends at work
    status: str  # work, home, or transport
    testing: bool  # a temp variable used in identifying friends
    happiness_home: float
    happiness_work: float
    MIN_FRIENDS: int
    MAX_FRIENDS: int
    HAPPINESS_INCREASE: float
    HAPPINESS_DECREASE: float
    SPEED: float
    CHANCE_NEW_FRIEND: float  # percent chance to make a new friend every 5 min

    def __init__(self, model, geometry, crs) -> None:
        super().__init__(model, geometry, crs)
        self.my_home = None
        self.start_time_h = round(np.random.normal(6.5, 1))
        while self.start_time_h < 6 or self.start_time_h > 9:
            self.start_time_h = round(np.random.normal(6.5, 1))
        self.start_time_m = np.random.randint(0, 12) * 5
        self.end_time_h = self.start_time_h + 8  # will work for 8 hours
        self.end_time_m = self.start_time_m
        self.happiness_work = 100.0
        self.happiness_home = 100.0
        self.work_friends_id = []
        self.testing = False

    def __repr__(self) -> str:
        return (
            f"Commuter(unique_id={self.unique_id}, geometry={self.geometry}, "
            f"status={self.status}, num_home_friends={self.num_home_friends}, "
            f"num_work_friends={len(self.work_friends_id)})"
        )

    @property
    def num_home_friends(self) -> int:
        return self.model.space.home_counter[self.my_home.centroid]

    @property
    def num_work_friends(self) -> int:
        return len(self.work_friends_id)

    def set_home(self, new_home: Building) -> None:
        old_home_pos = self.my_home.centroid if self.my_home else None
        self.my_home = new_home
        self.happiness_home = 100.0
        self.model.space.update_home_counter(
            old_home_pos=old_home_pos, new_home_pos=self.my_home.centroid
        )

    def set_work(self, new_work: Building) -> None:
        self.my_work = new_work
        self.work_friends_id = []
        self.happiness_work = 100.0

    def step(self) -> None:
        self._check_happiness()
        self._prepare_to_move()
        self._move()
        self._make_friends_at_work()

    def _check_happiness(self) -> None:
        if self.status == "work":
            if len(self.work_friends_id) > self.MAX_FRIENDS:
                self.happiness_work -= self.HAPPINESS_DECREASE * (
                    len(self.work_friends_id) - self.MAX_FRIENDS
                )
            else:
                if len(self.work_friends_id) < self.MIN_FRIENDS:
                    self.happiness_work -= self.HAPPINESS_DECREASE * (
                        self.MIN_FRIENDS - len(self.work_friends_id)
                    )
                else:
                    self.happiness_work += self.HAPPINESS_INCREASE
            if self.happiness_work < 0.0:
                self._relocate_work()
        elif self.status == "home":
            if self.num_home_friends > self.MAX_FRIENDS:
                self.happiness_home -= self.HAPPINESS_DECREASE * (
                    self.num_home_friends - self.MAX_FRIENDS
                )
            else:
                if self.num_home_friends < self.MIN_FRIENDS:
                    self.happiness_home -= self.HAPPINESS_DECREASE * (
                        self.MIN_FRIENDS - self.num_home_friends
                    )
                else:
                    self.happiness_home += self.HAPPINESS_INCREASE
            if self.happiness_home < 0.0:
                self._relocate_home()

    def _prepare_to_move(self) -> None:
        # start going to work
        if (
            self.status == "home"
            and self.model.hour == self.start_time_h
            and self.model.minute == self.start_time_m
        ):
            self.origin = self.model.space.get_building_by_id(self.my_home.unique_id)
            self.model.space.move_commuter(self, pos=self.origin.centroid)
            self.destination = self.model.space.get_building_by_id(
                self.my_work.unique_id
            )
            self._path_select()
            self.status = "transport"
        # start going home
        elif (
            self.status == "work"
            and self.model.hour == self.end_time_h
            and self.model.minute == self.end_time_m
        ):
            self.origin = self.model.space.get_building_by_id(self.my_work.unique_id)
            self.model.space.move_commuter(self, pos=self.origin.centroid)
            self.destination = self.model.space.get_building_by_id(
                self.my_home.unique_id
            )
            self._path_select()
            self.status = "transport"

    def _move(self) -> None:
        if self.status == "transport":
            if self.step_in_path < len(self.my_path):
                next_position = self.my_path[self.step_in_path]
                self.model.space.move_commuter(self, next_position)
                self.step_in_path += 1
            else:
                self.model.space.move_commuter(self, self.destination.centroid)
                if self.destination == self.my_work:
                    self.status = "work"
                elif self.destination == self.my_home:
                    self.status = "home"
                self.model.got_to_destination += 1

    def advance(self) -> None:
        raise NotImplementedError

    def _relocate_home(self) -> None:
        while (new_home := self.model.space.get_random_home()) == self.my_home:
            continue
        self.set_home(new_home)

    def _relocate_work(self) -> None:
        while (new_work := self.model.space.get_random_work()) == self.my_work:
            continue
        self.set_work(new_work)

    def _path_select(self) -> None:
        self.step_in_path = 0
        if (
            cached_path := self.model.walkway.get_cached_path(
                source=self.origin.entrance_pos, target=self.destination.entrance_pos
            )
        ) is not None:
            self.my_path = cached_path
        else:
            self.my_path = self.model.walkway.get_shortest_path(
                source=self.origin.entrance_pos, target=self.destination.entrance_pos
            )
            self.model.walkway.cache_path(
                source=self.origin.entrance_pos,
                target=self.destination.entrance_pos,
                path=self.my_path,
            )
        self._redistribute_path_vertices()

    def _redistribute_path_vertices(self) -> None:
        # if origin and destination share the same entrance, then self.my_path
        # will contain only this entrance node,
        # and len(self.path) == 1. There is no need to redistribute path vertices.
        if len(self.my_path) > 1:
            unit_transformer = UnitTransformer(degree_crs=self.model.walkway.crs)
            original_path = LineString([Point(p) for p in self.my_path])
            # from degree unit to meter
            path_in_meters = unit_transformer.degree2meter(original_path)
            redistributed_path_in_meters = redistribute_vertices(
                path_in_meters, self.SPEED
            )
            # meter back to degree
            redistributed_path_in_degree = unit_transformer.meter2degree(
                redistributed_path_in_meters
            )
            self.my_path = list(redistributed_path_in_degree.coords)

    def _make_friends_at_work(self) -> None:
        if self.status == "work":
            for work_friend_id in self.work_friends_id:
                self.model.space.get_commuter_by_id(work_friend_id).testing = True
            commuters_to_check = [
                c
                for c in self.model.space.get_commuters_by_pos(
                    (self.geometry.x, self.geometry.y)
                )
                if not c.testing
            ]
            if (
                commuters_to_check
                and np.random.uniform(0.0, 100.0) < self.CHANCE_NEW_FRIEND
            ):
                target_friend = random.choice(commuters_to_check)
                target_friend.work_friends_id.append(self.unique_id)
                self.work_friends_id.append(target_friend.unique_id)
            for work_friend_id in self.work_friends_id:
                self.model.space.get_commuter_by_id(work_friend_id).testing = False
