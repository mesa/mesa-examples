import numpy as np
import pandas as pd
from scipy.stats import qmc
from sklearn.ensemble import RandomForestRegressor

from .model import WealthModel


def sample_parameters(param_space, n_samples, seed=None):
    """Generates parameter sets using Latin Hypercube Sampling."""
    dim = len(param_space)
    sampler = qmc.LatinHypercube(d=dim, seed=seed)
    sample = sampler.random(n=n_samples)

    l_bounds = [v[0] for v in param_space.values()]
    u_bounds = [v[1] for v in param_space.values()]
    scaled_samples = qmc.scale(sample, l_bounds, u_bounds)

    param_names = list(param_space.keys())
    is_int = [isinstance(v[0], int) for v in param_space.values()]

    output = []
    for j in range(n_samples):
        config = {
            param_names[i]: round(scaled_samples[j, i])
            if is_int[i]
            else scaled_samples[j, i]
            for i in range(dim)
        }
        output.append(config)
    return output


param_space = {"n": (10, 100), "width": (10, 30), "height": (10, 30)}
param_names = list(param_space.keys())
samples = sample_parameters(param_space, n_samples=30, seed=42)

print("Running simulations for training data...")
results = []
for config in samples:
    model = WealthModel(**config)
    for _ in range(50):
        model.step()

    results.append({**config, "Gini": model.get_gini()})

df = pd.DataFrame(results)
X = df[param_names].values
y = df["Gini"].values

surrogate = RandomForestRegressor(n_estimators=100, random_state=42)
surrogate.fit(X, y)
print("Surrogate model trained.")

test_params = {"n": 65, "width": 22, "height": 22}
X_test = np.array([[test_params[p] for p in param_names]])
prediction = surrogate.predict(X_test)[0]

print(f"\nPrediction for {test_params}:")
print(f"Approximated Gini: {prediction:.4f}")
