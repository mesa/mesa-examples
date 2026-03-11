import mesa_geo as mg


class Household(mg.GeoAgent):
    """Solar panel adoption agent."""

    def __init__(self, model, geometry, crs, unique_id=None):
        """Create a new Household agent."""
        super().__init__(model, geometry, crs)
        self.unique_id = unique_id if unique_id is not None else self.model.random.randint(1, 100000000)
        self.has_solar = False
        self.solar_radiation = 0.0


    def step(self):
        if self.has_solar:
            return

        neighbors = list(self.model.space.get_neighbors_within_distance(self, distance=500))
        
        solar_neighbors = sum(1 for n in neighbors if getattr(n, 'has_solar', False))
        total_neighbors = len(neighbors)
        social_influence = solar_neighbors / total_neighbors if total_neighbors > 0 else 0.0
        economic_viability = self.solar_radiation
        
        prob_adopt = (self.model.social_weight * social_influence) + (self.model.economic_weight * economic_viability)
        prob_adopt += 0.01

        if self.model.random.random() < prob_adopt:
            self.has_solar = True
            self.model.total_adopted += 1

    def __repr__(self):
        return f"Household {self.unique_id} (Solar: {self.has_solar})"
