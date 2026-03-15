from dotenv import load_dotenv
from llm_prisoners_dilemma.model import PrisonersDilemmaModel
from mesa.visualization import SolaraViz, make_plot_component

load_dotenv()


def agent_portrayal(agent):
    """Color agents by their last action and score."""
    if not hasattr(agent, "last_action"):
        return {"color": "gray", "size": 40}

    color_map = {
        "cooperate": "#2ecc71",  # Green
        "defect": "#e74c3c",  # Red
        "none": "#95a5a6",  # Gray (first round)
    }
    color = color_map.get(agent.last_action, "gray")

    # Size reflects score — higher score = bigger circle
    size = 30 + min(agent.score * 2, 80)

    return {"color": color, "size": size}


model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 6,
        "label": "Number of Agents",
        "min": 2,
        "max": 20,
        "step": 2,
    },
    "llm_model": {
        "type": "Select",
        "value": "gemini/gemini-2.0-flash",
        "label": "LLM Model",
        "values": [
            "gemini/gemini-2.0-flash",
            "gpt-4o-mini",
            "gpt-4o",
        ],
    },
}

CoopPlot = make_plot_component(
    {
        "cooperation_rate": "#2ecc71",
    }
)

ScorePlot = make_plot_component(
    {
        "total_cooperations": "#2ecc71",
        "total_defections": "#e74c3c",
    }
)
model = PrisonersDilemmaModel()

page = SolaraViz(
    model,
    components=[CoopPlot, ScorePlot],
    model_params=model_params,
    name="LLM Prisoner's Dilemma",
)
