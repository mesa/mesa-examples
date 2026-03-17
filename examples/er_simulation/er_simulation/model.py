"""Emergency room simulation using Mesa's Action system."""

import mesa
import numpy as np

from .agents import Doctor, Patient, Treat, Triage


class ERModel(mesa.Model):
    """Discrete-event ER simulation with stochastic patient arrivals."""

    def __init__(self, n_doctors=3, arrival_rate=1.5, seed=42):
        super().__init__()
        self.rng = np.random.default_rng(seed)
        self.arrival_rate = arrival_rate
        self._queue = []

        for _ in range(n_doctors):
            Doctor(self)

        self._schedule_arrival()

    def _schedule_arrival(self):
        gap = self.rng.exponential(1.0 / self.arrival_rate)
        self.schedule_event(self._on_arrival, at=self.time + gap)

    def _on_arrival(self):
        patient = Patient(self, arrival_time=self.time)

        nurse = self._get_free_doctor()
        if nurse:
            nurse.start_action(Triage(nurse, patient))
        else:
            self._queue.append(patient)

        self._schedule_arrival()

    def enqueue_patient(self, patient):
        self._queue.append(patient)
        self._queue.sort(
            key=lambda p: (
                {"critical": 0, "moderate": 1, "minor": 2}.get(p.severity, 3),
                p.arrival_time,
            )
        )
        self._assign_waiting()

    def try_assign(self, doctor):
        if self._queue and not doctor.is_busy:
            patient = self._queue.pop(0)
            doctor.start_action(Treat(doctor, patient))

    def _assign_waiting(self):
        for doc in self.agents_by_type[Doctor]:
            if not doc.is_busy and self._queue:
                patient = self._queue.pop(0)
                doc.start_action(Treat(doc, patient))

    def _get_free_doctor(self):
        free = [d for d in self.agents_by_type[Doctor] if not d.is_busy]
        return self.rng.choice(free) if free else None

    def step(self):
        self.run_for(1.0)
        self._assign_waiting()
