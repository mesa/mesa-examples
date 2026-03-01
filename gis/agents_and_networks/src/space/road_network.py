from __future__ import annotations

import pickle

import geopandas as gpd
import momepy
import networkx as nx
import pyproj
from sklearn.neighbors import KDTree

from .utils import segmented

FloatCoordinate = tuple[float, float]


class RoadNetwork:
    _nx_graph: nx.Graph
    _kd_tree: KDTree
    _crs: pyproj.CRS

    def __init__(self, lines: gpd.GeoSeries):
        segmented_lines = gpd.GeoDataFrame(geometry=segmented(lines))
        G = momepy.gdf_to_nx(segmented_lines, approach="primal", length="length")  # noqa: N806
        self.nx_graph = G.subgraph(max(nx.connected_components(G), key=len))
        self.crs = lines.crs

    @property
    def nx_graph(self) -> nx.Graph:
        return self._nx_graph

    @nx_graph.setter
    def nx_graph(self, nx_graph) -> None:
        self._nx_graph = nx_graph
        self._kd_tree = KDTree(nx_graph.nodes)

    @property
    def crs(self) -> pyproj.CRS:
        return self._crs

    @crs.setter
    def crs(self, crs) -> None:
        self._crs = crs

    def get_nearest_node(self, float_pos: FloatCoordinate) -> FloatCoordinate:
        node_index = self._kd_tree.query([float_pos], k=1, return_distance=False)
        node_pos = self._kd_tree.get_arrays()[0][node_index[0, 0]]
        return tuple(node_pos)

    def get_shortest_path(
        self, source: FloatCoordinate, target: FloatCoordinate
    ) -> list[FloatCoordinate]:
        from_node_pos = self.get_nearest_node(source)
        to_node_pos = self.get_nearest_node(target)
        # return nx.shortest_path(self.nx_graph, from_node_pos,
        #                         to_node_pos, method="dijkstra", weight="length")
        return nx.astar_path(self.nx_graph, from_node_pos, to_node_pos, weight="length")


class CampusWalkway(RoadNetwork):
    campus: str
    _path_select_cache: dict[
        tuple[FloatCoordinate, FloatCoordinate],
        list[FloatCoordinate],
    ]

    def __init__(self, campus, lines, output_dir) -> None:
        super().__init__(lines)
        self.campus = campus
        self._path_cache_result = f"{output_dir}/{campus}_path_cache_result.pkl"
        try:
            with open(self._path_cache_result, "rb") as cached_result:
                self._path_select_cache = pickle.load(cached_result)  # noqa: S301
        except FileNotFoundError:
            self._path_select_cache = {}

    def cache_path(
        self,
        source: FloatCoordinate,
        target: FloatCoordinate,
        path: list[FloatCoordinate],
    ) -> None:
        # print(f"caching path... current number of cached paths:
        # {len(self._path_select_cache)}")
        self._path_select_cache[(source, target)] = path
        self._path_select_cache[(target, source)] = list(reversed(path))
        with open(self._path_cache_result, "wb") as cached_result:
            pickle.dump(self._path_select_cache, cached_result)

    def get_cached_path(
        self, source: FloatCoordinate, target: FloatCoordinate
    ) -> list[FloatCoordinate] | None:
        return self._path_select_cache.get((source, target), None)
