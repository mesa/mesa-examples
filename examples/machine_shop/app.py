import solara
from machine_shop.model import MachineShop
from mesa.visualization import SolaraViz
from mesa.visualization.utils import update_counter


@solara.component
def machine_shop_status(model):
    """Display the current state of the machine and its production job."""
    update_counter.get()

    machine = model.machine
    action = machine.current_action

    if machine.is_broken:
        status = "Broken"
    elif machine.current_action is not None:
        status = "Operating"
    else:
        status = "Idle"

    activity = "Idle" if action is None else action.name

    progress = model.production.progress
    percentage = int(progress * 100)

    filled = int(progress * 20)
    progress_bar = "█" * filled + "░" * (20 - filled)

    solara.Markdown(
        f"""
## Machine Shop

**Machine status:** {status}

**Current activity:** {activity}

**Simulation time:** {model.time:.1f}

### Production Progress

`{progress_bar}` {percentage}%
"""
    )


model = MachineShop()

page = SolaraViz(
    model,
    components=[machine_shop_status],
    name="Machine Shop",
)

page  # noqa
