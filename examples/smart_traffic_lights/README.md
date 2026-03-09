# Smart Traffic Lights

## Summary

An optimization simulation where traffic light agents use local information to minimize vehicle wait times at intersections.

![Simulation of Smart Traffic Controller](./assets/chrome-capture-2026-03-09_TrafficModel_Mesa.gif)

## Installation

To install the dependencies use pip and the requirements.txt in this directory. e.g.

```
    $ pip install -r requirements.txt
```



Then open your browser to [http://127.0.0.1:8521/](http://127.0.0.1:8521/), select the model parameters, press Reset, then Start.

## Files

* ``smart_traffic_light/agents.py``: Defines the CarAgent, the TrafficLightAgent and the IntersectionController classes.
* ``smart_traffic_light/model.py``: Defines the Traffic model and the DataCollector functions.
* ``run_example.py``: Script to compare waiting time in traffic using smart and normal traffic light controller.
* ``app.py``: Visualization script on Solara.
