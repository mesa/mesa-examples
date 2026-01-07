from mesa.examples.advanced.wolf_sheep.agents import GrassPatch, Sheep, Wolf

from .utility import move


class SheepRL(Sheep):
    def step(self):
        """The code is exactly same as mesa-example with the only difference being the move function and new sheep creation class.
        Link : https://github.com/mesa/mesa-examples/blob/main/examples/wolf_sheep/wolf_sheep/agents.py
        """
        action = self.model.action_dict[self.unique_id]
        move(self, action)

        living = True

        if self.model.grass:
            # Reduce energy
            self.energy -= 1

            # If there is grass available, eat it
            this_cell = self.model.grid.get_cell_list_contents([self.pos])
            grass_patch = next(obj for obj in this_cell if isinstance(obj, GrassPatch))
            if grass_patch.fully_grown:
                self.energy += self.model.sheep_gain_from_food
                grass_patch.fully_grown = False

            # Death
            if self.energy < 0:
                self.model.grid.remove_agent(self)
                self.model.remove(self)
                living = False

        if living and self.random.random() < self.model.sheep_reproduce:
            # Create a new sheep:
            if self.model.grass:
                self.energy /= 2
            unique_id_str = f"sheep_{self.model.next_id()}"
            lamb = SheepRL(unique_id_str, self.pos, self.model, self.moore, self.energy)
            self.model.grid.place_agent(lamb, self.pos)
            self.model.add(lamb)


class WolfRL(Wolf):
    def step(self):
        """The code is exactly same as mesa-example with the only difference being the move function and new wolf creation class.
        Link : https://github.com/mesa/mesa-examples/blob/main/examples/wolf_sheep/wolf_sheep/agents.py
        """
        action = self.model.action_dict[self.unique_id]
        move(self, action)

        self.energy -= 1

        # If there are sheep present, eat one
        x, y = self.pos
        this_cell = self.model.grid.get_cell_list_contents([self.pos])
        sheep = [obj for obj in this_cell if isinstance(obj, Sheep)]
        if len(sheep) > 0:
            sheep_to_eat = self.random.choice(sheep)
            self.energy += self.model.wolf_gain_from_food

            # Kill the sheep
            self.model.grid.remove_agent(sheep_to_eat)
            self.model.remove(sheep_to_eat)

        # Death or reproduction
        if self.energy < 0:
            self.model.grid.remove_agent(self)
            self.model.remove(self)
        else:
            if self.random.random() < self.model.wolf_reproduce:
                # Create a new wolf cub
                self.energy /= 2
                unique_id_str = f"wolf_{self.model.next_id()}"
                cub = WolfRL(
                    unique_id_str, self.pos, self.model, self.moore, self.energy
                )
                self.model.grid.place_agent(cub, cub.pos)
                self.model.add(cub)
