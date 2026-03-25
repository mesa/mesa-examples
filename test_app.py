from examples.forest_fire.app import forest_fire_portrayal
from examples.forest_fire.forest_fire.model import ForestFire

try:
    m = ForestFire()
    for tree in m.grid.all_cells[0].agents:
        p = forest_fire_portrayal(tree)
        print(p)
except Exception:
    import traceback

    traceback.print_exc()
