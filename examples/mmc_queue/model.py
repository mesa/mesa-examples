"""M/M/c queuing model: a pure discrete event simulation in Mesa.

Demonstrates schedule_recurring (arrivals), schedule_event (service),
and run_until — no step() needed.
"""

from collections import deque

from mesa import Model
from mesa.time import Schedule

try:
    from .agents import Customer, Server
except ImportError:
    from agents import Customer, Server


class MMcQueue(Model):
    """M/M/c queuing system.

    Args:
        arrival_rate: Mean arrival rate (λ). Customers per time unit.
        service_rate: Mean service rate per server (μ).
        n_servers: Number of servers (c).
        rng: Random number generator seed.
    """

    def __init__(self, arrival_rate=1.0, service_rate=0.5, n_servers=2, **kwargs):
        super().__init__(**kwargs)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.n_servers = n_servers

        # Queue
        self.queue = deque()

        # Metrics
        self.customers_served = 0
        self.total_wait_time = 0.0
        self.total_system_time = 0.0

        # Create servers
        self.servers = [Server(self, service_rate) for _ in range(n_servers)]

        # Disable default step schedule — pure DES
        self._default_schedule.stop()

        # Schedule stochastic arrivals
        self.schedule_recurring(
            self._customer_arrival,
            Schedule(
                interval=lambda m: m.rng.exponential(1.0 / m.arrival_rate),
                start=0.0,
            ),
        )

    def _customer_arrival(self):
        """Handle a customer arrival."""
        customer = Customer(self)

        for server in self.servers:
            if server.is_idle:
                server.start_service(customer)
                return

        self.queue.append(customer)

    def _record_departure(self, customer):
        """Record metrics for a departing customer."""
        self.customers_served += 1
        self.total_wait_time += customer.wait_time
        self.total_system_time += customer.system_time

    # --- Metrics ---

    @property
    def avg_wait_time(self):
        if self.customers_served == 0:
            return 0.0
        return self.total_wait_time / self.customers_served

    @property
    def avg_system_time(self):
        if self.customers_served == 0:
            return 0.0
        return self.total_system_time / self.customers_served

    @property
    def server_utilization(self):
        if self.time == 0:
            return 0.0
        return sum(s.busy_time for s in self.servers) / (self.n_servers * self.time)

    @property
    def current_queue_length(self):
        return len(self.queue)


if __name__ == "__main__":
    try:
        from .analytical_mmc import analytical_mmc
    except ImportError:
        from analytical_mmc import analytical_mmc

    ARRIVAL_RATE = 2.0
    SERVICE_RATE = 1.0
    N_SERVERS = 3
    SIM_TIME = 10_000.0

    model = MMcQueue(
        arrival_rate=ARRIVAL_RATE,
        service_rate=SERVICE_RATE,
        n_servers=N_SERVERS,
        rng=42,
    )
    model.run_until(SIM_TIME)

    analytical = analytical_mmc(ARRIVAL_RATE, SERVICE_RATE, N_SERVERS)

    print(f"M/M/{N_SERVERS} Queue (λ={ARRIVAL_RATE}, μ={SERVICE_RATE}, T={SIM_TIME})")
    print(f"Customers served: {model.customers_served}\n")
    print(f"{'Metric':<25} {'Simulated':>12} {'Analytical':>12}")
    print("-" * 51)
    print(
        f"{'Server utilization':<25} {model.server_utilization:>12.4f} {analytical['utilization']:>12.4f}"
    )
    print(
        f"{'Avg wait time':<25} {model.avg_wait_time:>12.4f} {analytical['avg_wait_time']:>12.4f}"
    )
    print(
        f"{'Avg system time':<25} {model.avg_system_time:>12.4f} {analytical['avg_system_time']:>12.4f}"
    )
