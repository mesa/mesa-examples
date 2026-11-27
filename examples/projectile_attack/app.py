"""
run.py - solara run run.py
"""

from __future__ import annotations

from typing import Any

import solara

try:
    from .agents import ResultText, Shell, Tank, Target, Wall
except ImportError:
    from agents import ResultText, Shell, Tank, Target, Wall
from mesa.visualization import SolaraViz, SpaceRenderer
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle

try:
    from .model import TankGameModel
except ImportError:
    from model import TankGameModel


def agent_portrayal(agent: Any) -> AgentPortrayalStyle:
    if isinstance(agent, Tank):
        return AgentPortrayalStyle(marker="s", size=140, color="tab:green", zorder=5)
    if isinstance(agent, Target):
        return AgentPortrayalStyle(marker="X", size=170, color="tab:red", zorder=6)
    if isinstance(agent, Shell):
        return AgentPortrayalStyle(marker="o", size=60, color="black", zorder=7)
    if isinstance(agent, Wall):
        return AgentPortrayalStyle(marker="s", size=140, color="tab:gray", zorder=1)
    if isinstance(agent, ResultText):
        text = agent.text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        color = "tab:green" if agent.kind == "success" else "tab:red"
        return AgentPortrayalStyle(
            marker=f"$\\text{{{text}}}$",
            size=80000,
            color=color,
            zorder=10,
        )
    return AgentPortrayalStyle(marker="o", size=80, zorder=3)


def propertylayer_portrayal(layer) -> PropertyLayerStyle | None:
    if layer.name == "trajectory":
        return PropertyLayerStyle(
            color="orange",
            alpha=0.7,
            vmin=0,
            vmax=1,
            colorbar=False,
        )
    return None


@solara.component
def GameControls(model: TankGameModel):
    angle, set_angle = solara.use_state(model.angle)
    power, set_power = solara.use_state(model.power)
    target_movable, set_target_movable = solara.use_state(model.target_movable)
    render_tick, set_render_tick = solara.use_state(0)

    def bump_render():
        set_render_tick(render_tick + 1)

    def on_angle_change(value: float) -> None:
        set_angle(value)
        model.angle = 90.0 - value

    def on_power_change(value: float) -> None:
        set_power(value)
        model.power = value

    def on_target_movable_change(value: bool) -> None:
        set_target_movable(value)
        model.target_movable = value

    def fire_with_params() -> None:
        model.angle = 90.0 - angle
        model.power = power
        model.target_movable = target_movable
        model.fire()
        bump_render()

    with solara.Card("Game Controls"):
        solara.SliderFloat(
            "Angle",
            value=angle,
            on_value=on_angle_change,
            min=0.0,
            max=90.0,
            step=1.0,
        )
        solara.SliderFloat(
            "Power",
            value=power,
            on_value=on_power_change,
            min=0.0,
            max=100.0,
            step=1.0,
        )
        solara.Checkbox(
            label="Target movable",
            value=target_movable,
            on_value=on_target_movable_change,
        )
        with solara.Row(gap="12px"):
            solara.Button(
                "Fire",
                on_click=fire_with_params,
                disabled=model.shell_exists
                or model.game_over
                or model.shots_fired >= model.max_shots,
            )
            solara.Button(
                "Reloading",
                on_click=bump_render,
            )
        solara.Text(
            f"The remaining chances you have: {model.shots_fired}/{model.max_shots}"
        )


model_params = {
    "width": 35,
    "height": 35,
}

model = TankGameModel()

renderer = SpaceRenderer(model, backend="matplotlib")
renderer.draw_structure()
if hasattr(renderer, "setup_agents"):
    renderer.setup_agents(agent_portrayal).draw_agents()
else:
    renderer.draw_agents(agent_portrayal)

if hasattr(renderer, "setup_propertylayer"):
    renderer.setup_propertylayer(propertylayer_portrayal).draw_propertylayer()
else:
    renderer.draw_propertylayer(propertylayer_portrayal)

page = SolaraViz(
    model,
    renderer=renderer,
    model_params=model_params,
    components=[(GameControls, 0)],
)
