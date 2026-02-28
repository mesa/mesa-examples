from mesa import Agent

class CarAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        
    def move(self):
        x,y = self.pos
        new_pos = ((x + 1) % self.model.grid.width, y)
        if self.model.grid.is_cell_empty(new_pos):
            self.model.grid.move_agent(self, new_pos)

    def step(self):
        self.move()
        
