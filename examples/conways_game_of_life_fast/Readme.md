## Conway's Game of Life (Fast)
This example demonstrates a fast and efficient implementation of Conway's Game of Life using the [`PropertyLayer`](https://github.com/mesa/mesa/pull/1898) from the Mesa framework.

![GoL_fast_screenshot.png](GoL_fast_screenshot.png)

### Overview
Conway's [Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) is a classic cellular automaton where each cell on a grid can either be alive or dead. The state of each cell changes over time based on a set of simple rules that depend on the number of alive neighbors.

#### Key features:
- **No grid or agents:** This implementation uses the `PropertyLayer` to manage the state of cells, eliminating the need for traditional grids or agents.
- **Fast:** By using 2D convolution to count neighbors, the model efficiently applies the rules of the Game of Life across the entire grid.
- **Toroidal:** The grid wraps around at the edges, creating a seamless, continuous surface.

#### Performance
The model is benchmarked in https://github.com/mesa/mesa/pull/1898#issuecomment-1849000346 to be about 100x faster over a traditional implementation.

![runtime_comparison](https://github.com/mesa/mesa/assets/15776622/d30232c6-e23b-499b-8698-14695a95e627)

- Benchmark code: [benchmark_gol.zip](https://github.com/mesa/mesa/files/13628343/benchmark_gol.zip)

### Getting Started
#### Prerequisites
- Python 3.10 or higher
- Mesa 2.3 or higher (3.0.0b0 or higher for the visualisation)
- NumPy and SciPy

#### Running the Model
To run the model, open a new file or notebook and add:

```Python
from model import GameOfLifeModel
model = GameOfLifeModel(width=10, height=10, alive_fraction=0.2)
for i in range(10):
    model.step()
```
Or to run visualized with Solara, run in your terminal:

```bash
solara run app.py
```

### Understanding the Code
- **Model initialization:** The grid is represented by a `PropertyLayer` where each cell is randomly initialized as alive or dead based on a given probability.
- **`PropertyLayer`:** In the `cell_layer` (which is a `PropertyLayer`), each cell has either a value of 1 (alive) or 0 (dead).
- **Step function:** Each simulation step calculates the number of alive neighbors for each cell and applies the Game of Life rules.
- **Data collection:** The model tracks and reports the number of alive cells and the fraction of the grid that is alive.

### Customization
You can easily modify the model parameters such as grid size and initial alive fraction to explore different scenarios. You can also add more metrics or visualisations.

### Summary
This example provides a fast approach to modeling cellular automata using Mesa's `PropertyLayer`.

### Future work
Add visualisation of the `PropertyLayer` in SolaraViz. See:
- https://github.com/mesa/mesa/issues/2138
