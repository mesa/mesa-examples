# Solar Adoption Model

This model demonstrates a simulation of households adopting solar panels, driven by two key geographic factors:
1. **Environmental (Raster Data):** The economic viability of solar is based on local solar radiation (simulated via a `RasterLayer`).
2. **Social (Vector Data):** The "peer effect" where households are more likely to adopt solar panels if their neighbors—within a certain distance—have already adopted them. Households are represented as `GeoAgents`.

This example is specifically designed to showcase how `mesa-geo` integrates both **Continuous Space (Raster)** environments and **Discrete Space (Vector)** agents interacting with one another.

## How to Run

To run the model, first install the dependencies:

```bash
pip install -r requirements.txt
```

Then run the application:

```bash
solara run app.py
```

Then visit the provided localhost address in your web browser.

## Using the Interface

- **Number of Households:** Controls how many `Household` agents populate the environment.
- **Social Influence Weight:** Adjusts how strongly a household is influenced by neighbors who already have solar panels.
- **Economic Weight (Radiation):** Adjusts how strongly the underlying solar radiation `RasterLayer` influences adoption.

Watch how clusters of adoption naturally form in areas with high solar radiation and slowly spread outward through social influence!
