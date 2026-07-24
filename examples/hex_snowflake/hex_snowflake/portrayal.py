def portrayCell(cell):
    """Portrayal function called each tick to describe how to draw a cell.

    Reads the frozen / empty state from model.state_grid rather than from an
    agent attribute, because state now lives on the model as a NumPy array.

    :param cell: the grid cell in the simulation
    :return: the portrayal dictionary
    """
    if cell is None:
        raise AssertionError

    # Retrieve the Cell agent sitting on this grid position.
    agent = cell.agents[0] if cell.agents else None

    # Look up the frozen state from the model-level NumPy array.
    x, y = cell.coordinate
    state = agent.model.state_grid[x, y] if agent else 0

    return {
        "Shape": "hex",
        "r": 1,
        "Filled": "true",
        "Layer": 0,
        "x": x,
        "y": y,
        "Color": "black" if state == 1 else "white",
    }
