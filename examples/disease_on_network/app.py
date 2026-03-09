import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from typing import Dict, Any
from disease_on_network.model import IllnessModel
from disease_on_network.agent import PersonAgent, State


def agent_portrayal(agent: PersonAgent) -> Dict[str, Any]:
    """
    Provide rendering instructions for nodes based on disease state.
    """
    colors = {
        State.SUSCEPTIBLE: "tab:blue",
        State.INFECTED: "tab:red",
        State.RECOVERED: "tab:green",
        State.DEAD: "black",
    }
    return {"color": colors[agent.state], "size": 50, "alpha": 0.8}


# Define the interactive parameters
model_params = {
    "num_nodes": mesa.visualization.Slider(
        label="Number of Agents", value=100, min=10, max=500, step=10
    ),
    "avg_degree": mesa.visualization.Slider(
        label="Avg Connections per Node", value=4, min=1, max=20, step=1
    ),
    "initial_infected": mesa.visualization.Slider(
        label="Initial Cases", value=5, min=1, max=50, step=1
    ),
    "p_transmission": mesa.visualization.Slider(
        label="Infection Probability (p1)", value=0.2, min=0.0, max=1.0, step=0.01
    ),
    "p_recovery": mesa.visualization.Slider(
        label="Recovery Probability (p2)", value=0.1, min=0.0, max=1.0, step=0.01
    ),
    "p_mortality": mesa.visualization.Slider(
        label="Mortality Probability (p4)", value=0.05, min=0.0, max=0.2, step=0.005
    ),
    "link_dynamics": mesa.visualization.Slider(
        label="Link Dynamics (0=Off, 1=On)", value=1, min=0, max=1, step=1
    ),
}

# Create Space Component (Network Movie)
space_component = make_space_component(agent_portrayal)

# Create Plot Component (Disease Curve Chart)
line_chart = make_plot_component(
    {
        "Susceptible": "tab:blue",
        "Infected": "tab:red",
        "Recovered": "tab:green",
        "Dead": "black",
    }
)

initial_model = IllnessModel()


# Instantiate the Page
app = SolaraViz(
    model=initial_model,
    components=[space_component, line_chart],
    model_params=model_params,
    name="Epidemic Network Simulator",
)

#app
