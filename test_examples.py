import importlib
import os

import pytest
from mesa import Model


def get_models(directory):
    models = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "model.py":
                module_name = os.path.relpath(os.path.join(root, file[:-3])).replace(
                    os.sep, "."
                )

                try:
                    module = importlib.import_module(module_name)
                except Exception as exc:
                    # Report an unimportable example as one failing test. Raising
                    # here would abort collection for the whole file, so a single
                    # broken import would hide every other example's result.
                    models.append(pytest.param(exc, id=module_name))
                    continue

                for item in dir(module):
                    obj = getattr(module, item)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, Model)
                        and obj is not Model
                    ):
                        models.append(obj)

    return models


@pytest.mark.parametrize("model_class", get_models("examples"))
def test_model_steps(model_class):
    if isinstance(model_class, Exception):
        pytest.fail(f"example could not be imported: {model_class!r}")

    model = model_class()  # Assume no arguments are needed
    model.run_for(10)
    assert model.time == 10.0
