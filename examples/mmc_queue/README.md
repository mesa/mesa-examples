# M/M/c Queue
A classic [M/M/c queue](https://en.wikipedia.org/wiki/M/M/c_queue) implemented as a pure discrete event simulation in Mesa.

## Summary
Customers arrive according to a Poisson process (rate λ) and join a single FIFO queue. *c* servers each draw from the queue independently, with exponentially distributed service times (rate μ per server). This is the standard multi-server queuing model from operations research, with well-known analytical solutions for validation.

### Mesa DES features demonstrated

| Feature | Usage |
|---|---|
| `schedule_recurring` | Stochastic customer arrivals (exponential inter-arrival times) |
| `schedule_event(after=...)` | Scheduling service completions |
| `run_until` | Running a pure event-driven simulation to a target time |
| Dynamic agent lifecycle | Customers created on arrival, `remove()`d after service |

The model disables Mesa's default step schedule (`_default_schedule.stop()`) and is driven entirely by events.

### Design: server-centric
Servers are active agents. When a server completes service, it checks the queue and pulls the next customer itself — a natural ABM pattern, in contrast to the system-centric routing common in traditional DES.

## How to run
```bash
python model.py
```

Runs the simulation for 10,000 time units and prints simulated vs. analytical steady-state metrics.

## Files

| File | Description |
|---|---|
| `agents.py` | `Customer` and `Server` agents |
| `model.py` | `MMcQueue` model |
| `analytical_mmc.py` | Erlang C closed-form solutions for validation |

## Analytical validation
For a stable M/M/c system (traffic intensity $ρ = λ/(cμ) < 1$), closed-form results exist via the Erlang C formula. The model includes `analytical_mmc()` to compute these, so simulation output can be compared directly:

```
M/M/3 Queue (λ=2.0, μ=1.0, T=10000.0)
Customers served: 19992

Metric                     Simulated   Analytical
---------------------------------------------------
Server utilization              0.6672       0.6667
Avg wait time                   0.3716       0.3750
Avg system time                 1.3716       1.3750
```

Results converge to analytical values as simulation time increases.

## Visualisation
There's no visualization yet, but an `app.py` implementation would be appreciated!
