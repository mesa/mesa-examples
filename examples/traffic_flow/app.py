from mesa.visualization import SolaraViz, make_space_component
from traffic_flow.model import TraficFlow


def car_portrayal(agent):
    if agent is None or agent.pos is None:
        return
    return {
        "color": "#1f77b4",
        "size": 50,
    }


space_component = make_space_component(
    car_portrayal,
    draw_grid=True,
)

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 20,
        "label": "Width",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 5,
        "label": "Height",
        "min": 2,
        "max": 20,
        "step": 1,
    },
    "n_cars": {
        "type": "SliderInt",
        "value": 20,
        "label": "Number of cars",
        "min": 1,
        "max": 200,
        "step": 1,
    },
    "seed": {
        "type": "InputText",
        "value": 1,
        "label": "Seed",
    },
}

model = TraficFlow(width=20, height=5, n_cars=20, seed=1)

page = SolaraViz(
    model,
    components=[space_component],
    model_params=model_params,
    name="Traffic Flow",
)
page  # noqa
