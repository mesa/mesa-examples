import importlib
import os
import sys
import time

import pytest
from mesa.visualization import SolaraViz


def get_viz_files(directory):
    viz_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file in ["app.py", "viz.py"]:
                module_name = os.path.relpath(os.path.join(root, file[:-3])).replace(
                    os.sep, "."
                )
                viz_files.append(module_name)
    return viz_files


@pytest.mark.parametrize("module_name", get_viz_files("examples"))
def test_solara_viz(module_name):
    # Add the 'examples' directory to the Python path
    examples_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "examples")
    )
    sys.path.insert(0, examples_dir)

    # Add the parent directory of the module to the Python path
    module_parent_dir = os.path.abspath(
        os.path.join(examples_dir, os.path.dirname(module_name.replace(".", os.sep)))
    )
    if module_parent_dir not in sys.path:
        sys.path.insert(0, module_parent_dir)

    # Import the visualization module
    module = importlib.import_module(module_name)

    # Find the SolaraViz instance
    solara_viz = None
    for item_name in dir(module):
        item = getattr(module, item_name)
        if isinstance(item, SolaraViz):
            solara_viz = item
            break

    assert solara_viz is not None, f"No SolaraViz instance found in {module_name}"

    # Get the model instance
    model = solara_viz.model

    # Store the initial state
    initial_step = model.steps

    # Do 3 steps
    for _ in range(3):
        model.step()
    assert model.steps == initial_step + 3

    # Pause (no actual pause needed in this context)

    # 3 more steps
    for _ in range(3):
        model.step()
    assert model.steps == initial_step + 6

    # Reset
    model_params = solara_viz.model_params
    new_model = model.__class__(**model_params)
    solara_viz.model = new_model
    model = new_model

    assert model.steps == 0 or model.steps == initial_step

    # Run steps for 5 seconds
    start_time = time.time()
    while time.time() - start_time < 5:
        model.step()

    # Pause (no actual pause needed in this context)

    # Check if the step counter has increased
    assert model.steps > 0, "Model did not advance steps"

    print(f"Test completed for {module_name}. Final step count: {model.steps}")

    # Remove the added directories from the Python path
    sys.path.pop(0)
    if module_parent_dir in sys.path:
        sys.path.remove(module_parent_dir)


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
