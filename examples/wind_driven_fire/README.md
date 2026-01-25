# Wind-Driven Forest Fire

This model demonstrate how wind introduces anisotropy in wildfire rate of spread.

Compared to forest-fire demos that focus on burned area, this model explicitly measures fire-head propagation speed along the wind direction and compares it with crosswind flank spread.

## Description of the Model
Similar to the forest-fire demos, each cell contains a single tree that can be in one of three states:

- **Fine**: unburned fuel
- **On Fire**: actively burning
- **Burned Out**: burned and inert

Fire spreads probabilistically between neighboring trees, with ignition probability biased by wind direction.

### Fire Spread Rule

At each time step, trees that are *On Fire* attempt to ignite their neighbors (Moore neighborhood).
The ignition probability is modified by wind alignment:

$$
p = p_{\text{spread}} \cdot \left( 1 + s \cdot \cos(\theta) \right)
$$
where:
- $ p_{\text{spread}} $ is the baseline spread probability
- $  s $  is wind strength
- $  \theta $  is the angle between the wind direction and the neighbor direction
After spreading fire, burning trees transition to *Burned Out*.


### Wind Representation

Wind is represented as a **global vector field** defined by:

- **Wind direction (degrees)** using the meteorological convention (wind coming *from*)
- **Wind strength**, controlling the magnitude of directional bias

### Fire-Head–Based Rate of Spread

- **Head Distance (Downwind)**: The **fire head** is defined as the furthest burned cell projected onto the wind axis.
Fire-head distance is measured relative to the ignition reference point:

$$
H(t)
=
\max(x \cdot w_x + y \cdot w_y)
-
(x_{\text{ignite}} \cdot w_x + y_{\text{ignite}} \cdot w_y)
$$

This quantity captures the **downwind advance of the fire front**.

- **Flank Half-Width (Crosswind)**: Crosswind spread is measured as the **maximum absolute deviation** from the ignition reference along the crosswind axis:

$$
W(t)
=
\max \left|
x \cdot p_x + y \cdot p_y
-
(x_{\text{ignite}} \cdot p_x + y_{\text{ignite}} \cdot p_y)
\right|
$$

This represents **lateral fire growth (flank spread)** without being affected by upstream contraction.

## Visualization

The visualization shows the spatial fire spread pattern together with
time-series plots of directional rate of spread (ROS).
![Example run with weak wind showing limited anisotropy](<weak wind.png>)
![Example run with strong wind showing pronounced downwind fire spread](<strong wind.png>)

## How to Run

### From this directory, run:
```
$ solara run app.py
```



## Reference

Mesa-example：forest-fire https://github.com/mesa/mesa-examples/tree/main/examples/forest_fire

