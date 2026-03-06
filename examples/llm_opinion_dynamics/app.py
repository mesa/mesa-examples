import matplotlib.pyplot as plt
import solara
from llm_opinion_dynamics.model import LLMOpinionDynamicsModel
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter

model_params = {
    "n_agents": {
        "type": "SliderInt",
        "value": 9,
        "label": "Number of agents",
        "min": 4,
        "max": 20,
        "step": 1,
    },
    "width": {
        "type": "SliderInt",
        "value": 5,
        "label": "Grid width",
        "min": 3,
        "max": 10,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 5,
        "label": "Grid height",
        "min": 3,
        "max": 10,
        "step": 1,
    },
    "topic": {
        "type": "InputText",
        "value": "Should artificial intelligence be regulated by governments?",
        "label": "Debate topic",
    },
}


def OpinionTrajectoriesPlot(model):
    """Plot opinion trajectories for all agents over time."""
    update_counter.get()

    df = model.datacollector.get_agent_vars_dataframe()

    if df.empty:
        fig, ax = plt.subplots()
        ax.set_title("No data yet — run the model")
        return solara.FigureMatplotlib(fig)

    opinions = df["opinion"].unstack("AgentID")

    fig, ax = plt.subplots(figsize=(7, 5))
    for agent_id in opinions.columns:
        ax.plot(opinions.index, opinions[agent_id], linewidth=1.5, alpha=0.8)

    ax.set_xlabel("Time step")
    ax.set_ylabel("Opinion (0=against, 10=for)")
    ax.set_title(f"Opinion Trajectories\nTopic: {model.topic[:60]}...")
    ax.set_ylim(-0.5, 10.5)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    return solara.FigureMatplotlib(fig)


MeanOpinionPlot = make_plot_component("mean_opinion")
VariancePlot = make_plot_component("opinion_variance")

model = LLMOpinionDynamicsModel()

page = SolaraViz(
    model,
    components=[
        OpinionTrajectoriesPlot,
        MeanOpinionPlot,
        VariancePlot,
    ],
    model_params=model_params,
    name="LLM Opinion Dynamics",
)
