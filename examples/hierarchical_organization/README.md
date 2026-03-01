# Hierarchical Organization Model

**Category:** Organizational Modeling
**Mesa Version:** >=3.0
**Visualization:** SolaraViz

---

## Overview

A three-level hierarchical agent simulation:

```
EmployeeAgent → DepartmentAgent → OrganizationAgent
```

Employees produce output based on productivity and morale. Departments aggregate performance and rebalance workload. The Organization applies global policy adjustments each step.

---

## Run Instructions

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m solara run app.py
```

---

## Parameters

| Parameter | Default | Description |

| `num_departments` | 3 | Number of departments |
| `employees_per_department` | 5 | Employees per department |
| `shock_probability` | 0.05 | Probability of external shock per step |

---

## Mesa 3.x Notes

- No legacy schedulers — activation is explicit in `model.step()`
- `unique_id` is auto-assigned by Mesa 3.x via `super().__init__(model)`
- Relative imports used throughout for pytest compatibility