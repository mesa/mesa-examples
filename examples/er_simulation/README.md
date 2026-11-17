# Emergency Room Simulation

This example models a busy emergency room using Mesa's [Action system](https://github.com/mesa/mesa/pull/3461).

In plain language, patients show up over time, get triaged, and then wait for treatment. Some cases are minor and leave after triage. Others need treatment, and critical patients are always prioritized. If a doctor is already treating a moderate patient and a critical case arrives, that ongoing treatment can be interrupted and resumed later.

The goal of this example is not medical realism. It is a compact, easy-to-read model for exploring timed actions, interruption, resumption, and event-driven scheduling in Mesa.

## Why this example is interesting

This model is a nice fit for Mesa's Actions API because an emergency room is full of things that take time:

- triage takes time
- treatment takes time
- patients arrive at random times
- some work can be interrupted
- some work cannot

That makes it a good teaching example for discrete-event behavior inside an agent-based model.

## What the model does

Each run follows the same high-level flow:

1. Patients arrive at random intervals.
2. A free doctor triages the patient, or the patient waits in the triage queue.
3. Triage assigns one of three severities: `critical`, `moderate`, or `minor`.
4. Minor patients leave directly after triage.
5. Critical and moderate patients wait for treatment.
6. Critical patients are treated first.
7. Moderate treatments can be interrupted if a critical patient needs immediate attention.
8. Interrupted moderate treatments are resumed later.

## Mesa features demonstrated

| Feature | How it appears here |
|---------|----------------------|
| `Action` subclassing | `Triage` and `Treat` are both custom actions |
| Timed actions | Triage and treatment both have durations |
| Interruptible actions | Moderate treatment can be bumped by critical arrivals |
| Resumable actions | Interrupted treatment continues later instead of restarting |
| `schedule_event` | Patient arrivals are scheduled using an exponential distribution |
| Priority queues | Critical patients move ahead of moderate patients |
| Data collection | Queue lengths, throughput, interruptions, and wait time are tracked |

## Project structure

| File | Purpose |
|------|---------|
| `er_simulation/model.py` | Main ER model, queues, scheduling, and metrics |
| `er_simulation/agents.py` | Doctor and patient agents plus the `Triage` and `Treat` actions |
| `render_visuals.py` | Generates a PNG or GIF dashboard from a simulation run |
| `tests.py` | Basic checks for processing, waiting times, triage, and interruptions |

## Quick start

From inside this folder:

```bash
pip install -r requirements.txt
```

Then run a simple simulation:

```bash
python -c "
from er_simulation.model import ERModel
from er_simulation.agents import Patient, Doctor

model = ERModel(n_doctors=4, arrival_rate=1.5, seed=11)
for _ in range(40):
    model.step()

patients = list(model.agents_by_type[Patient])
discharged = [p for p in patients if p.status == 'discharged']

print(f'Total patients: {len(patients)}')
print(f'Discharged: {len(discharged)}')
print(f'Triage queue: {model.triage_queue_length}')
print(f'Treatment queue: {model.treatment_queue_length}')
print(f'Interruptions: {model.total_interruptions}')
if discharged:
    avg_wait = sum(p.wait_time for p in discharged) / len(discharged)
    print(f'Avg wait time: {avg_wait:.1f}')
for doc in model.agents_by_type[Doctor]:
    print(f'Doctor {doc.unique_id}: {doc.patients_treated} treated')
"
```

## How to make a visual

If you want something you can attach to a PR, use the renderer:

```bash
python render_visuals.py --steps 40 --n-doctors 4 --arrival-rate 1.5 --seed 11 --output er_snapshot.png
python render_visuals.py --steps 40 --n-doctors 4 --arrival-rate 1.5 --seed 11 --output er_animation.gif --fps 4
```

This produces:

- a static dashboard image showing the final state and recent trends
- an animated GIF showing how queues, throughput, wait time, and doctor activity evolve over time

## Parameters you can play with

These are the main knobs worth changing:

| Parameter | Meaning |
|-----------|---------|
| `n_doctors` | Number of doctors available for triage and treatment |
| `arrival_rate` | How quickly patients arrive on average |
| `seed` | Random seed for reproducible runs |
| `steps` | How long the simulation runs |

Good starter combinations:

- `n_doctors=2, arrival_rate=3.0` for heavy overload
- `n_doctors=4, arrival_rate=1.5` for a balanced run with visible interruptions
- `n_doctors=6, arrival_rate=1.0` for a better-staffed system

## What to look for

Here are a few behaviors newcomers usually find interesting:

- If you keep staffing fixed and raise `arrival_rate`, the triage queue grows fast.
- If you keep `arrival_rate` fixed and add doctors, more patients make it through treatment and the system feels less congested.
- Minor patients help reduce pressure because they leave directly after triage.
- Interruptions are easiest to notice under moderate pressure, where doctors have enough time to begin moderate treatments before a critical case arrives.
- Under extreme overload, the system can become so busy triaging incoming patients that interruptions actually become less visible than you might expect.

## Questions worth exploring

If you are experimenting with the model, these are good prompts:

- When does the main bottleneck shift from triage to treatment?
- How many doctors are needed before queues stop growing rapidly?
- Do interruptions clearly help critical patients, or do they mostly delay moderate ones?
- Which parameter change helps more: lowering arrivals or adding one more doctor?

## Example output

One run with `n_doctors=4`, `arrival_rate=1.5`, `seed=11`, and `40` steps produced:

```text
Total patients: 63
Discharged: 22
Triage queue: 26
Treatment queue: 11
Interruptions: 3
Avg wait time: 16.6
Doctor 1: 2 treated
Doctor 2: 3 treated
Doctor 3: 1 treated
Doctor 4: 2 treated
```

## Notes

- This is a teaching model, not a hospital operations model.
- Severity assignment and service durations are simplified on purpose.
- The same doctors perform both triage and treatment, which creates useful queueing behavior for demonstration.
