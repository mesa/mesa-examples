import random

from mesa import Agent


class EmployeeAgent(Agent):
    """
    Base-level agent representing an employee.
    """

    def __init__(self, unique_id, model, department_id):
        super().__init__(model)
        self.unique_id = unique_id
        self.department_id = department_id

        self.productivity = random.uniform(0.7, 1.3)
        self.morale = random.uniform(0.7, 1.0)
        self.workload = random.uniform(0.8, 1.0)

    def step(self):
        self.update_morale()
        self.produce()

    def update_morale(self):
        # Workload stress
        if self.workload > 1.2:
            self.morale -= 0.03
        else:
            self.morale += 0.01

        # Natural recovery
        self.morale += 0.005

        self.morale = max(0.1, min(self.morale, 2.0))

    def produce(self):
        output = self.productivity * self.morale
        self.model.total_output += output


class DepartmentAgent(Agent):
    """
    Mid-level meta-agent (Department).
    Aggregates employee performance and adjusts workload.
    """

    def __init__(self, unique_id, model):
        super().__init__(model)
        self.unique_id = unique_id
        self.performance = 0

    def step(self):
        self.aggregate_performance()
        self.adjust_workload()

    def aggregate_performance(self):
        employees = [
            agent
            for agent in self.model.employees
            if agent.department_id == self.unique_id
        ]

        self.performance = sum(agent.productivity * agent.morale for agent in employees)

    def adjust_workload(self):
        employees = [
            agent
            for agent in self.model.employees
            if agent.department_id == self.unique_id
        ]

        # Adaptive threshold (scales with department size)
        target = self.model.performance_threshold
        gap = target - self.performance

        # Damped adjustment
        for agent in employees:
            agent.workload += 0.02 * gap

            # Clamp workload to prevent explosion
            agent.workload = max(0.5, min(agent.workload, 2.0))


class OrganizationAgent(Agent):
    """
    Top-level meta-agent (Organization).
    Applies policy adjustments based on global performance.
    """

    def __init__(self, unique_id, model):
        super().__init__(model)
        self.unique_id = unique_id
        self.policy_factor = 1.0

    def step(self):
        self.evaluate_departments()

    def evaluate_departments(self):
        departments = self.model.departments

        if not departments:
            return

        avg_performance = sum(d.performance for d in departments) / len(departments)

        # Damped policy adjustment
        if avg_performance < self.model.performance_threshold:
            self.policy_factor += 0.01
        else:
            self.policy_factor -= 0.005

        self.policy_factor = max(0.9, min(self.policy_factor, 1.2))

        # Additive morale adjustment (not multiplicative)
        for employee in self.model.employees:
            employee.morale += 0.02 * (self.policy_factor - 1)
