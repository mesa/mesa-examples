# Mesa Examples
## Core Mesa examples
The core Mesa examples are available at the main Mesa repository: https://github.com/mesa/mesa/tree/main/mesa/examples

Those core examples are fully tested, updated and guaranteed to work with the Mesa release that they are included with. They are also included in the Mesa package, so you can access them directly from your Python environment.

## Mesa user examples
This repository contains user examples and showcases that illustrate different features of Mesa. For more information on each model, see its own Readme and documentation.

- Mesa examples that work on the Mesa and Mesa-Geo main development branches are available here on the [`main`](https://github.com/mesa/mesa-examples) branch.
- Mesa examples that work with Mesa 2.x releases and Mesa-Geo 0.8.x releases are available here on the [`mesa-2.x`](https://github.com/mesa/mesa-examples/tree/mesa-2.x) branch.

To contribute to this repository, see [CONTRIBUTING.rst](https://github.com/mesa/mesa-examples/blob/main/CONTRIBUTING.rst).

This repo also contains a package that readily lets you import and run some of the examples:
```console
$ # This will install the "mesa_models" package
$ pip install -U -e git+https://github.com/mesa/mesa-examples#egg=mesa-models
```
For Mesa 2.x examples, install:
```console
$ # This will install the "mesa_models" package
$ pip install -U -e git+https://github.com/mesa/mesa-examples@mesa-2.x#egg=mesa-models
```
```python
from mesa_models.boltzmann_wealth_model.model import BoltzmannWealthModel

```
You can see the available models at [setup.cfg](https://github.com/mesa/mesa-examples/blob/main/setup.cfg).

Table of Contents
=================

* [Grid Spacce Examples](#grid-space-examples)
* [Continuous Space Examples](#continuous-space-examples)
* [Network Examples](#network-examples)
* [Visualization Examples](#visualization-examples)
* [GIS Examples](#gis-examples)
* [Other Examples](#other-examples)

## Grid Space Examples

### [Bank Reserves Model](https://github.com/mesa/mesa-examples/blob/main/examples/bank_reserves)

A highly abstracted, simplified model of an economy, with only one type of agent and a single bank representing all banks in an economy.

### [Color Patches Model](https://github.com/mesa/mesa-examples/tree/main/examples/color_patches)

A cellular automaton model where agents opinions are influenced by that of their neighbors. As the model evolves, color patches representing the prevailing opinion in a given area expand, contract, and sometimes disappear.

### [Conway's Game Of "Life" Model (Fast)](https://github.com/mesa/mesa-examples/tree/main/examples/conways_game_of_life_fast)

A very fast performance optimized version of Conway's Game of Life using the Mesa [`PropertyLayer`](https://github.com/mesa/mesa/pull/1898). About 100x as fast as the regular versions, but limited visualisation (for [now](https://github.com/mesa/mesa/issues/2138)).

### [Conway's Game Of "Life" Model on a Hexagonal Grid](https://github.com/mesa/mesa-examples/tree/main/examples/hex_snowflake)

Conway's game of life on a hexagonal grid.

### [Forest Fire Model](https://github.com/mesa/mesa-examples/tree/main/examples/forest_fire)

Simple cellular automata of a fire spreading through a forest of cells on a grid, based on the NetLogo [Fire](http://ccl.northwestern.edu/netlogo/models/Fire) model.

### [Hotelling's Law Model](https://github.com/mesa/mesa-examples/tree/main/examples/hotelling_law)

This project is an agent-based model implemented using the Mesa framework in Python. It simulates market dynamics based on Hotelling's Law, exploring the behavior of stores in a competitive market environment. Stores adjust their prices and locations if it's increases market share to maximize revenue, providing insights into the effects of competition and customer behavior on market outcomes.

### [Rumor Mill Model](https://github.com/mesa/mesa-examples/tree/main/examples/rumor_mill)

A simple agent-based simulation showing how rumors spread through a population based on the spread chance and initial knowing percentage, implemented with the Mesa framework and adapted from NetLogo [Rumor mill](https://www.netlogoweb.org/launch#https://www.netlogoweb.org/assets/modelslib/Sample%20Models/Social%20Science/Rumor%20Mill.nlogox).


## Continuous Space Examples
_No user examples available yet._


## Network Examples

### [Boltzmann Wealth Model with Network](https://github.com/mesa/mesa-examples/tree/main/examples/boltzmann_wealth_model_network)

This is the same [Boltzmann Wealth](https://github.com/mesa/mesa-examples/tree/main/examples/boltzmann_wealth_model) Model, but with a network grid implementation.

### [Ant System for Traveling Salesman Problem](https://github.com/mesa/mesa-examples/tree/main/examples/aco_tsp)

This is based on Dorigo's Ant System "Swarm Intelligence" algorithm for generating solutions for the Traveling Salesman Problem.

## Visualization Examples

### [Charts Example](https://github.com/mesa/mesa-examples/tree/main/examples/charts)

A modified version of the [Bank Reserves](https://github.com/mesa/mesa-examples/tree/main/examples/bank_reserves) example made to provide examples of Mesa's charting tools.

### [Shape Example](https://github.com/mesa/mesa-examples/tree/main/examples/shape_example)

Example of grid display and direction showing agents in the form of arrow-head shape.

## GIS Examples

### Vector Data

- [GeoSchelling Model (Polygons)](https://github.com/mesa/mesa-examples/tree/main/gis/geo_schelling)
- [GeoSchelling Model (Points & Polygons)](https://github.com/mesa/mesa-examples/tree/main/gis/geo_schelling_points)
- [GeoSIR Epidemics Model](https://github.com/mesa/mesa-examples/tree/main/gis/geo_sir)
- [Agents and Networks Model](https://github.com/mesa/mesa-examples/tree/main/gis/agents_and_networks)

### Raster Data

- [Rainfall Model](https://github.com/mesa/mesa-examples/tree/main/gis/rainfall)
- [Urban Growth Model](https://github.com/mesa/mesa-examples/tree/main/gis/urban_growth)

### Raster and Vector Data Overlay

- [Population Model](https://github.com/mesa/mesa-examples/tree/main/gis/population)

## Other Examples

### [El Farol Model](https://github.com/mesa/mesa-examples/tree/main/examples/el_farol)

This folder contains an implementation of El Farol restaurant model. Agents (restaurant customers) decide whether to go to the restaurant or not based on their memory and reward from previous trials. Implications from the model have been used to explain how individual decision-making affects overall performance and fluctuation.

### [Schelling Model with Caching and Replay](https://github.com/mesa/mesa-examples/tree/main/examples/caching_and_replay)

This example applies caching on the Mesa [Schelling](https://github.com/mesa/mesa-examples/tree/main/examples/schelling) example. It enables a simulation run to be "cached" or in other words recorded. The recorded simulation run is persisted on the local file system and can be replayed at any later point.
