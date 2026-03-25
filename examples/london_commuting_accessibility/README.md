---
title: London Commuting ABM
emoji: 🚇
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
license: mit
pinned: false
---

# London Commuting Model

Agent-based simulation of daily commuting patterns in London using Mesa + mesa-geo.
983 MSOA zones, hourly BPR congestion, gravity-model employment accessibility.

## Tabs

- **The Inequality Landscape** — choropleth maps of commute time and accessibility by MSOA
- **How Congestion Amplifies Inequality** — Gini/Palma time series, commute time distribution
- **Who Suffers Most?** — occupation × accessibility breakdown (SOC 1–9)
- **Model Validation** — calibration and validation summary

## Data Sources

| Dataset | Source |
|---|---|
| MSOA boundaries | ONS Geoportal |
| OD travel-to-work flows | Zenodo doi:10.5281/zenodo.13327082 |
| Congestion ratios | TomTom Traffic Index |
| Commute mode (Census 2011) | NOMIS NM_568_1 |
| Occupation proportions (Census 2021) | NOMIS Census 2021 bulk |
| Employment by MSOA (BRES 2024) | NOMIS |

## Run locally

```bash
conda activate mesa-demo
solara run app.py
```
