from mesa import Agent
import random


class citizen(Agent):

    def __init__(self, model):
        super().__init__(model)

        self.state = "healthy"
        self.stage = 0
        self.compliant = random.random() < self.model.compliance_rate

    def step(self):

        if self.model.quarantine_status and self.compliant:
            self.quarantine()
        else:
            self.move()

        if self.state == "infected":
            self.stage += 1
            if self.stage > 9:
                chance_of_death = random.random()

                if chance_of_death < 0.1:
                    self.state = "dead"
                    # self.remove()

                else:
                    self.state = "immune"

        cell_state = "healthy"

        cell_neigh = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False
        )

        for i in cell_neigh:
            if i.state == "infected":
                cell_state = "infected"

        if self.state == "healthy" and cell_state == "infected":
            chances = random.random()
            if chances > 0.40:
                self.state = "infected"

    def quarantine(self):
        if self.state != "dead":
            if self.state == "infected":
                return
            else:
                infected_pos = []
                for i in self.model.agents:
                    if i.state == "infected":
                        infected_pos.append(i.pos)

                possible_ops = self.model.grid.get_neighborhood(
                    self.pos, moore=False, include_center=False
                )
                emptys = []
                for i in possible_ops:
                    if self.model.grid.is_cell_empty(i):
                        emptys.append(i)

                if len(emptys) > 0:
                    best_cell = max(
                        emptys,
                        key=lambda pos: min(
                            abs(pos[0] - i[0]) + abs(pos[1] - i[1])
                            for i in infected_pos
                        ),
                    )
                    self.model.grid.move_agent(self, best_cell)

    def move(self):
        if self.state != "dead":

            possible_ops = self.model.grid.get_neighborhood(
                self.pos, moore=False, include_center=False
            )
            emptys = []
            for i in possible_ops:
                if self.model.grid.is_cell_empty(i):
                    emptys.append(i)
            if len(emptys) > 0:
                self.model.grid.move_agent(self, self.random.choice(emptys))
