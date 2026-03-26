import matplotlib.pyplot as plt
from ultimatum_game.model import UltimatumModel

# Setup and run
model = UltimatumModel(n=1000)
for i in range(1000):
    model.step()

# Retrieve data
data = model.datacollector.get_model_vars_dataframe()

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
data["Accept Rate"].plot(ax=axes[0, 0], title="Accept Rate %")
data["Avg Offer"].plot(ax=axes[0, 1], title="Average Offer")
data["Proposer Avg"].plot(ax=axes[1, 0], title="Proposer Earnings")
data["Responder Avg"].plot(ax=axes[1, 1], title="Responder Earnings")

plt.tight_layout()
plt.show()
