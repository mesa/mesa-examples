# Forest Fire Model Extended with Optional Wind Bias
This implementation extends the original Mesa Forest Fire model by adding an optional wind-driven fire spread mechanism, while preserving the original deterministic behavior as the default mode.

### New Features
This extended version introduces an optional wind bias module with the following capabilities:

1. **default behavior**

By default:

- Fire spreads deterministically to all neighboring Fine trees
- Initial ignition occurs in the leftmost column (x = 0)
- Behavior is identical to the original Mesa Forest Fire model

No wind effects are applied unless explicitly enabled.

2. **Optional probabilistic fire spread**

When probabilistic spread is enabled:

Fire spreads with base probability`p_spread`instead of deterministic spreading. This allows modeling stochastic fire propagation.

3. **Wind bias mechanism (optional)**

When wind bias is enabled:

- Fire spread probability is modified based on alignment with wind direction
- Spread is more likely downwind
- Spread is less likely upwind

Wind influence is calculated using the cosine alignment between the wind vector and spread direction:
```
p_effective = p_spread × wind_multiplier
```
Where:
```
wind_multiplier = max(0, 1 + wind_strength × alignment)
```
This produces directional fire growth.

4. **Wind-dependent ignition location**

To better simulate wind-driven fire scenarios:

- Wind disabled (default)
Fire ignites from the leftmost column (original behavior)

- Wind enabled
Fire ignites from a central region around the grid center

This allows symmetric wind-driven expansion.

### New Parameters

| Parameter     | Description                                         | Default |
| ------------- | --------------------------------------------------- | ------- |
| use_prob      | Enable probabilistic spread                         | False   |
| p_spread      | Base spread probability                             | 0.5   |
| wind_enabled  | Enable wind bias                                    | False   |
| wind_dir      | Wind direction (degrees, meteorological convention) | 0       |
| wind_strength | Wind influence strength                             | 1.0     |
