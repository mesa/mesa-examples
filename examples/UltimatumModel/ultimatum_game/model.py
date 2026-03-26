import mesa
import numpy as np
from ultimatum_game.agents import UltimatumAgent

class UltimatumModel(mesa.Model):
    def __init__(self, n, stake = 100):
        super().__init__()
        self.num_agents = n
        self.stake = stake
        self.grid = mesa.space.MultiGrid(10, 10, torus=True)
        self.offers = list(range(0, self.stake))
        self.thresholds = list(range(0, self.stake))
        self.learning_rate = 0.2
        self.decay_rate = 0.95
        # Data collection
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Accept Rate": "current_accept_rate",
                "Avg Offer": "current_avg_offer", 
                "Proposer Avg": "current_proposer_avg",
                "Responder Avg": "current_responder_avg"
            }
        )
        self.current_accept_rate = 0
        self.current_avg_offer = 0
        self.current_proposer_avg = 0
        self.current_responder_avg = 0

        # Create Agents
        for i in range(self.num_agents):
            agent = UltimatumAgent(self, i)
            # Random position
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
        agents = [a for a in self.agents]
        np.random.shuffle(agents)
        pairs = [(agents[i], agents[i+1]) for i in range(0, len(agents), 2)]
        
        # Stats trackers
        offers_made = []
        accept_count = 0
        total_proposer_pay = 0
        total_responder_pay = 0
        
        # Game Settings
        for first_agent, second_agent in pairs:
            if np.random.random() < 0.5:
                proposer, responder = first_agent, second_agent
            else:
                proposer, responder = second_agent, first_agent
                
            proposer_offer = proposer.offer_chosen if np.sum(proposer.offer_memory) > 0 else np.random.randint(0, len(proposer.offer_memory))
            if np.sum(proposer.offer_memory) > 0:
                exp_mem = np.exp(proposer.offer_memory / 5.0)
                probs = exp_mem / exp_mem.sum()
                proposer_offer = np.random.choice(len(proposer.offer_memory), p=probs)
            offer = self.offers[proposer_offer]
            proposer.offer_chosen = proposer_offer
            
            responder_thresh = responder.thresh_chosen if np.sum(responder.thresh_memory) > 0 else np.random.randint(0, len(responder.thresh_memory))
            if np.sum(responder.thresh_memory) > 0:
                exp_mem = np.exp(responder.thresh_memory / 5.0)
                probs = exp_mem / exp_mem.sum()
                responder_thresh = np.random.choice(len(responder.thresh_memory), p=probs)
            threshold = self.thresholds[responder_thresh]
            responder.thresh_chosen = responder_thresh
            
            # Play the game
            if offer >= threshold:
                p_pay = self.stake - offer
                r_pay = offer
                accept_count += 1
            else:
                p_pay = 0
                r_pay = 0
            
            # Learn
            proposer.offer_memory[proposer_offer] += self.learning_rate * p_pay
            responder.thresh_memory[responder_thresh] += self.learning_rate * r_pay
            
            # Decay memories
            proposer.offer_memory *= self.decay_rate
            responder.thresh_memory *= self.decay_rate
        
            # Update wealth
            proposer.wealth += p_pay
            responder.wealth += r_pay
            
            # Stats
            offers_made.append(offer)
            total_proposer_pay += p_pay
            total_responder_pay += r_pay
            
            # Model stats
        self.current_accept_rate = (accept_count / len(pairs)) * 100
        self.current_avg_offer = np.mean(offers_made)
        self.current_proposer_avg = total_proposer_pay / len(pairs)
        self.current_responder_avg = total_responder_pay / len(pairs)
        
        self.datacollector.collect(self)