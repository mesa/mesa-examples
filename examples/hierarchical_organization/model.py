from mesa import Model
from mesa.datacollection import DataCollector
import random

# Use relative imports so pytest can find the module from repo root
from .agents import EmployeeAgent, DepartmentAgent, OrganizationAgent


class HierarchicalOrganizationModel(Model):
    """
    Demonstrates explicit hierarchical activation in Mesa 3.x.

    Three-level hierarchy:
        EmployeeAgent → DepartmentAgent → OrganizationAgent

    Activation order is explicit and deliberate:
    1. All employees act first (produce output, update morale).
    2. Departments aggregate and rebalance workload.
    3. Organization evaluates globally and adjusts policy.

    This avoids the legacy RandomActivation scheduler entirely,
    which was removed in Mesa 3.x.
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

        self.total_output = 0.0
        self.shock_event = False

        self.employees = []
        self.departments = []

        # Performance threshold scales with department size
        self.performance_threshold = employees_per_department * 1.0

        # Create organization (top-level) — Mesa 3.x auto-assigns unique_id
        self.organization = OrganizationAgent(self)

        # Create departments and employees
        for _ in range(num_departments):
            department = DepartmentAgent(self)
            self.departments.append(department)

            for _ in range(employees_per_department):
                # Pass department's auto-assigned unique_id so employees
                # know which department they belong to
                employee = EmployeeAgent(self, department.unique_id)
                self.employees.append(employee)

        self.datacollector = DataCollector(
            model_reporters={
                "Total Output": lambda m: m.total_output,
                "Avg Department Performance": lambda m: (
                    sum(d.performance for d in m.departments) / len(m.departments)
                ) if m.departments else 0,
                "Shock Event": lambda m: int(m.shock_event),
            }
        )

        self.running = True

    def apply_external_shock(self):
        """
        With probability `shock_probability`, applies a morale penalty
        to all employees to simulate an external disruption (e.g. layoffs,
        market downturn). This tests the system's resilience mechanisms.
        """
        if random.random() < self.shock_probability:
            self.shock_event = True
            for employee in self.employees:
                employee.morale -= random.uniform(0.05, 0.15)
                # Clamp after shock to prevent going below floor
                employee.morale = max(0.1, employee.morale)
        else:
            self.shock_event = False

    def step(self):
        self.total_output = 0.0

        # 1. Apply random external shock
        self.apply_external_shock()

        # 2. Explicit bottom-up activation
        for employee in self.employees:
            employee.step()

        for department in self.departments:
            department.step()

        self.organization.step()

        self.datacollector.collect(self)