import random

from mesa import Agent


class EmployeeAgent(Agent):
    """
    Base-level agent representing an employee.
    Produces output based on productivity and morale.
    """

    def __init__(self, model, department_id):
        super().__init__(model)
        # NOTE: In Mesa 3.x, unique_id is auto-assigned by super().__init__()
        # Do NOT manually set self.unique_id — it conflicts with Mesa internals.
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
    Mid-level meta-agent representing a Department.
    Aggregates employee performance and adjusts workload.
    """

    def __init__(self, model):
        super().__init__(model)
        # unique_id auto-assigned by Mesa 3.x
        self.performance = 0.0

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
        target = self.model.performance_threshold
        gap = target - self.performance

        for agent in employees:
            agent.workload += 0.02 * gap
            agent.workload = max(0.5, min(agent.workload, 2.0))


class OrganizationAgent(Agent):
    """
    Top-level meta-agent representing the Organization.
    Applies policy adjustments based on global performance.
    """

    def __init__(self, model):
        super().__init__(model)
        # unique_id auto-assigned by Mesa 3.x
        self.policy_factor = 1.0

    def step(self):
        self.evaluate_departments()

    def evaluate_departments(self):
        departments = self.model.departments
        if not departments:
            return

        avg_performance = sum(d.performance for d in departments) / len(departments)

        if avg_performance < self.model.performance_threshold:
            self.policy_factor += 0.01
        else:
            self.policy_factor -= 0.005

        self.policy_factor = max(0.9, min(self.policy_factor, 1.2))

        # Additive morale boost/penalty based on policy
        for employee in self.model.employees:
            employee.morale += 0.02 * (self.policy_factor - 1.0)
