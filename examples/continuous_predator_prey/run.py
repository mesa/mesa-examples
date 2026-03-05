# attempt to import the model by name; this works both when the
# script is executed directly and when the package is imported by tests.
try:
    from model import PredatorPreyModel
except ImportError:
    from examples.continuous_predator_prey.model import PredatorPreyModel

# here models initiated

model = PredatorPreyModel(width=100, height=100, initial_prey=50, initial_predators=10)

# checking for 50 steps of the simulation
for i in range(50):
    model.step()
    # fetches latest data
    data = model.data_collector.get_model_vars_dataframe().iloc[
        -1
    ]  # it gets the latest data from the data collector for the current step of the simulation

    # it prints the number of prey and predators alive in the current step of the simulation
    print(
        f"step{i + 1}: Prey={data['Prey']},Prey,{int(data['Predators'])} Predators alive"
    )
print("done")
