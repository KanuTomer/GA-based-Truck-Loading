# GA-Based Truck Loading

Portfolio-style visual demo for a genetic-algorithm-based truck loading and route-packing workflow.

This repository is the standalone web-app project derived from the dissertation work in `Dissertation-3L-SDVRP`. The dissertation repository is treated as read-only source material; app development, commits, deployment, and future merges happen here.

## Planned MVP

- Upload or choose a demo dataset.
- Select an India-oriented truck/container preset.
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

It will not include dissertation baselines, historical scripts, paper-reporting outputs, ablation studies, or generated result archives.

## Development Status

Milestone 0 scaffold is in place. Solver code and app functionality will be added in later milestones.

