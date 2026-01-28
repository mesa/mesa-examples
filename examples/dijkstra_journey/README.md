Dijkstra_journey
========================

Dijkstra's algorithm, developed by Edsger W. Dijkstra in 1956, is a classic algorithm used to find the shortest paths between nodes in a graph. Its applications span network routing, geographical mapping, and various optimization problems.

## How to run
To launch the interactive visualization, run `solara run app.py` in this directory.


## Algorithm details
 formula used in Dijkstra's algorithm:

[ d[v] = \min(d[v], d[u] + w(u, v)) \]

where:
- \( d[v] \) is the current shortest distance from the start node to node \( v \).
- \( d[u] \) is the shortest distance from the start node to node \( u \).
- \( w(u, v) \) is the weight of the edge between nodes \( u \) and \( v \).
