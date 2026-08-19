from rumor_mill.model import RumorMillModel

m = RumorMillModel(10, 10, 0.1, 0.5, True, 1)
print("recovery_rate (should be default 0.0, NOT True):", m.recovery_rate)

m_a = RumorMillModel(10, 10, 0.1, 0.5, True, 1)
m_b = RumorMillModel(10, 10, 0.1, 0.5, True, 1)
seq_a = [m_a.random.random() for _ in range(5)]
seq_b = [m_b.random.random() for _ in range(5)]
print("seed reproducibility (should match):", seq_a == seq_b)
