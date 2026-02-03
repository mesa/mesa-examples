# Preferential Attachment Network

This model simulates the generation of **scale-free networks** using **preferential attachment**, inspired by the NetLogo [Preferential Attachment model](http://ccl.northwestern.edu/netlogo/models/PreferentialAttachment). It demonstrates how "hubs" with many connections emerge naturally when new nodes prefer to connect to already well-connected nodes.

## Summary

In this simulation, new nodes are added to a growing network one by one. Each new node connects to an existing node, where the probability of connection is **proportional to the degree** (number of connections) of the existing nodes. This leads to the formation of **Barabási-Albert scale-free networks**, where a few nodes (hubs) accumulate many connections, while most nodes have very few.

Such networks are common in real-world systems such as:
- The World Wide Web (webpages linking to other pages),
- Social networks (users connecting with popular accounts),
- Citation networks (new papers citing widely cited publications).

## Installation

Ensure that you have installed the latest version of **Mesa**.


## Usage

To run the simulation:

```bash
solara run app.py
```

## Model Details

### Agents

- **NodeAgent**: Represents a node in the network. Each agent keeps track of its degree and updates its connections as the network grows. New nodes prefer connecting to higher-degree nodes, simulating the preferential attachment process.

### Environment

- **Network**: The model uses Mesa's `Network` to maintain the graph structure, initialized with the fixed no. of agents. Each step connects a node to the existing network, and the visualization updates to reflect the current state of the network.


### Agent Behaviors

- **Preferential Connection**: When a new node is added, it connects to one existing node, with a probability weighted by the existing node’s degree.
- **Growth Step**: Each step corresponds to one node being added to the network.
- **Degree Monitoring**: A line plot is used to track the nodes with degree one.

## References

- Wilensky, U. (2005). *NetLogo Preferential Attachment model*. Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL. Available at: [NetLogo Preferential Attachment](http://ccl.northwestern.edu/netlogo/models/PreferentialAttachment)
- Barabási, A.-L., & Albert, R. (1999). *Emergence of scaling in random networks*. Science, 286(5439), 509-512.