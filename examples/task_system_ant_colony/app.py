import mesa.visualization as mv
from model import AntColonyModel

TASK_COLORS = {
    "Dig Soil":           "#1D9E75",
    "Transport Material": "#3B8BD4",
    "Respond to Signal":  "#E24B4A",
    "Rest":               "#888780",
    "Idle":               "#D3D1C7",
}

def agent_portrayal(agent):
    return {
        "color": TASK_COLORS.get(agent.current_task_name, "#ccc"),
        "size":  8 + agent.current_task_progress * 8,
        "shape": "circle",
    }

model_params = {
    "n_ants":        {"type": "SliderInt",   "label": "Number of ants",           "value": 20,   "min": 5,   "max": 60,  "step": 5},
    "signal_radius": {"type": "SliderInt",   "label": "Pheromone signal radius",  "value": 3,    "min": 1,   "max": 8,   "step": 1},
    "signal_prob":   {"type": "SliderFloat", "label": "Cave-in probability/step", "value": 0.05, "min": 0.0, "max": 0.3, "step": 0.01},
    "width":         {"type": "SliderInt",   "label": "Grid width",               "value": 20,   "min": 10,  "max": 40,  "step": 5},
    "height":        {"type": "SliderInt",   "label": "Grid height",              "value": 20,   "min": 10,  "max": 40,  "step": 5},
    "seed":          {"type": "SliderInt",   "label": "Random seed",              "value": 42,   "min": 0,   "max": 999, "step": 1},
}

# Pass an instance, not the class -- fixes the NoneType/_time bug in Mesa 3.5.1
model = AntColonyModel()

page = mv.SolaraViz(
    model,
    components=[
        mv.make_space_component(agent_portrayal),
        mv.make_plot_component({
            "Ants Digging":      "#1D9E75",
            "Ants Transporting": "#3B8BD4",
            "Ants Responding":   "#E24B4A",
            "Ants Resting":      "#888780",
        }),
        mv.make_plot_component({"Total Reward": "#7F77DD"}),
        mv.make_plot_component({"Total Interruptions": "#E24B4A"}),
    ],
    model_params=model_params,
    name="Ant Colony -- Task System",
)
