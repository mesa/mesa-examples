Agents and Networks Model
=========================

[![](https://img.youtube.com/vi/zIRMNPTBESc/0.jpg)](https://www.youtube.com/watch?v=zIRMNPTBESc)

## Summary

This is an implementation of the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) in Python, using [Mesa](https://github.com/mesa/mesa) and [Mesa-Geo](https://github.com/mesa/mesa-geo).

In this model, buildings are randomly assigned to agents as their home and work places, and the buildings' nearest road vertices are used as their entrances. Agents' commute routes can be found as the shortest path between entrances of their home and work places. These commute routes are segmented according to agents' walking speed. In this way, the movements of agents are constrained on the road network.

### GeoSpace

The GeoSpace contains multiple vector layers, including buildings, lakes, and a road network. More specifically, the road network is constructed from the polyline data and implemented by two underlying data structures: a topological network and a k-d tree. First, by treating road vertices as nodes and line segments as links, a topological network is created using the NetworkX and momepy libraries. NetworkX also provides several methods for shortest path computations (e.g., Dijkstra, A-star). Second, a k-d tree is built for all road vertices through the Scikit-learn library for the purpose of nearest vertex searches.

### GeoAgent

The commuters are the GeoAgents.

## How to run

First install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then run the model:

```bash
solara run app.py -- --campus ub
```

Change `ub` to `gmu` for a different campus map.

Then open your browser to [http://127.0.0.1:8765/](http://127.0.0.1:8765/) and press the play button `▶`.

## License

The data is from the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) and is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
