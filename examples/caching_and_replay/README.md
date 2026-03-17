# Schelling Model with Caching and Replay

## Summary

This example demonstrates how to record and replay Mesa simulations using the [Mesa-Replay](https://github.com/Logende/mesa-replay) library. It wraps the standard [Schelling segregation model](https://github.com/mesa/mesa-examples/tree/main/examples/schelling) with `CacheableModel`, allowing you to:

- **Record** simulations by saving the model state at each step to a cache file
- **Replay** previously recorded simulations to examine specific runs

The cacheable model behaves identically to a regular Mesa model but with added recording/replay capabilities. More examples can be found in the [Mesa-Replay repository](https://github.com/Logende/mesa-replay/tree/main/examples).

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

### Interactive Visualization

Run the cacheable version with replay controls:

```bash
solara run run.py
```

Or run the standard (non-cacheable) version:

```bash
solara run server.py
```

Then open [http://localhost:8765](http://localhost:8765) in your browser.

### Recording a Simulation

1. Uncheck the **'Replay cached run?'** checkbox
2. Adjust the **Cache File Path** if desired (default: `./my_cache_file_path.cache`)
3. Click **Reset**, then **Run**
4. The cache is saved automatically when the simulation completes

### Replaying a Simulation

1. Check the **'Replay cached run?'** checkbox
2. Ensure the cache file path matches your recorded file
3. Click **Reset**, then **Run**
4. The simulation will replay the exact recorded sequence

## Notes

- The cache file is written when the simulation completes (when `model.running` becomes `False`)
- During recording, model states are held in memory and written once at the end
- For large simulations, consider the memory requirements of caching all steps
- By default, every step is cached. For large runs, you can adjust `cache_step_rate` to cache fewer steps

## Files

* `run.py` - Cacheable model visualization with replay controls
* `cacheablemodel.py` - CacheableSchelling implementation with Mesa 3.x support
* `model.py` - Standard Schelling segregation model
* `server.py` - Standard (non-cacheable) visualization
* `requirements.txt` - Required packages

## Further Reading

* [Mesa-Replay library](https://github.com/Logende/mesa-replay)
* [Mesa-Replay examples](https://github.com/Logende/mesa-replay/tree/main/examples)
* [Original Schelling model](https://github.com/mesa/mesa-examples/tree/main/examples/schelling)
