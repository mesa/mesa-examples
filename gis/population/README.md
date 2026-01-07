# Population Model

[![](https://img.youtube.com/vi/0k8tsYPVwQs/0.jpg)](https://www.youtube.com/watch?v=0k8tsYPVwQs)

## Summary

This is an implementation of the [Uganda Example](https://github.com/abmgis/abmgis/tree/master/Chapter05-GIS/Models/UgandaExample) in Python, using [Mesa](https://github.com/mesa/mesa) and [Mesa-Geo](https://github.com/mesa/mesa-geo).

### GeoSpace

The GeoSpace consists of both a raster and a vector layer. The raster layer contains population data for each cell, and it is this data that is used for model initialisation, in the sense creating the agents. The vector layer shown in blue color represents a lake in Uganda. It overlays with the raster layer to mask out the cells that agents cannot move into.

### GeoAgent

The GeoAgents are people, created based on the population data. As this is a simple example model, the agents only move randomly to neighboring cells at each time step. To make the simulation more realistic and visually appealing, the agents in the same cell have a randomized position within the cell, so that they don’t stand on top of each other at exactly the same coordinate.

## How to Run

To run the model interactively, run `solara run app.py` in this directory. e.g.

```bash
solara run app.py
```

Then open your browser to [http://127.0.0.1:8765/](http://127.0.0.1:8765/) and press the play button `▶`.

## License

The data is from the [Uganda Example](https://github.com/abmgis/abmgis/tree/master/Chapter05-GIS/Models/UgandaExample) and is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
