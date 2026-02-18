from __future__ import annotations

import gzip

import geopandas as gpd
import mesa
from mesa_geo.geoagent import GeoAgent
from mesa_geo.geospace import GeoSpace
from mesa_geo.raster_layers import Cell, RasterLayer


class UgandaCell(Cell):
    population: float | None

    def __init__(
        self,
        model: mesa.Model | None = None,
        **kwargs: dict,
    ):
        super().__init__(model, **kwargs)
        self.population = None

    def step(self):
        pass


class Lake(GeoAgent):
    pass


class UgandaArea(GeoSpace):
    def __init__(self, crs):
        super().__init__(crs=crs)

    def load_data(self, population_gzip_file, lake_zip_file, world_zip_file, model):
        world_size = gpd.GeoDataFrame.from_file(world_zip_file)
        raster_layer = RasterLayer.from_file(
            population_gzip_file,
            model=model,
            cell_cls=UgandaCell,
            attr_name="population",
            rio_opener=gzip.open,
        )
        raster_layer.crs = world_size.crs
        raster_layer.total_bounds = world_size.total_bounds
        self.add_layer(raster_layer)
        self.lake = gpd.GeoDataFrame.from_file(lake_zip_file).geometry[0]
        self.add_agents(GeoAgent(model, self.lake, self.crs))

    @property
    def population_layer(self):
        return self.layers[0]
