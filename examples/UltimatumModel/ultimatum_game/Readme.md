# Iterated Ultimatum Game with Several Agents

## Summary

The Ultimatum Game is an experimental economics game in which two players interact to decide how to divide a sum of money. This model consists of agents that pair up, one randomly taking the role of proposer and the other the role of responder.

The total stake in this model is 100 units. The proposer chooses a positive integer between 0 and 99 as the offer to pay the responder. The responder has two options:

1. Accept: The offer is recognized as fair, and the money is divided according to the offer.

2. Reject: The offer is recognized as unfair; it is rejected, and neither party receives any amount.

Behavioral studies on this game have shown that, contrary to classic economic theory, responders do not always accept every offer greater than zero.

In this model, initial offers and thresholds start randomly. However, after each step, agents learn based on whether the interaction was successful. Each offer is recorded in the players' memory, increasing the probability of choosing that strategy in the future. The higher the benefit of a specific offer or threshold, the higher its probability weight. In each new step, agents are randomly re-paired and roles are reassigned.

## How to Run

To run the model and see the results, ensure you have mesa, numpy, and matplotlib installed, then execute:

```
    $ python run.py
```

## Files

* ``agents.py``: Contains the ``UltimatumAgent`` class and the learning logic.

* ``model.py``: Contains the ``UltimatumModel`` class. The model takes a positive integer ``n`` as an argument to determine the number of agents.

* ``run.py``: The script used to run the simulation for a specified number of steps and visualize the data.

## Further Reading

This model is adapted from:

* Camerer, Colin F. 2003. Behavioral Game Theory: Experiments in Strategic Interaction. Princeton, NJ: Princeton University Press.