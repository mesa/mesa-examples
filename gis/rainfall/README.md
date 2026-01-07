# Rainfall Model

[![](https://img.youtube.com/vi/T2FQwFnPDR8/0.jpg)](https://www.youtube.com/watch?v=T2FQwFnPDR8)

## Summary

This is an implementation of the [Rainfall Model](https://github.com/abmgis/abmgis/tree/master/Chapter06-IntegratingABMandGIS/Models/Rainfall) in Python, using [Mesa](https://github.com/mesa/mesa) and [Mesa-Geo](https://github.com/mesa/mesa-geo). Inspired by the NetLogo [Grand Canyon model](http://ccl.northwestern.edu/netlogo/models/GrandCanyon), this is an example of how a digital elevation model (DEM) can be used to create an artificial world.

### GeoSpace

The GeoSpace contains a raster layer representing elevations. It is this elevation value that impacts how the raindrops move over the terrain. Apart from `elevation`, each cell of the raster layer also has a `water_level` attribute that is used to track the amount of water it contains.

### GeoAgent

In this example, the raindrops are the GeoAgents. At each time step, raindrops are randomly created across the landscape to simulate rainfall. The raindrops flow from cells of higher elevation to lower elevation based on their eight surrounding cells (i.e., Moore neighbourhood). The raindrop also has its own height, which allows them to accumulate, gain height and flow if they are trapped at places such as potholes, pools, or depressions. When they reach the boundary of the GeoSpace, they are removed from the model as outflow.

## How to Run

To run the model interactively, run `solara run app.py` in this directory. e.g.

```bash
solara run app.py
```

Then open your browser to [http://127.0.0.1:8765/](http://127.0.0.1:8765/) and press the play button `▶`.

## License

The data is from the [Rainfall Model](https://github.com/abmgis/abmgis/tree/master/Chapter06-IntegratingABMandGIS/Models/Rainfall) and is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
