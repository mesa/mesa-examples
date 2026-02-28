import random

from agents import DepartmentAgent, EmployeeAgent, OrganizationAgent
from mesa import Model
from mesa.datacollection import DataCollector


class HierarchicalOrganizationModel(Model):
    """
    Demonstrates explicit hierarchical activation in Mesa 3.x.

    Employees → Departments → Organization
    """

    def __init__(
        self,
        num_departments=3,
        employees_per_department=5,
        shock_probability=0.05,
    ):
        super().__init__()

        self.num_departments = num_departments
        self.employees_per_department = employees_per_department
        self.shock_probability = shock_probability

        self.total_output = 0
        self.shock_event = False

        self.employees = []
        self.departments = []

        # Adaptive threshold
        self.performance_threshold = employees_per_department * 1.0

        self.organization = OrganizationAgent("ORG", self)

        # Create departments and employees
        for d in range(num_departments):
            department = DepartmentAgent(f"Dept_{d}", self)
            self.departments.append(department)

            for e in range(employees_per_department):
                emp_id = f"Emp_{d}_{e}"
                employee = EmployeeAgent(emp_id, self, department.unique_id)
                self.employees.append(employee)

        self.datacollector = DataCollector(
            model_reporters={
                "Total Output": lambda m: m.total_output,
                "Avg Department Performance": lambda m: (
                    sum(d.performance for d in m.departments) / len(m.departments)
                )
                if m.departments
                else 0,
                "Shock Event": lambda m: int(m.shock_event),
            }
        )

        self.running = True

    def apply_external_shock(self):
        if random.random() < self.shock_probability:
            self.shock_event = True
            for employee in self.employees:
                employee.morale -= random.uniform(0.05, 0.15)
        else:
            self.shock_event = False

    def step(self):
        self.total_output = 0

        self.apply_external_shock()

        # Explicit hierarchical activation
        for employee in self.employees:
            employee.step()

        for department in self.departments:
            department.step()

        self.organization.step()

        self.datacollector.collect(self)
