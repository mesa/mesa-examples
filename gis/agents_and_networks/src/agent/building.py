from __future__ import annotations

import uuid
from random import randrange

import mesa
import mesa_geo as mg
import pyproj
from shapely.geometry import Polygon

FloatCoordinate = tuple[float, float]


class Building(mg.GeoAgent):
    unique_id: int  # an ID that represents the building
    model: mesa.Model
    geometry: Polygon
    crs: pyproj.CRS
    centroid: FloatCoordinate
    name: str
    function: float  # 1.0 for work, 2.0 for home, 0.0 for neither
    entrance_pos: FloatCoordinate  # nearest vertex on road

    def __init__(self, model, geometry, crs) -> None:
        super().__init__(model=model, geometry=geometry, crs=crs)
        self.entrance = None
        self.name = str(uuid.uuid4())
        self.function = randrange(3)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(unique_id={self.unique_id}, name={self.name}, "
            f"function={self.function}, centroid={self.centroid})"
        )

    def __eq__(self, other):
        if isinstance(other, Building):
            return self.unique_id == other.unique_id
        return False

    def __hash__(self) -> int:
        return hash(self.unique_id)
