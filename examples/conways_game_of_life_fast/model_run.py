from model import GameOfLifeModel

model = GameOfLifeModel(width=10, height=10, alive_fraction=0.2)
for i in range(10):
    model.step()
