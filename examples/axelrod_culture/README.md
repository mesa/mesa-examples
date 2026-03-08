# Axelrod Culture Model

## Summary

An implementation of Axelrod's model of cultural dissemination. Each agent occupies a cell on a grid and holds a "culture" consisting of **F** features, each taking one of **Q** possible integer traits. At each step, an agent randomly selects a neighbor and interacts with probability equal to their cultural similarity (fraction of shared features). If interaction occurs, the agent copies one of the neighbor's differing traits.

Despite the local tendency toward convergence, stable cultural regions can persist globally — Axelrod's key insight: local homogenization and global polarization can coexist. The number of stable regions increases with Q (more possible traits → more diversity) and decreases with F (more features → more overlap → faster convergence).

## How to Run

To install the dependencies use pip and the requirements.txt in this directory:

    $ pip install -r requirements.txt

To run the model interactively, in this directory, run the following command:

    $ solara run app.py

## Files

* [agents.py](axelrod_culture/agents.py): Defines `CultureAgent` with a cultural profile and interaction logic
* [model.py](axelrod_culture/model.py): Sets up the grid, initializes random cultures, and tracks cultural regions
* [app.py](app.py): Solara based visualization showing the culture grid and region count over time

## Further Reading

* Axelrod, R. (1997). The dissemination of culture: A model with local convergence and global polarization. *Journal of Conflict Resolution*, 41(2), 203–226. https://doi.org/10.1177/0022002797041002001