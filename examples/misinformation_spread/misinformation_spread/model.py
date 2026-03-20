import mesa
from dotenv import load_dotenv
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from misinformation_spread.agents import CitizenAgent, RuleBasedAgent


class MisinformationModel(mesa.Model):
    def __init__(self, width=5, height=5, llm_model="ollama/llama3.2:3b"):
        super().__init__()

        load_dotenv()

        self.llm_model = llm_model
        self.rumor = (
            "The town's water supply has been contaminated with dangerous "
            "chemicals from the nearby factory."
        )

        self.grid = OrthogonalMooreGrid(
            (width, height), capacity=1, torus=True, random=self.random
        )

        agent_configs = [
            {
                "name": "Maria",
                "persona": "A cautious schoolteacher who values evidence and critical thinking. You don't believe things easily.",
                "initial_stance": "skeptic",
                "initial_belief": 0.2,
            },
            {
                "name": "Carlos",
                "persona": "An anxious shopkeeper who worries about health risks. You tend to believe warnings about safety.",
                "initial_stance": "believer",
                "initial_belief": 0.8,
            },
            {
                "name": "Priya",
                "persona": "A young university student studying chemistry. You trust scientific sources over gossip.",
                "initial_stance": "skeptic",
                "initial_belief": 0.15,
            },
            {
                "name": "James",
                "persona": "A retired factory worker who distrusts the factory owners. You've always suspected they cut corners on safety.",
                "initial_stance": "believer",
                "initial_belief": 0.85,
            },
            {
                "name": "Aisha",
                "persona": "A community health worker who has seen real contamination cases before. You take such claims seriously but want proof.",
                "initial_stance": "neutral",
                "initial_belief": 0.5,
            },
            {
                "name": "Tom",
                "persona": "A local journalist always looking for a story. You're curious but need verification before reporting.",
                "initial_stance": "neutral",
                "initial_belief": 0.45,
            },
            {
                "name": "Lin",
                "persona": "A grandmother who has lived here for 50 years. You trust your instincts and community word-of-mouth.",
                "initial_stance": "neutral",
                "initial_belief": 0.55,
            },
            {
                "name": "David",
                "persona": "A government water inspector who knows the water is tested regularly. You're confident the water is safe.",
                "initial_stance": "skeptic",
                "initial_belief": 0.1,
            },
            {
                "name": "Sofia",
                "persona": "A social media enthusiast who shares things quickly. You tend to amplify information without checking.",
                "initial_stance": "believer",
                "initial_belief": 0.75,
            },
            {
                "name": "Raj",
                "persona": "A doctor at the local clinic. You rely on medical data and are skeptical of unverified health claims.",
                "initial_stance": "skeptic",
                "initial_belief": 0.2,
            },
            {
                "name": "Emma",
                "persona": "A stay-at-home parent concerned about children's health. You err on the side of caution.",
                "initial_stance": "neutral",
                "initial_belief": 0.6,
            },
            {
                "name": "Mike",
                "persona": "A laid-back bartender who hears all sorts of gossip. You don't take rumors seriously.",
                "initial_stance": "neutral",
                "initial_belief": 0.4,
            },
        ]

        for config in agent_configs:
            agent = CitizenAgent(
                model=self,
                name=config["name"],
                persona=config["persona"],
                initial_stance=config["initial_stance"],
                initial_belief=config["initial_belief"],
            )
            agent.move_to(self.grid.select_random_empty_cell())

        self.datacollector = DataCollector(
            model_reporters={
                "believers": lambda m: sum(
                    1 for a in m.agents if a.stance == "believer"
                ),
                "skeptics": lambda m: sum(1 for a in m.agents if a.stance == "skeptic"),
                "neutrals": lambda m: sum(1 for a in m.agents if a.stance == "neutral"),
                "avg_belief": lambda m: sum(a.belief_score for a in m.agents)
                / len(m.agents),
            },
            agent_reporters={
                "belief_score": "belief_score",
                "stance": "stance",
            },
        )

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


class RuleBasedModel(mesa.Model):
    def __init__(self, width=5, height=5):
        super().__init__()

        self.grid = OrthogonalMooreGrid(
            (width, height), capacity=1, torus=True, random=self.random
        )

        agent_configs = [
            {
                "name": "Maria",
                "persona": "A cautious schoolteacher who values evidence and critical thinking.",
                "initial_stance": "skeptic",
                "initial_belief": 0.2,
            },
            {
                "name": "Carlos",
                "persona": "An anxious shopkeeper who worries about health risks.",
                "initial_stance": "believer",
                "initial_belief": 0.8,
            },
            {
                "name": "Priya",
                "persona": "A young university student studying chemistry.",
                "initial_stance": "skeptic",
                "initial_belief": 0.15,
            },
            {
                "name": "James",
                "persona": "A retired factory worker who distrusts the factory owners.",
                "initial_stance": "believer",
                "initial_belief": 0.85,
            },
            {
                "name": "Aisha",
                "persona": "A community health worker.",
                "initial_stance": "neutral",
                "initial_belief": 0.5,
            },
            {
                "name": "Tom",
                "persona": "A local journalist always looking for a story.",
                "initial_stance": "neutral",
                "initial_belief": 0.45,
            },
            {
                "name": "Lin",
                "persona": "A grandmother who has lived here for 50 years.",
                "initial_stance": "neutral",
                "initial_belief": 0.55,
            },
            {
                "name": "David",
                "persona": "A government water inspector.",
                "initial_stance": "skeptic",
                "initial_belief": 0.1,
            },
            {
                "name": "Sofia",
                "persona": "A social media enthusiast who shares things quickly.",
                "initial_stance": "believer",
                "initial_belief": 0.75,
            },
            {
                "name": "Raj",
                "persona": "A doctor at the local clinic.",
                "initial_stance": "skeptic",
                "initial_belief": 0.2,
            },
            {
                "name": "Emma",
                "persona": "A stay-at-home parent concerned about children's health.",
                "initial_stance": "neutral",
                "initial_belief": 0.6,
            },
            {
                "name": "Mike",
                "persona": "A laid-back bartender who hears all sorts of gossip.",
                "initial_stance": "neutral",
                "initial_belief": 0.4,
            },
        ]

        for config in agent_configs:
            agent = RuleBasedAgent(
                model=self,
                name=config["name"],
                persona=config["persona"],
                initial_stance=config["initial_stance"],
                initial_belief=config["initial_belief"],
            )
            agent.move_to(self.grid.select_random_empty_cell())

        self.datacollector = DataCollector(
            model_reporters={
                "believers": lambda m: sum(
                    1 for a in m.agents if a.stance == "believer"
                ),
                "skeptics": lambda m: sum(1 for a in m.agents if a.stance == "skeptic"),
                "neutrals": lambda m: sum(1 for a in m.agents if a.stance == "neutral"),
                "avg_belief": lambda m: sum(a.belief_score for a in m.agents)
                / len(m.agents),
            },
            agent_reporters={
                "belief_score": "belief_score",
                "stance": "stance",
            },
        )

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
