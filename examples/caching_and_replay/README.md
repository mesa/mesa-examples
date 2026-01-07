# Schelling Model with Caching and Replay

## Summary

This example applies caching on the Mesa [Schelling example](https://github.com/mesa/mesa-examples/tree/main/examples/schelling).
It enables a simulation run to be "cached" or in other words recorded. The recorded simulation run is persisted on the local file system and can be replayed at any later point.

It uses the [Mesa-Replay](https://github.com/Logende/mesa-replay) library and puts the Schelling model inside a so-called `CacheableModel` wrapper that we name `CacheableSchelling`.
From the user's perspective, the new model behaves the same way as the original Schelling model, but additionally supports caching.

Note that the main purpose of this example is to demonstrate that caching and replaying simulation runs is possible.
The example is designed to be accessible.
In practice, someone who wants to replay their simulation might not necessarily embed a replay button into the web view, but instead have a dedicated script to run a simulation that is being cached, separate from a script to replay a simulation run from a given cache file.
More examples of caching and replay can be found in the [Mesa-Replay Repository](https://github.com/Logende/mesa-replay/tree/main/examples).

## Installation

To install the dependencies use pip and the requirements.txt in this directory. e.g.

```
    $ pip install -r requirements.txt
```

## How to Run

To run the model interactively, run ``mesa runserver`` in this directory. e.g.

```
    $ mesa runserver
```

or

Directly run the file ``run.py`` in the terminal. e.g.

```
    $ python run.py
```

Then open your browser to [http://127.0.0.1:8521/](http://127.0.0.1:8521/) and press Reset, then Run.

First, run the **simulation** with the 'Replay' switch disabled.
When the simulation run is finished (e.g. all agents are happy, no more new steps are simulated), the run will automatically be stored in a cache file.

Next, **replay** your latest cached simulation run by enabling the Replay switch and then pressing Reset.

## Files

* ``run.py``: Launches a model visualization server and uses `CacheableModelSchelling` as simulation model
* ``cacheablemodel.py``: Implements `CacheableModelSchelling` to make the original Schelling model cacheable
* ``model.py``: Taken from the original Mesa Schelling example
* ``server.py``: Taken from the original Mesa Schelling example

## Further Reading

* [Mesa-Replay library](https://github.com/Logende/mesa-replay)
* [More caching and replay examples](https://github.com/Logende/mesa-replay/tree/main/examples)
