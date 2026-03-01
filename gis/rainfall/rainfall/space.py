from __future__ import annotations

import gzip

import mesa
import mesa_geo as mg
import numpy as np


class LakeCell(mg.Cell):
    elevation: int | None
    water_level: int | None
    water_level_normalized: float | None

    def __init__(
        self,
        model: mesa.Model | None = None,
        **kwargs: dict,
    ):
        super().__init__(model, **kwargs)
        self.elevation = None
        self.water_level = None
        self.water_level_normalized = None

    def step(self):
        pass


class CraterLake(mg.GeoSpace):
    def __init__(self, crs, water_height, model):
        super().__init__(crs=crs)
        self.model = model
        self.water_height = water_height
        self.outflow = 0

    def set_elevation_layer(self, elevation_gzip_file, crs):
        raster_layer = mg.RasterLayer.from_file(
            elevation_gzip_file,
            model=self.model,
            cell_cls=LakeCell,
            attr_name="elevation",
            rio_opener=gzip.open,
        )
        raster_layer.crs = crs
        raster_layer.apply_raster(
            data=np.zeros(shape=(1, raster_layer.height, raster_layer.width)),
            attr_name="water_level",
        )
        super().add_layer(raster_layer)

    @property
    def raster_layer(self):
        return self.layers[0]

    def is_at_boundary(self, row_idx, col_idx):
        return (
            row_idx == 0
            or row_idx == self.raster_layer.height
            or col_idx == 0
            or col_idx == self.raster_layer.width
        )

    def move_raindrop(self, raindrop, new_pos):
        self.remove_raindrop(raindrop)
        raindrop.pos = new_pos
        self.add_raindrop(raindrop)

    def add_raindrop(self, raindrop):
        x, y = raindrop.pos
        row_ind, col_ind = raindrop.rowcol
        if self.is_at_boundary(row_ind, col_ind):
            raindrop.is_at_boundary = True
            self.outflow += 1
        else:
            self.raster_layer.cells[x][y].water_level += self.water_height

    def remove_raindrop(self, raindrop):
        x, y = raindrop.pos
        self.raster_layer.cells[x][y].water_level -= self.water_height
