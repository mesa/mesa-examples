# Hierarchical Organization Model

**Mesa Version:** >=3.0 | **Visualization:** SolaraViz

---

## Overview

This model simulates how a three-level organization works — employees doing the actual work, departments managing them, and an organization setting policy for everyone.

```
EmployeeAgent → DepartmentAgent → OrganizationAgent
```

Each level responds to what's happening below it. Employees produce output based on their productivity and morale. Departments watch that output and adjust workloads accordingly. The organization looks at the overall picture and nudges morale up or down through policy.

The model also introduces random external shocks — sudden morale drops across all employees — to see whether the system can absorb and recover from disruptions.

---

## How to Run

```bash
pip install mesa[rec]
python -m solara run app.py
```

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `num_departments` | 3 | Number of departments |
| `employees_per_department` | 5 | Employees per department |
| `shock_probability` | 0.05 | Probability of external shock per step |

---

## Mesa 3.x Notes

- No legacy schedulers — activation is explicit in `model.step()`
- `unique_id` is auto-assigned by Mesa 3.x via `super().__init__(model)`
- Relative imports used throughout for pytest compatibility