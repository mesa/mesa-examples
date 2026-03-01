# Hierarchical Organization Model

**Category:** Organizational Modeling
**Focus:** Meta-Agent Hierarchies & Explicit Activation Semantics
**Mesa Version:** >=3.0
**Visualization:** SolaraViz

---

## What This Model Does

This example implements a three-level hierarchical agent system that simulates how organizations respond to workload pressure and external disruptions:

```
EmployeeAgent → DepartmentAgent → OrganizationAgent
```

Each level acts as a **meta-agent** that aggregates and responds to the level below it:

- **Employees** produce output based on their productivity and morale.
- **Departments** aggregate employee performance and rebalance workload.
- **The Organization** evaluates department performance and applies a global policy boost or penalty to employee morale.

---

## Why Meta-Agents?

In many real systems, decisions happen at multiple levels simultaneously — an employee's behavior is influenced by their department, which is in turn constrained by organizational policy. A flat agent model cannot capture this cleanly.

This example shows how Mesa 3.x supports hierarchical activation explicitly, without needing a scheduler. The activation order is deliberate:

1. Employees step first (bottom-up information flow)
2. Departments aggregate and adjust workload
3. Organization evaluates and updates policy

---

## What Is the "Shock"?

The `shock_probability` parameter introduces a random external disruption each step (e.g. a market downturn, a sudden restructuring). When triggered, all employees receive a random morale penalty. This tests the system's **resilience**: can the department and organization-level feedback loops recover output after a shock?

---

## Mesa 3.x Compatibility Notes

This example was written to address several breaking changes in Mesa 3.x:

- **No `RandomActivation`**: Removed in Mesa 3.x. Activation is now handled explicitly in `model.step()`.
- **Agent constructor**: `unique_id` is auto-assigned by `super().__init__(model)`. Do not pass or manually set it.
- **Relative imports**: `agents.py` uses `from .agents import ...` so the package works correctly when run from the repo root via pytest or `solara run`.

---

## Run Instructions

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m solara run app.py
```

---

## Parameters

| Parameter | Default | Description |
| `num_departments` | 3 | Number of department agents |
| `employees_per_department` | 5 | Employees per department |
| `shock_probability` | 0.05 | Per-step probability of an external shock |