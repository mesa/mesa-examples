import app
import model

m = model.GameOfLifeModel()
# get the component function
space_func = app.layer_viz
try:
    c = space_func(m)
    print("Success")
except Exception:
    import traceback

    traceback.print_exc()
