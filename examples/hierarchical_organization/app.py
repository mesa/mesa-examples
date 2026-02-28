from mesa.visualization import SolaraViz, make_plot_component
from model import HierarchicalOrganizationModel


def model_params():
    return {
        "num_departments": {
            "type": "SliderInt",
            "value": 3,
            "min": 1,
            "max": 8,
            "step": 1,
        },
        "employees_per_department": {
            "type": "SliderInt",
            "value": 5,
            "min": 1,
            "max": 15,
            "step": 1,
        },
        "shock_probability": {
            "type": "SliderFloat",
            "value": 0.05,
            "min": 0.0,
            "max": 0.5,
            "step": 0.01,
        },
    }


model = HierarchicalOrganizationModel()

main_plot = make_plot_component(
    ["Total Output", "Avg Department Performance"]
)

shock_plot = make_plot_component(["Shock Event"])

page = SolaraViz(
    model,
    components=[main_plot, shock_plot],
    model_params=model_params(),
    name="Hierarchical Organization Model",
)