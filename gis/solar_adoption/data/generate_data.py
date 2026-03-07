import os
import random
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

# Paths
script_dir = os.path.dirname(__file__)
raster_path = os.path.join(script_dir, "solar_radiation.tif")
vector_path = os.path.join(script_dir, "households.geojson")

def generate_raster():
    """Generate a procedural raster layer representing solar radiation."""
    width = 100
    height = 100
    
    # Create a procedural 2D numpy array (e.g. gradient + noise) for solar radiation
    # Values from 0 (low radiation) to 1 (high radiation)
    y, x = np.mgrid[0:height, 0:width]
    gradient = (x + y) / (width + height)  # Diagonal gradient
    noise = np.random.normal(0, 0.1, (height, width))
    radiation_data = np.clip(gradient + noise, 0, 1)

    # Reshape to (1, height, width) for Rasterio format
    radiation_data = radiation_data.reshape(1, height, width).astype(np.float32)

    # Create a Georeferenced Transform for the Raster (e.g., origin at 0,0, pixel size 1000m)
    transform = from_origin(0, height * 1000, 1000, 1000)

    with rasterio.open(
        raster_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=radiation_data.dtype,
        crs="epsg:3857",
        transform=transform,
    ) as dataset:
        dataset.write(radiation_data)
    print(f"Generated {raster_path}")
    return transform, width, height

def generate_vector(width, height):
    bounds = [0, 0, width * 1000, height * 1000]
    minx, miny, maxx, maxy = bounds

    num_houses = 100
    points = []
    for i in range(num_houses):
        # Generate random points within the bounds
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        points.append(Point(x, y))

    # Create a GeoDataFrame from points
    gdf = gpd.GeoDataFrame(geometry=points, crs="epsg:3857")
    gdf.to_file(vector_path, driver="GeoJSON")
    print(f"Generated {vector_path}")

if __name__ == "__main__":
    t, w, h = generate_raster()
    generate_vector(w, h)
