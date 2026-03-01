from mesa.visualization import SolaraViz, make_plot_component

# Use relative import consistent with model.py
from .model import HierarchicalOrganizationModel


model_params = {
    "num_departments": {
        "type": "SliderInt",
        "value": 3,
        "min": 1,
        "max": 8,
        "step": 1,
        "label": "Number of Departments",
    },
    "employees_per_department": {
        "type": "SliderInt",
        "value": 5,
        "min": 1,
        "max": 15,
        "step": 1,
        "label": "Employees per Department",
    },
    "shock_probability": {
        "type": "SliderFloat",
        "value": 0.05,
        "min": 0.0,
        "max": 0.5,
        "step": 0.01,
        "label": "Shock Probability",
    },
}

# NOTE: SolaraViz instantiates the model itself using model_params.
# Do NOT instantiate the model here manually — pass the class instead.
model = HierarchicalOrganizationModel()

main_plot = make_plot_component(
    ["Total Output", "Avg Department Performance"]
)

shock_plot = make_plot_component(["Shock Event"])

page = SolaraViz(
    model,
    components=[main_plot, shock_plot],
    model_params=model_params,
    name="Hierarchical Organization Model",
)