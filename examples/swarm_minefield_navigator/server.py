"""Mesa visualization server for the swarm minefield mapping example."""

from __future__ import annotations

import socket

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.visualization.UserParam import Slider, StaticText

if __package__:
    from .agents import (
        FINAL_PATH,
        MINE,
        SAFE,
        UNSAFE_BUFFER,
        CheckpointAgent,
        DeadEndAgent,
        DroneAgent,
        KnowledgeCellAgent,
        MineAgent,
    )
    from .model import MinefieldModel
else:  # pragma: no cover - direct script compatibility
    from agents import (
        FINAL_PATH,
        MINE,
        SAFE,
        UNSAFE_BUFFER,
        CheckpointAgent,
        DeadEndAgent,
        DroneAgent,
        KnowledgeCellAgent,
        MineAgent,
    )
    from model import MinefieldModel


def find_available_port(start_port: int = 8521, attempts: int = 20) -> int:
    """Return the first available localhost port from a small search range."""
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                candidate.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise OSError(
        f"No available port found between {start_port} and {start_port + attempts - 1}"
    )


def portrayal(agent):
    """Render drones, discovered mines, and the shared knowledge base."""
    if isinstance(agent, DroneAgent):
        if agent.role == "LEADER":
            color = "#8A2BE2"
            radius = 0.9
            layer = 4
            text = "L"
        else:
            color = (
                "Orange"
                if agent.state == "RALLYING" and agent.safety_override
                else "DeepSkyBlue"
            )
            radius = 0.7
            layer = 3
            text = "R" if agent.state == "RALLYING" and agent.safety_override else "F"
        return {
            "Shape": "circle",
            "Color": color,
            "Filled": "true",
            "Layer": layer,
            "r": radius,
            "text": text,
            "text_color": "white",
        }

    if isinstance(agent, MineAgent):
        return {
            "Shape": "rect",
            "Color": (
                "DarkRed"
                if agent.model.knowledge_base.get(agent.pos) == MINE
                else "Orange"
            ),
            "Filled": "true",
            "Layer": 2,
            "w": 0.8,
            "h": 0.8,
        }

    if isinstance(agent, CheckpointAgent):
        return {
            "Shape": "rect",
            "Color": "LightBlue",
            "Filled": "true",
            "Layer": 1,
            "w": 0.6,
            "h": 0.6,
        }

    if isinstance(agent, DeadEndAgent):
        return {
            "Shape": "rect",
            "Color": "DimGray",
            "Filled": "true",
            "Layer": 0,
            "w": 0.5,
            "h": 0.5,
        }

    if isinstance(agent, KnowledgeCellAgent):
        if agent.cell_state == SAFE:
            return {
                "Shape": "circle",
                "Color": "LightGreen",
                "Filled": "true",
                "Layer": 0,
                "r": 0.2,
            }
        if agent.cell_state == UNSAFE_BUFFER:
            return {
                "Shape": "rect",
                "Color": "LightPink",
                "Filled": "true",
                "Layer": 0,
                "w": 1.0,
                "h": 1.0,
            }
        if agent.cell_state == FINAL_PATH:
            return {
                "Shape": "rect",
                "Color": "#003B8E",
                "Filled": "true",
                "Layer": 2,
                "w": 1.0,
                "h": 1.0,
            }

    return None


class StatusText(TextElement):
    """Display swarm metrics above the grid."""

    def render(self, model):
        batteries = " | ".join(
            f"D{index + 1}: {agent.battery}"
            for index, agent in enumerate(model.iter_drones())
        )
        final_path_cells = len(model.final_path)
        elapsed_seconds = model.get_elapsed_seconds()
        return (
            "<div style='font-family:Segoe UI, sans-serif; padding:10px 12px; "
            "background:#0f172a; color:#e2e8f0; border-radius:10px; "
            "margin-bottom:10px;'>"
            f"<div style='font-size:18px; font-weight:700;'>Swarm Minefield Mapper</div>"
            f"<div style='margin-top:6px;'><strong>Status:</strong> {model.path_status}</div>"
            f"<div><strong>Elapsed Time:</strong> {elapsed_seconds:.2f} seconds</div>"
            f"<div><strong>Formation Ready:</strong> {model.formation_ready}</div>"
            f"<div><strong>Mines Discovered:</strong> {len(model.discovered_mines)}</div>"
            f"<div><strong>Cells Explored:</strong> {len(model.scanned_cells)}</div>"
            f"<div><strong>Final Path Cells:</strong> {final_path_cells}</div>"
            f"<div><strong>Battery Levels:</strong> {batteries}</div>"
            "</div>"
        )


grid = CanvasGrid(portrayal, 100, 100, 700, 700)
status = StatusText()
model_params = {
    "width": 100,
    "height": 100,
    "drone_count": 4,
    "seed": None,
    "reset_hint": StaticText(
        "<b>Reset Mines:</b> use Mesa's built-in <b>Reset</b> control to reroll a new field."
    ),
    "num_mines": Slider("Total Cluster Mines", 300, 50, 500, 25),
    "drone_1_x": Slider("Drone 1 X", 40, 0, 99, 1),
    "drone_2_x": Slider("Drone 2 X", 45, 0, 99, 1),
    "drone_3_x": Slider("Drone 3 X", 50, 0, 99, 1),
    "drone_4_x": Slider("Drone 4 X", 55, 0, 99, 1),
}

server = ModularServer(
    MinefieldModel,
    [status, grid],
    "Autonomous Swarm Drone Minefield Mapping",
    model_params,
)

server.port = find_available_port()


if __name__ == "__main__":
    server.launch()
