import matplotlib.pyplot as plt
from disease_on_network.model import IllnessModel

## With link dynamics

print("###### Starting Simulation with link dynamics active ######")

ModelDynamic = IllnessModel(
    num_nodes=500,
    avg_degree=8,
    p_transmission=0.2,
    p_recovery=0.1,
    p_mortality=0.05,
    initial_infected=5,
    link_dynamics=True,
    seed=None,
)

for _ in range(150):
    inf = ModelDynamic.datacollector.get_model_vars_dataframe()["Infected"].iloc[-1]
    dead = ModelDynamic.datacollector.get_model_vars_dataframe()["Dead"].iloc[-1]
    print(f"Step {ModelDynamic.steps}: Infected count = {inf}, Death count = {dead}")

    if inf == 0:
        break
    ModelDynamic.step()


## Without link dynamics

print("\n\n###### Starting Simulation with link dynamics inactive ######")

ModelStatic = IllnessModel(
    num_nodes=500,
    avg_degree=8,
    p_transmission=0.2,
    p_recovery=0.1,
    p_mortality=0.05,
    initial_infected=5,
    link_dynamics=False,
    seed=None,
)

for _ in range(150):
    inf = ModelStatic.datacollector.get_model_vars_dataframe()["Infected"].iloc[-1]
    dead = ModelStatic.datacollector.get_model_vars_dataframe()["Dead"].iloc[-1]
    print(f"Step {ModelStatic.steps}: Infected count = {inf}, Death count = {dead}")

    if inf == 0:
        break
    ModelStatic.step()


## Plot the results

fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))


PercentStatic = (
    ModelStatic.datacollector.get_model_vars_dataframe()["Infected"]
    / ModelStatic.num_nodes
)
PercentDynamic = (
    ModelDynamic.datacollector.get_model_vars_dataframe()["Infected"]
    / ModelDynamic.num_nodes
)

PercentStatic.plot(ax=ax1, label="Without link dynamics", linewidth=2)
PercentDynamic.plot(ax=ax1, label="With link dynamics", linewidth=2)

ax1.set_title("Comparison between fraction of Infected", fontsize=14, pad=15)
ax1.set_xlabel("Time steps", fontsize=12)
ax1.set_ylabel("Fraction of Infected", fontsize=12)
ax1.legend()
ax1.grid(True)

PercentStatic = (
    ModelStatic.datacollector.get_model_vars_dataframe()["Dead"] / ModelStatic.num_nodes
)
PercentDynamic = (
    ModelDynamic.datacollector.get_model_vars_dataframe()["Dead"]
    / ModelDynamic.num_nodes
)

PercentStatic.plot(ax=ax2, label="Without link dynamics", linewidth=2)
PercentDynamic.plot(ax=ax2, label="With link dynamics", linewidth=2)

ax2.set_title("Comparison between fraction of Deaths", fontsize=14, pad=15)
ax2.set_xlabel("Time steps", fontsize=12)
ax2.set_ylabel("Fraction of Deaths", fontsize=12)
ax2.grid(True)


plt.tight_layout()
plt.show()
