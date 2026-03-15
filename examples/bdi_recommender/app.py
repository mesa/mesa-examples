"""

Displays:
- Grid with Bob (red) and Doctor (cyan)
- Current beliefs, desires, goals panel
- lime green for gym
- orange for nutrition center
- blue for clinic
"""

import solara
from agents import (
    ClinicAgent,
    DoctorAgent,
    GymAgent,
    NutritionCentreAgent,
    UserAgent,
)
from mesa.visualization import SolaraViz, SpaceRenderer
from mesa.visualization.components import AgentPortrayalStyle
from model import BDIRecommenderModel


def agent_portrayal(agent):
    """Define how agents are displayed on the grid."""
    if isinstance(agent, UserAgent):
        return AgentPortrayalStyle(
            color="red",
            size=100,
            marker="o",
            zorder=3,  # Bob appears on top
        )
    elif isinstance(agent, DoctorAgent):
        return AgentPortrayalStyle(
            color="cyan",
            size=120,
            marker="s",
            zorder=2,  # Doctor below Bob
        )
    elif isinstance(agent, GymAgent):
        return AgentPortrayalStyle(
            color="limegreen",
            size=150,
            marker="s",
            zorder=1,  # Locations at bottom
        )
    elif isinstance(agent, NutritionCentreAgent):
        return AgentPortrayalStyle(
            color="orange",
            size=150,
            marker="s",
            zorder=1,
        )
    elif isinstance(agent, ClinicAgent):
        return AgentPortrayalStyle(
            color="dodgerblue",
            size=150,
            marker="s",
            zorder=1,
        )
    return AgentPortrayalStyle()


def get_bdi_summary(model):
    """Display Bob's BDI state summary."""
    user = model.user
    goals = ", ".join(user.goals.keys()) if user.goals else "None"
    beliefs = ", ".join(f"{k}={v:.1f}" for k, v in user.beliefs.items())
    desires = ", ".join(f"{k}={v:.1f}" for k, v in user.desires.items())
    intentions = ", ".join(i[0] for i in user.intentions) if user.intentions else "None"
    dest_idx = user.current_destination_index
    total_dest = len(user.destinations)

    return solara.Markdown(f"""
**Time:** {model.time}<br>
**Beliefs:** {beliefs}<br>
**Desires:** {desires}<br>
**Goals:** {goals}<br>
**Intentions:** {intentions}<br>
**Progress:** {dest_idx}/{total_dest} destinations
""")


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "user_desire_pa": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "User Desire: PA (Physical Activity)",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    "user_desire_wr": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "User Desire: WR (Weight Reduction)",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    "doctor_proposal_tick": {
        "type": "SliderInt",
        "value": 3,
        "label": "Doctor Proposal Tick",
        "min": 1,
        "max": 40,
        "step": 1,
    },
}

model = BDIRecommenderModel(rng=42)

renderer = SpaceRenderer(model, backend="matplotlib").setup_agents(agent_portrayal)
renderer.draw_agents()

page = SolaraViz(
    model,
    renderer,
    components=[get_bdi_summary],
    model_params=model_params,
    name="BDI Recommender Agent",
)
page  # noqa
