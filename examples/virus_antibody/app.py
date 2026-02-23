import weakref

from matplotlib.markers import MarkerStyle
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_plot_component,
    make_space_component,
)
from virus_antibody.agents import AntibodyAgent, VirusAgent
from virus_antibody.model import VirusAntibodyModel

# Style and portrayals
MARKER_CACHE = {}
MARKER_CACHE["antibody"] = MarkerStyle("o")
MARKER_CACHE["virus"] = MarkerStyle("*")


def agent_portrayal(agent):
    """Portray an agent for visualization."""
    portrayal = {}

    if isinstance(agent, AntibodyAgent):
        portrayal["marker"] = MARKER_CACHE["antibody"]
        portrayal["size"] = 30

        if isinstance(agent.target, weakref.ReferenceType):
            target_obj = agent.target()  # dereference the weakref
        else:
            target_obj = agent.target

        if target_obj == agent:
            # gray if ko
            portrayal["color"] = "gray"
            portrayal["layer"] = 2

        elif target_obj is None:
            # Blue if moving
            portrayal["color"] = "blue"
            portrayal["layer"] = 1

        else:
            # Purple if aiming for virus
            portrayal["color"] = "purple"
            portrayal["layer"] = 1

    elif isinstance(agent, VirusAgent):
        portrayal["marker"] = MARKER_CACHE["virus"]
        portrayal["size"] = 50
        portrayal["color"] = "red"
        portrayal["filled"] = True
        portrayal["layer"] = 0

    return portrayal


# Setup model parameters for the visualization interface
model = VirusAntibodyModel()

model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "initial_antibody": Slider(
        label="Number of antibodies",
        value=20,
        min=1,
        max=50,
        step=1,
    ),
    "antibody_duplication_rate": Slider(
        label="Rate of duplication for antibodies",
        value=0.01,
        min=0,
        max=0.05,
        step=0.001,
    ),
    "initial_viruses": Slider(
        label="Number of viruses",
        value=20,
        min=1,
        max=50,
        step=1,
    ),
    "virus_duplication_rate": Slider(
        label="Rate of duplication for viruses",
        value=0.01,
        min=0,
        max=0.05,
        step=0.001,
    ),
    "virus_mutation_rate": Slider(
        label="Rate of mutation for viruses",
        value=0.05,
        min=0,
        max=0.3,
        step=0.01,
    ),
}


# Visualization and plots


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


agents_lineplot_component = make_plot_component(
    {"Antibodies": "tab:blue", "Viruses": "tab:red"},
    post_process=post_process_lines,
)

agent_portrayal_component = make_space_component(
    agent_portrayal=agent_portrayal, backend="matplotlib"
)

page = SolaraViz(
    model,
    components=[
        agent_portrayal_component,
        agents_lineplot_component,
    ],
    model_params=model_params,
    name="Virus/Antibody",
)

page  # noqa
