from mesa import Agent

class CarAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        
    def move(self):
        x,y = self.pos
        new_pos = ((x + 1) % self.model.grid.dimensions[0], y)
        if len(self.model.grid._cells[new_pos].agents) == 0:
            # Remove from current cell
            self.model.grid._cells[self.pos].remove_agent(self)
            # Add to new cell
            self.model.grid._cells[new_pos].add_agent(self)
            # Update agent position
            self.pos = new_pos

    def step(self):
        self.move()
        
