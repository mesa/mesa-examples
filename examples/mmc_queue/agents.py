"""Customer and Server agents for the M/M/c queue model."""

from mesa import Agent


class Customer(Agent):
    """A customer in the queuing system.

    Created on arrival, removed after service. Tracks timestamps
    for wait time and system time calculations.
    """

    def __init__(self, model):
        super().__init__(model)
        self.arrival_time = model.time
        self.service_start_time = None
        self.service_end_time = None

    @property
    def wait_time(self):
        """Time spent waiting in queue before service began."""
        if self.service_start_time is None:
            return None
        return self.service_start_time - self.arrival_time

    @property
    def system_time(self):
        """Total time in the system (wait + service)."""
        if self.service_end_time is None:
            return None
        return self.service_end_time - self.arrival_time


class Server(Agent):
    """A server that pulls customers from the queue when idle.

    Server-centric design: after completing service, the server
    checks the queue and pulls the next customer itself.
    """

    def __init__(self, model, service_rate):
        super().__init__(model)
        self.service_rate = service_rate
        self.current_customer = None
        self.busy_time = 0.0
        self._service_started_at = None

    @property
    def is_idle(self):
        return self.current_customer is None

    def start_service(self, customer):
        """Begin serving a customer."""
        customer.service_start_time = self.model.time
        self.current_customer = customer
        self._service_started_at = self.model.time

        duration = self.model.rng.exponential(1.0 / self.service_rate)
        self.model.schedule_event(self._complete_service, after=duration)

    def _complete_service(self):
        """Complete service and try to pull next customer from queue."""
        customer = self.current_customer
        customer.service_end_time = self.model.time
        self.busy_time += self.model.time - self._service_started_at

        self.model._record_departure(customer)
        customer.remove()

        # Server-centric: actively pull from queue
        self.current_customer = None
        self._service_started_at = None
        if self.model.queue:
            self.start_service(self.model.queue.popleft())
