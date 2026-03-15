"""Actions and agents for the ER simulation."""

import mesa
import numpy as np
from mesa.experimental.actions import Action


class Triage(Action):
    """Assess a patient's severity and route them accordingly."""

    def __init__(self, nurse, patient):
        dur = max(0.5, nurse.model.rng.normal(1.5, 0.3))
        super().__init__(nurse, duration=dur)
        self.patient = patient

    def on_complete(self):
        severity = self.agent.model.rng.choice(
            ["critical", "moderate", "minor"], p=[0.15, 0.45, 0.4]
        )
        self.patient.severity = severity
        self.patient.status = "triaged"

        if severity == "minor":
            self.patient.status = "discharged"
            self.patient.discharge_time = self.agent.model.time
            return

        self.agent.model.enqueue_patient(self.patient)


class Treat(Action):
    """Treat a patient; duration depends on severity."""

    DURATIONS = {"critical": 12.0, "moderate": 6.0, "minor": 2.0}

    def __init__(self, doctor, patient):
        base = self.DURATIONS.get(patient.severity, 4.0)
        dur = max(1.0, doctor.model.rng.normal(base, base * 0.2))
        super().__init__(
            doctor,
            duration=dur,
            interruptible=(patient.severity != "critical"),
        )
        self.patient = patient

    def on_start(self):
        self.agent.current_patient = self.patient
        self.patient.status = "being_treated"

    def on_complete(self):
        self.patient.status = "discharged"
        self.patient.discharge_time = self.agent.model.time
        self.agent.patients_treated += 1
        self.agent.current_patient = None
        self.agent.model.try_assign(self.agent)

    def on_interrupt(self, progress):
        self.patient.status = "waiting"
        self.agent.current_patient = None
        self.agent.model.enqueue_patient(self.patient)

    def on_resume(self):
        self.agent.current_patient = self.patient
        self.patient.status = "being_treated"


class Patient(mesa.Agent):
    """A patient arriving in the ER."""

    def __init__(self, model, arrival_time):
        super().__init__(model)
        self.arrival_time = arrival_time
        self.discharge_time = None
        self.severity = None
        self.status = "arrived"

    @property
    def wait_time(self):
        end = self.discharge_time if self.discharge_time else self.model.time
        return end - self.arrival_time


class Doctor(mesa.Agent):
    """A doctor who treats patients."""

    def __init__(self, model):
        super().__init__(model)
        self.patients_treated = 0
        self.current_patient = None
