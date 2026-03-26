# Airport Operations Simulation in Mesa: Towards Queueing and Resource Modeling Extensions

## Idea

This project investigates how Mesa can be used to model a real-world operational system where system dynamics are driven not only by agent interactions, but also by queues and constrained resources. The chosen case study is an airport operations simulator, where aircraft compete for limited runway capacity under priority and safety constraints.

The core objective is not only to implement the model, but to evaluate how well Mesa supports this class of systems and to identify missing abstractions that could be generalized for broader use.

---

## Reference to Previous Work

The work builds on an earlier standalone implementation:

[https://github.com/Vadim3377/SWE-project](https://github.com/Vadim3377/SWE-project)

The original project implemented a discrete-time airport simulation with:

* priority-based holding queues for inbound aircraft
* FIFO takeoff queues for outbound aircraft
* runway assignment and service logic
* statistical reporting (queue sizes, wait times, cancellations, etc.)

While functionally complete, this system was not structured within an agent-based modeling framework and lacked extensibility, standardised data collection, and interactive visualization.

---

## Transition to Mesa

The project was reimplemented using Mesa to explore how an operational system can be expressed in an ABM paradigm.

The mapping between the original system and Mesa is as follows:

* aircraft: `AircraftAgent`
* runways: `RunwayAgent`
* simulation engine:  `AirportModel`
* queues:  separate queue module (`queues.py`)
* statistics: Mesa `DataCollector`

This transition made the architecture more modular and reusable, and enabled integration with Mesa’s visualization tools. At the same time, it exposed limitations in Mesa when modeling systems that are primarily driven by queues and service constraints rather than spatial interactions.

---

## Learning Experience

The implementation was guided by Mesa tutorials and documentation, including:

* the introductory model tutorial for understanding agent and model structure
* time and scheduling concepts for designing the simulation loop
* data collection for tracking system metrics
* visualization using SolaraViz for interactive dashboards

This process provided a deeper understanding of Mesa’s design philosophy and highlighted how its abstractions apply to non-standard ABM use cases.

---

## Implementation and Description

The model simulates airport operations as a discrete-time system.

Aircraft are represented as agents with state variables including type (inbound or outbound), fuel level, emergency status, and waiting time. Inbound aircraft consume fuel over time and may escalate to emergency or be diverted if fuel falls below a threshold. Outbound aircraft may be cancelled if their waiting time exceeds a maximum limit.

Runways are modeled as service resources that process aircraft for landing or takeoff, with configurable service durations. Each runway maintains its own state, including current operation and remaining service time.

The system is driven by two queues. The holding queue is implemented as a priority queue where emergency aircraft are prioritised and FIFO ordering is preserved within priority levels. The takeoff queue is implemented as a FIFO queue.

Each simulation step performs the following sequence:

* update aircraft states (waiting time, fuel consumption)
* update runway service progress
* generate new aircraft arrivals
* update queue priorities and constraints
* assign runways to available aircraft
* collect statistics

Visualization is provided both through static plots and an interactive dashboard using SolaraViz, allowing real-time inspection of queue sizes, throughput, and runway utilisation.

---

## Observations

The implementation demonstrates that Mesa provides a strong structure for organizing models and collecting data, but that key elements of queueing systems must be implemented manually.

In particular:

* there are no built-in abstractions for queues or resource-constrained services
* visualization is primarily oriented toward spatial models rather than operational dashboards
* modeling of service systems requires combining agent logic with external scheduling and queue management

These observations align with the Mesa GSoC direction of evaluating what works well in practice and identifying missing components through implementation experience. 

---

## Proposed Improvements

This project suggests a natural extension of Mesa in line with the 2026 project ideas, particularly the **behavioral framework initiative**, which emphasizes implementing models, identifying limitations, and proposing reusable improvements based on practical experience. 

Based on this work, the following improvements are proposed:

A queueing and resource module could be introduced, providing reusable abstractions such as priority queues, FIFO queues, and service resources. These components would generalize beyond the airport model and support a wide class of systems including healthcare, logistics, and transportation.

A more flexible policy framework for resource allocation could allow users to define and compare strategies for scheduling and prioritization. In this project, runway assignment policies significantly affect system behaviour, suggesting the need for modular strategy definitions.

Visualization support could be extended to better accommodate non-spatial models, with built-in dashboard components for metrics, queue states, and resource utilisation rather than relying primarily on spatial portrayals.

Finally, example models in Mesa could be expanded to include operational systems such as airport or service-center simulations, complementing existing examples and improving accessibility for users working outside traditional spatial ABM domains.


