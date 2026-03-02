import math
from mesa.experimental.continuous_space import ContinuousSpaceAgent


# Simple scheduler that randomly activates agents in each step, without modifying the original list of agents.
class SimpleRandomActivation:
    def __init__(self, model):
        self.model = model
        self.agents = []

    def add(self, agent):
        self.agents.append(agent)

    def remove(self, agent):
        """Remove an agent from the schedule."""
        if agent in self.agents:
            self.agents.remove(agent)

    def step(self):
        # random activation order without modifying original list
        order = list(self.agents)
        self.model.random.shuffle(order)
        for a in order:
            a.step()


class Prey(ContinuousSpaceAgent):

    "a prey create which hase very random motion the a continous space"
    def __init__(self, unique_id, space, model, pos, speed=1.0):
        # ContinuousSpaceAgent requires (space, model)
        super().__init__(space, model)
        # assign the unique identifier and starting position
        self.unique_id = unique_id
        self.position = pos
        self.speed = speed
    #now we need make it motion randomso we need move agent to random position based it's spee
    def random_move(self):
        #random angle between 0 and 2pi would taken 
        angle=self.random.uniform(0,2*math.pi)
        #change in x and y by trigonometry
        dx=math.cos(angle)*self.speed
        dy=math.sin(angle)*self.speed
        #NEW POSITION  calculated
        new_x=self.pos[0]+dx
        new_y=self.pos[1]+dy

        new_pos=(new_x,new_y)
        
        # to make sure it doesn't go off the map; use the new helper
        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)

        # update the stored position
        self.position = new_pos

    def step(self):
        #it calls the random move function to move the agent in each step of the simulation
        self.random_move()
        if self.random.random() < self.model.prey_reproduce:
            # create new prey at the exact same position
            new_prey = Prey(self.model.next_id(), self.model.space, self.model, self.position, self.speed)
            self.model.schedule.add(new_prey)

class Predator(ContinuousSpaceAgent):
    "a predator agent which move move randomly but also try to catch the prey if it is nearby"

    def __init__(self, unique_id, space, model, pos, speed=1.5, energy=0): #it need faster than prey to catch it
        super().__init__(space, model)
        self.unique_id = unique_id
        self.position = pos
        self.speed = speed
        self.energy = energy # energy level of the predator
    
    def random_move(self):
        #here we make it hunt the prey if it is nearby
        #we will same random walk logic used in prey agent
        angle=self.random.uniform(0,2*math.pi)
        dx=math.cos(angle)*self.speed
        dy=math.sin(angle)*self.speed

        new_pos=(self.pos[0]+dx,self.pos[1]+dy)
        if self.model.space.torus:
            new_pos = self.model.space.torus_correct(new_pos)
        self.position = new_pos
    
    def step(self):
        self.random_move()
        self.energy -= 1 #predator lose energy each step

        neighbors, distances=self.get_neighbors_in_radius(radius=2.0)#it get the nearby agents within a certain radius, it returns two lists: one with the neighboring agents and another with their corresponding distances from the predator
        prey_neighbors=[obj for obj in neighbors if isinstance(obj,Prey)] #it filter the nearby agents to find the prey


        if prey_neighbors:
            prey_to_eat = self.random.choice(prey_neighbors)  # randomly select one nearby prey to eat
            self.energy += self.model.predator_gain_from_food  # gain energy from eating the prey

            # Prefer the agent-level remove() which handles model and space cleanup.
            try:
                prey_to_eat.remove()
            except Exception:
                # Fallbacks: remove from space and schedule if available
                if hasattr(self.model.space, "_remove_agent"):
                    try:
                        self.model.space._remove_agent(prey_to_eat)
                    except Exception:
                        pass
                if hasattr(self.model.schedule, "remove"):
                    try:
                        self.model.schedule.remove(prey_to_eat)
                    except Exception:
                        pass
                else:
                    if hasattr(self.model.schedule, "agents") and prey_to_eat in self.model.schedule.agents:
                        try:
                            self.model.schedule.agents.remove(prey_to_eat)
                        except Exception:
                            pass
        if self.energy <= 0:
            # remove from scheduler and model/space
            if hasattr(self.model.schedule, "remove"):
                self.model.schedule.remove(self)
            if self in getattr(self.model.schedule, "agents", []):
                try:
                    self.model.schedule.agents.remove(self)
                except Exception:
                    pass
            try:
                self.remove()
            except Exception:
                pass
            return

        if self.random.random() < self.model.predator_reproduce:
            self.energy /= 2  # reproduction costs energy
            new_predator = Predator(self.model.next_id(), self.model.space, self.model, self.position, self.speed, int(self.energy))  # new predator starts with half parent's energy
            self.model.schedule.add(new_predator)
