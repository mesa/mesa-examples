"""ML optimization demo - Gaussian Process regression for finding good parameters."""
from .model import (
    MLDemoModel,
    run_optimization,
    run_statistical_validation,
    run_full_analysis,
    visualize_optimization
)
from .agents import SimpleAgent
__all__=[
    "MLDemoModel",
    "SimpleAgent",
    "run_optimization",
    "run_statistical_validation",
    "run_full_analysis",
    "visualize_optimization"
]