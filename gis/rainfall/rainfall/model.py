from pathlib import Path

import mesa
import mesa_geo as mg
import numpy as np
from shapely.geometry import Point

from .space import CraterLake

script_directory = Path(__file__).resolve().parent


class RaindropAgent(mg.GeoAgent):
    def __init__(self, model, pos):
        super().__init__(
            model,
            geometry=None,
            crs=model.space.crs,
        )
        self.pos = pos
        self.is_at_boundary = False

    @property
    def pos(self):
        return self._pos

    @property
    def indices(self):
        return self._indices

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        if pos is not None:
            x, y = self.pos
            row_idx = self.model.space.raster_layer.height - y - 1
            col_idx = x
            self._indices = row_idx, col_idx
            self.geometry = Point(
                self.model.space.raster_layer.transform * self.indices
            )
        else:
            self.geometry = None

    def step(self):
        if self.is_at_boundary:
            self.remove()
        else:
            lowest_pos = min(
                self.model.space.raster_layer.get_neighboring_cells(
                    pos=self.pos, moore=True, include_center=True
                ),
                key=lambda cell: cell.elevation + cell.water_level,
            ).pos
            if lowest_pos != self.pos:
                self.model.space.move_raindrop(self, lowest_pos)


class Rainfall(mesa.Model):
    def __init__(self, rain_rate=500, water_height=5, export_data=False, num_steps=20):
        super().__init__()
        self.rain_rate = rain_rate
        self.water_amount = 0
        self.export_data = export_data
        self.num_steps = num_steps

        self.space = CraterLake(crs="epsg:4326", water_height=water_height, model=self)
        self.datacollector = mesa.DataCollector(
            {
                "Total Amount of Water": "water_amount",
                "Total Contained": "contained",
                "Total Outflow": "outflow",
            }
        )

        data_path = script_directory / "../data/elevation.asc.gz"
        self.space.set_elevation_layer(data_path, crs="epsg:4326")

    @property
    def contained(self):
        return self.water_amount - self.outflow

    @property
    def outflow(self):
        return self.space.outflow

    def export_water_level_to_file(self):
        self.space.raster_layer.to_file(
            raster_file="data/water_level.asc",
            attr_name="water_level",
            driver="AAIGrid",
        )

    def step(self):
        for _ in range(self.rain_rate):
            random_x = np.random.randint(0, self.space.raster_layer.width)
            random_y = np.random.randint(0, self.space.raster_layer.height)
            raindrop = RaindropAgent(
                model=self,
                pos=(random_x, random_y),
            )
            self.space.add_raindrop(raindrop)
            self.water_amount += 1

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        current_water_level = self.space.raster_layer.get_raster("water_level")
        self.space.raster_layer.apply_raster(
            current_water_level / current_water_level.max(),
            "water_level_normalized",
        )

        if self.steps >= self.num_steps:
            self.running = False
        if not self.running and self.export_data:
            self.export_water_level_to_file()
