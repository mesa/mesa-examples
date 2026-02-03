from __future__ import annotations

import gzip
import random

import mesa
import mesa_geo as mg
import numpy as np
import rasterio as rio


class UrbanCell(mg.Cell):
    urban: bool | None
    slope: int | None
    road_1: int | None
    excluded: int | None
    land_use: int | None

    suitable: bool | None
    road: bool | None
    run_value: int | None
    road_found: bool | None
    road_pixel: UrbanCell | None

    new_urbanized: bool | None
    old_urbanized: bool | None

    def __init__(
        self,
        model: mesa.Model | None = None,
        **kwargs: dict,
    ):
        super().__init__(model, **kwargs)
        self.urban = None
        self.slope = None
        self.road_1 = None
        self.excluded = None
        self.land_use = None

        self.suitable = None
        self.road = None
        self.run_value = None
        self.road_found = None
        self.road_pixel = None
        self.new_urbanized = None
        self.old_urbanized = None

    def step(self):
        self._new_spreading_center_growth()
        self._edge_growth()

    def _new_spreading_center_growth(self) -> None:
        if self.new_urbanized:
            x = np.random.randint(self.model.max_coefficient)
            if x < self.model.breed_coefficient:
                neighbors = self.model.space.raster_layer.get_neighboring_cells(
                    self.pos, moore=True
                )
                for random_neighbor in random.choices(neighbors, k=2):
                    if (not random_neighbor.urban) and random_neighbor.suitable:
                        random_neighbor.urban = True
                        random_neighbor.new_urbanized = True
            self.new_urbanized = False

    def _edge_growth(self) -> None:
        if self.urban:
            x = np.random.randint(self.model.max_coefficient)
            if x < self.model.spread_coefficient:
                neighbors = self.model.space.raster_layer.get_neighboring_cells(
                    self.pos, moore=True
                )
                urban_neighbors = [c for c in neighbors if c.urban]
                non_urban_neighbors = [c for c in neighbors if not c.urban]
                if len(urban_neighbors) > 1 and len(non_urban_neighbors) > 0:
                    random_non_urban_neighbor = random.choice(non_urban_neighbors)
                    if random_non_urban_neighbor.suitable:
                        random_non_urban_neighbor.urban = True
                        random_non_urban_neighbor.new_urbanized = True


class City(mg.GeoSpace):
    def __init__(self, width, height, crs, total_bounds, model):
        super().__init__(crs=crs)
        self.add_layer(
            mg.RasterLayer(width, height, crs, total_bounds, model, cell_cls=UrbanCell)
        )

    def load_datasets(
        self, urban_data, slope_data, road_data, excluded_data, land_use_data
    ):
        data = {
            "urban": urban_data,
            "slope": slope_data,
            "road_1": road_data,
            "excluded": excluded_data,
            "land_use": land_use_data,
        }
        for attribute_name, data_file in data.items():
            with rio.open(data_file, "r", opener=gzip.open) as dataset:
                values = dataset.read()
            self.raster_layer.apply_raster(values, attr_name=attribute_name)

        for cell in self.raster_layer:
            cell.urban = cell.urban == 2
            cell.old_urbanized = cell.urban

    def check_road(self):
        for cell in self.raster_layer:
            cell.road = cell.road_1 > 0

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
