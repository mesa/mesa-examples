"""Forest fire with global wind """

import mesa
import math

from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from .agent import Tree

class ForestFire(mesa.Model):
    """
    Wind-driven Forest Fire Model
    """

    def __init__(
        self,
        width=100,
        height=100,
        p_spread=0.25,
        wind_dir=0.0,          # degrees
        wind_strength=0.8,     
        seed=None,
        ignite_pos=None,
    ):
        super().__init__(seed=seed)

        self.step_count = 0
        self.width = width
        self.height = height
        self.p_spread = p_spread
        self.wind_dir = wind_dir
        self.wind_strength = wind_strength

        # Initialize Grid
        self.grid = MultiGrid(width, height, torus=False)

        # Place trees
        for x in range(width):
            for y in range(height):
                    tree = Tree(self, condition="Fine")
                    self.grid.place_agent(tree, (x, y))


        # Ignite Logic
        if ignite_pos:
            for pos in ignite_pos:
                self.ignite(pos)
        else:
            self.ignite()

        self.step_count = 0

        # store ignition reference in grid coords (float is ok)
        if ignite_pos:
            ix = sum(p[0] for p in ignite_pos) / len(ignite_pos)
            iy = sum(p[1] for p in ignite_pos) / len(ignite_pos)
            self.ignite_ref = (ix, iy)
        else:
            # if random ignition, fall back to grid center
            self.ignite_ref = (self.width / 2, self.height / 2)


        # Data collector
        self.datacollector = DataCollector(
            {
                "Fine": lambda m: self.count_type(m, "Fine"),
                "On Fire": lambda m: self.count_type(m, "On Fire"),
                "Burned Out": lambda m: self.count_type(m, "Burned Out"),
                "HeadDist Wind": lambda m: ForestFire.get_head_distance_wind(m),
                "FlankHalfwidth Cross": lambda m: ForestFire.get_flank_halfwidth_crosswind(m),
                "Rate of spread at the fire head": lambda m: ForestFire.get_head_distance_wind(m) / max(1, m.step_count),
                "Rate of spread at the fire Flank": lambda m: ForestFire.get_flank_halfwidth_crosswind(m) / max(1, m.step_count),

            }
        )

        self.datacollector.collect(self)

    def ignite(self, pos=None):
            """Ignite a specific tree or a random one."""
            if pos is None:
                # Random ignition
                trees = [a for a in self.agents if a.condition == "Fine"]
                if trees:
                    self.random.choice(trees).condition = "On Fire"
            else:
                if not self.grid.out_of_bounds(pos):
                    cell_agents = self.grid.get_cell_list_contents([pos])
                    for a in cell_agents:
                        if  a.condition == "Fine":
                            a.condition = "On Fire"
                            return

    
    def wind_unit_vector(self):
        """
        Convert meteorological wind direction to unit vector.
        0° = From North (Vector: 0, -1)
        """
        rad = math.radians(self.wind_dir)
        # Wind comes FROM rad, blows TOWARD opposite
        # Grid (0,0) is bottom-left. 
        wx = -math.sin(rad)
        wy = -math.cos(rad)
        return (wx, wy)

    def wind_biased_probability(self, dx, dy):
        """Compute probability modifier based on alignment"""
        wx, wy = self.wind_unit_vector()

        norm = (dx**2 + dy**2) ** 0.5
        if norm == 0: return 1.0
        
        dxu, dyu = dx / norm, dy / norm
        align = dxu * wx + dyu * wy 
        
        # Simple linear bias: 1 + strength * alignment
        return max(0.0, 1.0 + (self.wind_strength * align))


    def step(self):
        self.step_count += 1
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


    @staticmethod
    def count_type(model, tree_condition):
        """Helper to count trees in a given condition in a fast way."""
        count = 0
        for tree in model.agents:
            if tree.condition == tree_condition:
                count += 1
        return count

    @staticmethod
    def _burnt_positions(model):
        return [
            a.pos for a in model.agents
            if a.__class__.__name__ == "Tree" and a.condition in ["On Fire", "Burned Out"]
        ]

    @staticmethod
    def get_head_distance_wind(model):
        """Downwind head distance relative to ignition reference."""
        pts = ForestFire._burnt_positions(model)
        if not pts:
            return 0.0

        wx, wy = model.wind_unit_vector()  # toward-wind unit vector

        # ignition reference projection
        ix, iy = model.ignite_ref
        proj_ignite = ix * wx + iy * wy

        # head projection among burnt cells
        proj_head = max(x * wx + y * wy for (x, y) in pts)
        return float(proj_head - proj_ignite)

    @staticmethod
    def get_flank_halfwidth_crosswind(model):
        """Crosswind half-width (max absolute deviation) relative to ignition reference."""
        pts = ForestFire._burnt_positions(model)
        if not pts:
            return 0.0

        wx, wy = model.wind_unit_vector()
        px, py = (-wy, wx)  # crosswind axis

        ix, iy = model.ignite_ref
        proj_ignite_c = ix * px + iy * py

        dev = [abs(x * px + y * py - proj_ignite_c) for (x, y) in pts]
        return float(max(dev))


    







