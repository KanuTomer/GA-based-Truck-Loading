"""Gradio entry point for the GA-Based Truck Loading demo."""

from __future__ import annotations

import gradio as gr

from truck_loading.presets import format_dimensions, get_preset, preset_names


CUSTOM_CSS = """
:root {
    --bg-ink: #111417;
    --panel: #171b20;
    --panel-soft: #20262d;
    --line: rgba(255, 255, 255, 0.12);
    --text-main: #f4f7f9;
    --text-muted: #9da8b2;
    --teal: #22d3c5;
    --amber: #f7c948;
    --coral: #ff6b5f;
    --steel: #8aa0b4;
}

body,
gradio-app {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}

.gradio-container {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 1480px !important;
    margin: 0 auto !important;
    overflow-x: hidden !important;
    background:
        linear-gradient(135deg, rgba(34, 211, 197, 0.08), transparent 36%),
        linear-gradient(180deg, #f6f7f2 0%, #e9edf0 48%, #dde4e8 100%) !important;
    color: #1c252c;
}

.main,
main,
.wrap,
.contain,
.row,
.column {
    max-width: 100% !important;
    min-width: 0 !important;
}

.app-shell,
.app-shell * {
    box-sizing: border-box;
}

.app-shell {
    width: 100%;
    max-width: 100%;
    padding: 18px;
}

.hero {
    background: #111417;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 28px;
    color: var(--text-main);
    box-shadow: 0 24px 60px rgba(17, 20, 23, 0.22);
}

.hero-kicker {
    color: var(--teal);
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.hero-title {
    margin: 10px 0 8px;
    font-size: clamp(2.4rem, 5vw, 4.8rem);
    line-height: 0.95;
    letter-spacing: 0;
}

.hero-copy {
    max-width: 850px;
    color: #d6dde3;
    font-size: 1.06rem;
    line-height: 1.55;
}

.hero-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 24px;
}

.strip-item {
    min-height: 74px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.055);
    border-radius: 10px;
    padding: 12px;
}

.strip-label {
    color: var(--text-muted);
    font-size: 0.78rem;
}

.strip-value {
    margin-top: 6px;
    color: var(--text-main);
    font-size: 1rem;
    font-weight: 800;
}

.control-panel,
.result-panel,
.stage-panel {
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.78);
    box-shadow: 0 18px 50px rgba(35, 47, 58, 0.12);
    padding: 16px;
}

.control-panel,
.result-panel,
.control-panel label,
.result-panel label,
.control-panel p,
.result-panel p,
.control-panel h2,
.control-panel h3,
.result-panel h2,
.result-panel h3,
.control-panel table,
.result-panel table,
.control-panel td,
.control-panel th,
.result-panel td,
.result-panel th {
    color: #1c252c !important;
}

.stage-panel {
    background: var(--bg-ink);
    color: var(--text-main);
    overflow: hidden;
}

.stage-shell {
    position: relative;
    min-height: 460px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background:
        linear-gradient(160deg, rgba(34, 211, 197, 0.12), transparent 26%),
        linear-gradient(340deg, rgba(247, 201, 72, 0.09), transparent 28%),
        #101418;
    overflow: hidden;
}

.stage-grid {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.055) 1px, transparent 1px);
    background-size: 42px 42px;
    transform: perspective(900px) rotateX(58deg) translateY(120px);
    transform-origin: 50% 100%;
}

.truck-outline {
    position: absolute;
    left: 9%;
    right: 9%;
    top: 27%;
    height: 230px;
    border: 2px solid rgba(34, 211, 197, 0.72);
    border-radius: 12px;
    box-shadow: inset 0 0 42px rgba(34, 211, 197, 0.08), 0 0 34px rgba(34, 211, 197, 0.12);
}

.cab {
    position: absolute;
    right: 4%;
    top: 39%;
    width: 72px;
    height: 105px;
    border: 2px solid rgba(247, 201, 72, 0.76);
    border-radius: 10px 22px 22px 10px;
    background: rgba(247, 201, 72, 0.08);
}

.box-stack {
    position: absolute;
    left: 14%;
    bottom: 30%;
    display: grid;
    grid-template-columns: repeat(5, 58px);
    gap: 8px;
}

.demo-box {
    height: 42px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.22);
}

.demo-box:nth-child(1),
.demo-box:nth-child(6) { background: #22d3c5; }
.demo-box:nth-child(2),
.demo-box:nth-child(7) { background: #f7c948; }
.demo-box:nth-child(3),
.demo-box:nth-child(8) { background: #ff6b5f; }
.demo-box:nth-child(4),
.demo-box:nth-child(9) { background: #8aa0b4; }
.demo-box:nth-child(5),
.demo-box:nth-child(10) { background: #78d979; }

.stage-caption {
    position: absolute;
    left: 22px;
    bottom: 20px;
    max-width: 540px;
}

.stage-caption h2 {
    color: var(--text-main);
    font-size: 1.45rem;
    margin: 0 0 8px;
}

.stage-caption p {
    color: #c7d0d8;
    margin: 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}

.metric-card {
    min-height: 94px;
    background: #ffffff;
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
    padding: 14px;
}

.metric-label {
    color: #677482;
    font-size: 0.76rem;
    text-transform: uppercase;
    font-weight: 800;
}

.metric-value {
    margin-top: 8px;
    color: #151b20;
    font-size: 1.45rem;
    font-weight: 900;
}

.metric-note {
    margin-top: 3px;
    color: #7c8995;
    font-size: 0.82rem;
}

.placeholder-chart {
    min-height: 180px;
    border-radius: 12px;
    border: 1px dashed rgba(17, 20, 23, 0.18);
    background:
        linear-gradient(90deg, rgba(34, 211, 197, 0.2) 0 18%, transparent 18% 100%),
        linear-gradient(90deg, rgba(247, 201, 72, 0.24) 0 40%, transparent 40% 100%),
        linear-gradient(90deg, rgba(255, 107, 95, 0.18) 0 62%, transparent 62% 100%),
        linear-gradient(90deg, rgba(138, 160, 180, 0.2) 0 76%, transparent 76% 100%);
    background-size: 100% 32px;
    background-position: 0 24px, 0 70px, 0 116px, 0 162px;
    background-repeat: no-repeat;
}

@media (max-width: 900px) {
    .hero-strip,
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .box-stack {
        grid-template-columns: repeat(3, 50px);
    }
}

@media (max-width: 640px) {
    .app-shell {
        padding: 10px;
    }

    .hero {
        padding: 20px;
    }

    .hero-strip,
    .metric-grid {
        grid-template-columns: 1fr;
    }

    .stage-shell {
        min-height: 360px;
    }

    .truck-outline {
        left: 6%;
        right: 12%;
    }

    .box-stack {
        grid-template-columns: repeat(2, 48px);
        left: 12%;
    }
}
"""


def dataset_helper(source: str) -> str:
    if source == "Upload dataset":
        return (
            "### Upload dataset\n"
            "Accepted in later milestones: internal 3L-SDVRP JSON or VRP file. "
            "This shell keeps the upload control visible without parsing files yet."
        )
    return (
        "### Demo dataset\n"
        "A curated small demo dataset will be bundled in a later milestone for instant playback."
    )


def update_dataset_source(source: str):
    return dataset_helper(source), gr.update(visible=source == "Upload dataset")


def update_truck_preset(name: str):
    preset = get_preset(name)
    return format_dimensions(name), gr.update(visible=preset.is_custom)


def run_placeholder(source: str, truck_name: str, custom_l: float, custom_w: float, custom_h: float) -> str:
    preset = get_preset(truck_name)
    if preset.is_custom:
        dims = f"{int(custom_l or 0):,} x {int(custom_w or 0):,} x {int(custom_h or 0):,} mm"
    else:
        dims = f"{preset.length_mm:,} x {preset.width_mm:,} x {preset.height_mm:,} mm"

    return (
        f"### Proposed GA run queued for a later milestone\n"
        f"Dataset source: **{source}**\n\n"
        f"Truck profile: **{truck_name}** ({dims})\n\n"
        "Validation, solver execution, and 3D loading animation are intentionally placeholders in M1."
    )


def hero_html() -> str:
    return """
    <section class="hero">
        <div class="hero-kicker">Visual optimization demo</div>
        <h1 class="hero-title">GA-Based Truck Loading</h1>
        <p class="hero-copy">
            A cinematic interface for showing how a proposed genetic algorithm turns customer
            routes into physically packed truck loads.
        </p>
        <div class="hero-strip">
            <div class="strip-item">
                <div class="strip-label">Dataset</div>
                <div class="strip-value">Demo or upload</div>
            </div>
            <div class="strip-item">
                <div class="strip-label">Truck</div>
                <div class="strip-value">India presets</div>
            </div>
            <div class="strip-item">
                <div class="strip-label">Model</div>
                <div class="strip-value">Proposed GA only</div>
            </div>
            <div class="strip-item">
                <div class="strip-label">Payoff</div>
                <div class="strip-value">3D packed load</div>
            </div>
        </div>
    </section>
    """


def stage_html() -> str:
    boxes = "".join('<div class="demo-box"></div>' for _ in range(10))
    return f"""
    <div class="stage-shell">
        <div class="stage-grid"></div>
        <div class="truck-outline"></div>
        <div class="cab"></div>
        <div class="box-stack">{boxes}</div>
        <div class="stage-caption">
            <h2>Truck loading stage</h2>
            <p>
                The live Three.js truck scene arrives after dataset validation and placement data
                are connected. This panel reserves the visual center of the product now.
            </p>
        </div>
    </div>
    """


def metrics_html() -> str:
    cards = [
        ("Best score", "Pending", "Calculated after proposed GA run"),
        ("Packed boxes", "Pending", "Loaded from route placements"),
        ("Fill rate", "Pending", "Shown per selected truck route"),
        ("Runtime", "Pending", "Capped for hosted demo"),
    ]
    items = "\n".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """
        for label, value, note in cards
    )
    return f'<div class="metric-grid">{items}</div>'


def build_app() -> gr.Blocks:
    with gr.Blocks(title="GA-Based Truck Loading") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(hero_html())

            with gr.Row(equal_height=False):
                with gr.Column(scale=1, min_width=300, elem_classes=["control-panel"]):
                    gr.Markdown("## Control deck")
                    dataset_source = gr.Radio(
                        choices=["Demo dataset", "Upload dataset"],
                        value="Demo dataset",
                        label="Dataset source",
                    )
                    upload_file = gr.File(
                        label="Dataset file",
                        file_types=[".json", ".vrp"],
                        visible=False,
                    )
                    dataset_status = gr.Markdown(dataset_helper("Demo dataset"))

                    truck_preset = gr.Dropdown(
                        choices=preset_names(),
                        value="Tata 407 Type",
                        label="Truck preset",
                    )
                    truck_dimensions = gr.Markdown(format_dimensions("Tata 407 Type"))

                    with gr.Group(visible=False) as custom_dimensions:
                        gr.Markdown("### Custom internal dimensions")
                        custom_length = gr.Number(value=4000, label="Length mm", precision=0)
                        custom_width = gr.Number(value=1800, label="Width mm", precision=0)
                        custom_height = gr.Number(value=1800, label="Height mm", precision=0)

                    gr.Textbox(
                        value="Proposed packing-aware genetic algorithm",
                        label="Model",
                        interactive=False,
                    )

                    with gr.Row():
                        pop_size = gr.Slider(
                            20,
                            100,
                            value=40,
                            step=10,
                            label="Population",
                            interactive=False,
                        )
                        generations = gr.Slider(
                            10,
                            100,
                            value=50,
                            step=10,
                            label="Generations",
                            interactive=False,
                        )

                    run_button = gr.Button("Prepare visual run", variant="primary")
                    run_status = gr.Markdown(
                        "### Ready\nChoose a dataset source and truck profile to preview the M1 flow."
                    )

                with gr.Column(scale=2, min_width=300, elem_classes=["stage-panel"]):
                    gr.HTML(stage_html())

            with gr.Column(elem_classes=["result-panel"]):
                gr.Markdown("## Result preview")
                metric_cards = gr.HTML(metrics_html())
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Convergence preview")
                        gr.HTML('<div class="placeholder-chart"></div>')
                    with gr.Column(scale=1):
                        gr.Markdown("### Route summary")
                        gr.Dataframe(
                            headers=["Route", "Distance", "Packed Boxes", "Fill", "Status"],
                            value=[
                                ["Route 1", "Pending", "Pending", "Pending", "Awaiting run"],
                                ["Route 2", "Pending", "Pending", "Pending", "Awaiting run"],
                            ],
                            interactive=False,
                            wrap=True,
                        )
                gr.Markdown(
                    "Downloads for normalized dataset, result JSON, and metrics CSV arrive with the execution milestone."
                )

        dataset_source.change(
            fn=update_dataset_source,
            inputs=dataset_source,
            outputs=[dataset_status, upload_file],
        )
        truck_preset.change(
            fn=update_truck_preset,
            inputs=truck_preset,
            outputs=[truck_dimensions, custom_dimensions],
        )
        run_button.click(
            fn=run_placeholder,
            inputs=[dataset_source, truck_preset, custom_length, custom_width, custom_height],
            outputs=run_status,
        )

    return demo


if __name__ == "__main__":
    build_app().launch(
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(primary_hue="cyan", secondary_hue="amber"),
    )
