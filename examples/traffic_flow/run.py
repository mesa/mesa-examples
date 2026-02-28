from traffic_flow.model import TraficFlow


def render_grid(model):
    lines = []
    for y in reversed(range(model.grid.height)):
        row = []
        for x in range(model.grid.width):
            cell_agents = model.grid.get_cell_list_contents((x, y))
            row.append("C" if cell_agents else ".")
        lines.append("".join(row))
    return "\n".join(lines)


if __name__ == "__main__":
    model = TraficFlow(width=20, height=5, n_cars=20, seed=1)

    for t in range(10):
        print(f"tick {t}")
        print(render_grid(model))
        print()
        model.step()
