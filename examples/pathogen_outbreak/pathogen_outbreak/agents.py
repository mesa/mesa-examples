from mesa.discrete_space import CellAgent


class Citizen(CellAgent):
    def __init__(self, model):
        super().__init__(model)

        self.state = "healthy"
        self.stage = 0
        self.compliant = self.random.random() < self.model.compliance_rate

    def step(self):
        if self.model.quarantine_status and self.compliant:
            self.quarantine()
        else:
            self.move()

        if self.state == "infected":
            self.stage += 1
            if self.stage > 9:
                chance_of_death = self.random.random()

                if chance_of_death < 0.1:
                    self.state = "dead"
                    # self.remove()

                else:
                    self.state = "immune"

        if self.state == "healthy":
            neighbors = [
                a for cell in self.cell.connections.values() for a in cell.agents
            ]
            for i in neighbors:
                if i.state == "infected":
                    if self.random.random() > 0.40:
                        self.state = "infected"
                    break

    def quarantine(self):
        if self.state != "dead":
            if self.state == "infected":
                return
            else:
                infected_pos = []
                for i in self.model.agents:
                    if i.state == "infected":
                        infected_pos.append(i.cell.coordinate)

                possible_ops = self.cell.connections.values()
                emptys = []
                for i in possible_ops:
                    if i.is_empty:
                        emptys.append(i)

                if len(emptys) > 0:
                    best_cell = max(
                        emptys,
                        key=lambda cell: min(
                            abs(cell.coordinate[0] - i[0])
                            + abs(cell.coordinate[1] - i[1])
                            for i in infected_pos
                        ),
                    )
                    self.move_to(best_cell)

    def move(self):
        if self.state != "dead":
            possible_ops = self.cell.connections.values()
            emptys = []
            for i in possible_ops:
                if i.is_empty:
                    emptys.append(i)
            if len(emptys) > 0:
                self.move_to(self.random.choice(emptys))
