# Hierarchical Organization Model

Category: Organizational Modeling
Focus: Meta-Agent Hierarchies & Activation Semantics
Mesa Version: >=3.0
Visualization: SolaraViz

## Overview

This example demonstrates a three-level hierarchical agent system:

Employees → Departments → Organization

The model intentionally avoids legacy scheduler patterns and uses explicit activation ordering to remain compatible with Mesa 3.x.

## Why This Example Matters

While building this model in a clean environment, several friction points became apparent:

- Removal of legacy schedulers (RandomActivation)
- Agent constructor changes in Mesa 3.x
- Implicit visualization dependencies
- Lack of documented activation best practices

This example is structured to be:

- Reproducible
- Explicit in dependency requirements
- Clear in activation semantics
- Compatible with modern Mesa visualization

## Features

- Hierarchical meta-agent structure
- Organizational policy intervention
- External shock events
- System resilience dynamics
- Explicit dependency isolation

## Run Instructions

1. Create virtual environment
2. pip install -r requirements.txt
3. python -m solara run app.py