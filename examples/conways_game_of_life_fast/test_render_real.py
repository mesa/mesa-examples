import app
import model
from mesa.visualization.components.matplotlib_components import SpaceMatplotlib

m = model.GameOfLifeModel()
SpaceMatplotlib(
    m, agent_portrayal=lambda x: {}, propertylayer_portrayal=app.propertylayer_portrayal
)
