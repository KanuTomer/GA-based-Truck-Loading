---
title: GA-Based Truck Loading
emoji: 🚚
colorFrom: cyan
colorTo: teal
sdk: gradio
app_file: app.py
pinned: false
---

# GA-Based Truck Loading

Portfolio-style visual demo for a genetic-algorithm-based truck loading and route-packing workflow.

This repository is the standalone web-app project for a visual GA-based truck loading demo. App development, commits, deployment, and future merges happen here while the original research prototype remains separate.

## Planned MVP

- Upload or choose a demo dataset.
- Select one of two India-oriented truck classes with a 3D body-style preview.
- Validate customers, boxes, assignments, and container dimensions.
- Run a capped version of the proposed GA model.
- Inspect metrics, routes, and an animated 3D truck-packing visualization.

## Repository Scope

This repo will include only the code needed for the app demo:

- dataset parsing and validation
- proposed GA model runtime
- packing placement logic
- Gradio UI
- 2D/3D visualization helpers

It will not include legacy comparison baselines, historical scripts, paper-reporting outputs, ablation studies, or generated result archives.

## Assets

The truck preview models use selected assets from Kenney Car Kit 3.1, licensed
under Creative Commons Zero (CC0). Credit is not required, but the original
license is included under `assets/kenney-car-kit/License.txt`.

## Development Status

Milestone 5 connects a capped proposed-GA runtime, real rotation-enabled packing
placements, downloadable run artifacts, and an animated procedural 3D truck
loading viewer.

## Running And Hosting

Run locally with:

```powershell
python app.py
```

The app is prepared for Hugging Face Spaces with Gradio SDK metadata in this
README and dependencies in `requirements.txt`. The intended quick visual demo
settings are population `10` and generations `2`; larger runs are available but
may be slower on free CPU hosting. Free Spaces are suitable for this personal
demo, with the expectation that the app can sleep when unused.
