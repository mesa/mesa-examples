import mesa
import numpy as np

class UltimatumAgent(mesa.Agent):
    def __init__(self, model, unique_id):
        super().__init__(model)
        self.wealth = 0.0
        self.offer_memory = np.zeros(len(model.offers))
        self.offer_chosen = 0
        self.thresh_memory = np.zeros(len(model.thresholds))
        self.thresh_chosen = 0
        