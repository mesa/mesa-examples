# Emergency Room Simulation

An example model demonstrating Mesa's [Action system](https://github.com/mesa/mesa/pull/3461).

Patients arrive at random intervals, get triaged by severity (critical / moderate / minor), and are treated by available doctors. Critical treatments cannot be interrupted; moderate ones can be bumped by a higher-priority patient and resumed later.

## What it demonstrates

| Feature | How it's used |
|---------|---------------|
| `Action` subclassing | `Triage` and `Treat` actions with lifecycle hooks |
| Interruptible actions | Moderate treatments can be bumped by critical patients |
| Resumable actions | Interrupted treatments resume from where they left off |
| `schedule_event` | Stochastic patient arrivals via exponential distribution |
| Priority queue | Critical patients are seen before moderate ones |

## Running it

```bash
pip install -r requirements.txt
python -c "
from er_simulation.model import ERModel
from er_simulation.agents import Patient, Doctor

model = ERModel(n_doctors=3, arrival_rate=1.5, seed=42)
for _ in range(50):
    model.step()

patients = list(model.agents_by_type[Patient])
discharged = [p for p in patients if p.status == 'discharged']
print(f'Total patients: {len(patients)}')
print(f'Discharged: {len(discharged)}')
if discharged:
    avg = sum(p.wait_time for p in discharged) / len(discharged)
    print(f'Avg wait time: {avg:.1f}')
for doc in model.agents_by_type[Doctor]:
    print(f'Doctor {doc.unique_id}: {doc.patients_treated} treated')
"
```

## Sample output

```
Total patients: 73
Discharged: 58
Avg wait time: 4.2
Doctor 1: 21 treated
Doctor 2: 19 treated
Doctor 3: 18 treated
```
