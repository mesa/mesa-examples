"""ML optimization demo - Gaussian Process regression for finding good parameters."""

from .agents import SimpleAgent
from .model import (
    MLDemoModel,
    run_full_analysis,
    run_optimization,
    run_statistical_validation,
    visualize_optimization,
)

__all__ = [
    "MLDemoModel",
    "SimpleAgent",
    "run_full_analysis",
    "run_optimization",
    "run_statistical_validation",
    "visualize_optimization",
]
