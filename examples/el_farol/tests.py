import numpy as np
from el_farol.model import ElFarolBar

np.random.seed(1)
crowd_threshold = 60


def test_convergence():
    # Testing that the attendance converges to crowd_threshold
    attendances = []
    for _ in range(10):
        model = ElFarolBar(num_agents=100, crowd_threshold=crowd_threshold, memory_size=10)
        for _ in range(100):
            model.step()
        attendances.append(model.attendance)
    mean = np.mean(attendances)
    standard_deviation = np.std(attendances)
    deviation = abs(mean - crowd_threshold)
    assert deviation < standard_deviation
