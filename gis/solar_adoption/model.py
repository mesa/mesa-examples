import os
import random

import geopandas as gpd
import mesa
import mesa_geo as mg
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

from agents import Household


class SolarAdoption(mesa.Model):
    """Model class for the Solar Adoption model."""

    def __init__(
        self,
        num_houses=100,
        social_weight=0.3,
        economic_weight=0.3,
        seed=None,
    ):
        super().__init__(seed=seed)
        self.num_houses = num_houses
        self.social_weight = social_weight
        self.economic_weight = economic_weight

        self.space = mg.GeoSpace(crs="epsg:3857")
        self.total_adopted = 0
        self.running = True

        self._generate_raster_layer()
        self._generate_households()

        self.datacollector = mesa.DataCollector(
            model_reporters={"Adopted": "total_adopted"}
        )

    def _generate_raster_layer(self):
        """Load the raster layer representing solar radiation."""
        script_dir = os.path.dirname(__file__)
        raster_path = os.path.join(script_dir, "data/solar_radiation.tif")
        
        self.raster_layer = mg.RasterLayer.from_file(
            raster_path,
            model=self,
            attr_name="radiation"
        )
        self.space.add_layer(self.raster_layer)

    def _generate_households(self):
        """Load Household agents from vector data."""
        script_dir = os.path.dirname(__file__)
        vector_path = os.path.join(script_dir, "data/households.geojson")
        
        gdf = gpd.read_file(vector_path)

        ac = mg.AgentCreator(Household, model=self)
        self.agents_added = ac.from_GeoDataFrame(gdf)

        for ind, agent in enumerate(self.agents_added):
            agent.unique_id = ind
            x, y = agent.geometry.x, agent.geometry.y
            
            try:
                row, col = self.raster_layer.transform.inverse * (x, y)
                row, col = int(row), int(col)
                row = min(max(row, 0), self.raster_layer.height - 1)
                col = min(max(col, 0), self.raster_layer.width - 1)
                
                val = self.raster_layer.cells[row][col].radiation
                agent.solar_radiation = val
            except Exception:
                agent.solar_radiation = 0.5
                
        self.space.add_agents(self.agents_added)

    def step(self):
        """Run one step of the model."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        if self.total_adopted == self.num_houses:
            self.running = False
