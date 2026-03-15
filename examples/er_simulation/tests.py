from er_simulation.agents import Doctor, Patient
from er_simulation.model import ERModel


def test_patients_are_processed():
    model = ERModel(n_doctors=3, arrival_rate=1.5, seed=42)
    for _ in range(20):
        model.step()

    patients = list(model.agents_by_type[Patient])
    assert len(patients) > 0

    discharged = [p for p in patients if p.status == "discharged"]
    assert len(discharged) > 0


def test_all_doctors_work():
    model = ERModel(n_doctors=3, arrival_rate=2.0, seed=42)
    for _ in range(30):
        model.step()

    for doc in model.agents_by_type[Doctor]:
        assert doc.patients_treated > 0


def test_wait_times_are_positive():
    model = ERModel(n_doctors=2, arrival_rate=1.5, seed=42)
    for _ in range(25):
        model.step()

    discharged = [
        p for p in model.agents_by_type[Patient] if p.status == "discharged"
    ]
    for p in discharged:
        assert p.wait_time >= 0
