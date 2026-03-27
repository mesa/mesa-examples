"""Agent class for the segregation model."""
import mesa
import numpy as np
class SimpleAgent(mesa.Agent):
    """Agent that moves around randomly. Has a type (A or B) which is used to calculate segregation."""
    def __init__(self,unique_id,model):
        super().__init__(unique_id,model)
        self.type=np.random.choice(["A","B"])
    def step(self):
        """Move to a random neighboring cell."""
        dx=self.random.randint(-1,2)
        dy=self.random.randint(-1,2)
        new_x=self.pos[0]+dx
        new_y=self.pos[1]+dy
        new_x=max(0,min(self.model.grid.width-1,new_x))
        new_y=max(0,min(self.model.grid.height-1,new_y))
        self.model.grid.move_agent(self,(new_x,new_y))