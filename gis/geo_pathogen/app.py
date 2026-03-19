from mesa.visualization import SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import dis_Model
from agents import citizen

def citizen_draw(agent):
    if not isinstance(agent, citizen):
        return {"color": "Gray", "fillOpacity": 0.1, "weight": 1}
    
    if agent.state == "healthy":
        return {"color": "Green", "radius": 3}
    elif agent.state == "infected":
        return {"color": "Red", "radius": 3}
    elif agent.state == "immune":
        return {"color": "Blue", "radius": 3}
    elif agent.state == "dead":
        return {"color": "Black", "radius": 3}

model_params = {
    "compliance": {
        "type": "SliderFloat",
        "value": 0.7,
        "label": "Quarantine Compliance Rate",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    "n": {
        "type": "SliderInt",
        "value": 100,
        "label": "Citizens",
        "min": 10,
        "max": 300,
        "step": 10,
    },
    "infn": {
        "type": "SliderInt",
        "value": 5,
        "label": "Infected",
        "min": 1,
        "max": 20,
        "step": 1,
    }
}

model = dis_Model(n=100, infn=5)

renderer = make_geospace_component(citizen_draw)

graph_ot = make_plot_component(["healthy", "infected", "immune", "dead", "quarantine"])

page = SolaraViz(
    model,
    components=[renderer, graph_ot],
    model_params=model_params,
    name="Compliance/Quarantine during Outbreak Model",
)
