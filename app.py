"""Gradio entry point for the GA-Based Truck Loading demo."""

from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import gradio as gr

from truck_loading.presets import (
    ASSET_ROOT,
    default_variant_name,
    format_dimensions,
    get_preset,
    model_path_for,
    preset_names,
    preview_path_for,
    variant_names,
)


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

.gradio-container .prose {
    font-size: 0.96rem;
    line-height: 1.5;
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

.main-workspace {
    align-items: stretch;
    flex-wrap: wrap !important;
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
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.86);
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
.result-panel th,
.control-panel strong,
.result-panel strong,
.control-panel .prose strong,
.result-panel .prose strong {
    color: #1c252c !important;
}

.control-panel .prose p,
.control-panel .prose li,
.control-panel .prose table,
.result-panel .prose p,
.result-panel .prose li,
.result-panel .prose table {
    font-size: 0.9rem !important;
    line-height: 1.48 !important;
}

.control-panel .prose h2,
.control-panel .prose h3,
.result-panel .prose h2,
.result-panel .prose h3 {
    margin-top: 0.2rem !important;
    margin-bottom: 0.55rem !important;
}

.truck-details,
.run-status {
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
    background: #f9fbfb;
    padding: 12px;
}

.truck-details table {
    margin-top: 0.65rem !important;
}

.stage-panel {
    background: var(--bg-ink);
    color: var(--text-main);
    overflow: hidden;
}

.stage-panel label,
.stage-panel h2,
.stage-panel h3,
.stage-panel p {
    color: var(--text-main) !important;
}

.truck-card-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin: 12px 0 14px;
}

.truck-card {
    min-height: 214px;
    border: 1px solid rgba(17, 20, 23, 0.12);
    border-radius: 12px;
    padding: 12px;
    background:
        linear-gradient(145deg, rgba(34, 211, 197, 0.11), transparent 44%),
        linear-gradient(320deg, rgba(247, 201, 72, 0.14), transparent 36%),
        #ffffff;
    box-shadow: 0 14px 32px rgba(35, 47, 58, 0.1);
    overflow: hidden;
}

.truck-card.is-selected {
    border-color: rgba(34, 211, 197, 0.82);
    box-shadow: 0 16px 38px rgba(34, 211, 197, 0.18);
}

.truck-card-visuals {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}

.truck-thumb {
    display: grid;
    min-height: 82px;
    place-items: center;
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 10px;
    background:
        radial-gradient(circle at 50% 18%, rgba(34, 211, 197, 0.18), transparent 42%),
        #eff4f5;
}

.truck-thumb img {
    width: 64px;
    height: 64px;
    object-fit: contain;
    image-rendering: auto;
    filter: drop-shadow(0 12px 14px rgba(17, 20, 23, 0.18));
}

.truck-card-kicker {
    color: #51616f;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
}

.truck-card-title {
    margin-top: 8px;
    color: #141a1f;
    font-size: 1.05rem;
    font-weight: 900;
}

.truck-card-dims {
    margin-top: 8px;
    color: #556471;
    font-size: 0.86rem;
    line-height: 1.35;
}

.truck-card-bodies {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
}

.body-chip {
    border: 1px solid rgba(17, 20, 23, 0.12);
    border-radius: 999px;
    padding: 4px 8px;
    background: #eef4f5;
    color: #26333c;
    font-size: 0.72rem;
    font-weight: 800;
}

.truck-class-radio,
.body-style-radio {
    margin-top: 8px;
}

.model-stage {
    position: relative;
    min-height: 630px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background:
        radial-gradient(circle at 74% 22%, rgba(247, 201, 72, 0.18), transparent 22%),
        linear-gradient(160deg, rgba(34, 211, 197, 0.16), transparent 28%),
        linear-gradient(340deg, rgba(255, 107, 95, 0.1), transparent 30%),
        #101418;
    overflow: hidden;
    padding: 18px;
}

.model-stage-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 12px;
}

.model-stage-kicker {
    color: var(--teal);
    font-size: 0.76rem;
    font-weight: 900;
    text-transform: uppercase;
}

.model-stage-title {
    margin-top: 6px;
    color: var(--text-main);
    font-size: 1.55rem;
    font-weight: 900;
}

.model-stage-copy {
    max-width: 690px;
    color: #c7d0d8;
    line-height: 1.45;
}

.model-pill {
    border: 1px solid rgba(34, 211, 197, 0.35);
    border-radius: 999px;
    padding: 8px 11px;
    color: #d9fffb;
    background: rgba(34, 211, 197, 0.08);
    font-size: 0.78rem;
    font-weight: 900;
    white-space: nowrap;
}

.model-frame {
    overflow: hidden;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background:
        linear-gradient(rgba(255, 255, 255, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.055) 1px, transparent 1px),
        #0f1418;
    background-size: 44px 44px;
    box-shadow:
        inset 0 0 58px rgba(34, 211, 197, 0.08),
        0 18px 42px rgba(0, 0, 0, 0.24);
}

.asset-preview-band {
    display: grid;
    grid-template-columns: 82px minmax(0, 1fr);
    align-items: center;
    gap: 14px;
    margin-top: 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.06);
    padding: 12px;
}

.selected-preview {
    display: grid;
    min-height: 82px;
    place-items: center;
    border-radius: 12px;
    background:
        radial-gradient(circle at 50% 20%, rgba(34, 211, 197, 0.22), transparent 45%),
        rgba(255, 255, 255, 0.08);
}

.selected-preview img {
    width: 64px;
    height: 64px;
    object-fit: contain;
    filter: drop-shadow(0 18px 22px rgba(0, 0, 0, 0.32));
}

.variant-copy {
    margin: 0;
}

.variant-copy,
.variant-copy p,
.variant-copy h3,
.variant-copy strong {
    color: #e6edf2 !important;
}

.variant-copy .prose {
    font-size: 0.92rem !important;
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
    .metric-grid,
    .truck-card-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .model-stage-header {
        display: block;
    }

    .model-pill {
        display: inline-block;
        margin-top: 12px;
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
    .metric-grid,
    .truck-card-grid {
        grid-template-columns: 1fr;
    }

    .model-stage {
        min-height: 440px;
        padding: 12px;
    }

    .main-workspace {
        flex-direction: column !important;
    }

    .main-workspace > div,
    .main-workspace .control-panel,
    .main-workspace .stage-panel {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }

    .asset-preview-band {
        grid-template-columns: 1fr;
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


@lru_cache(maxsize=16)
def image_data_uri(path: str) -> str:
    image_path = Path(path)
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def selected_asset_html(truck_name: str, variant_name: str) -> str:
    preset = get_preset(truck_name)
    variant = preset.get_variant(variant_name)
    preview_src = image_data_uri(preview_path_for(preset.name, variant.name))
    dims = f"{preset.length_mm:,} x {preset.width_mm:,} x {preset.height_mm:,} mm"

    return f"""
    <div class="asset-preview-band">
        <div class="selected-preview">
            <img src="{preview_src}" alt="{escape(variant.name)} preview">
        </div>
        <div class="variant-copy">
            <h3>{escape(variant.name)}</h3>
            <p>{escape(variant.description)}</p>
            <p><strong>Truck class:</strong> {escape(preset.name)}</p>
            <p><strong>Internal load space:</strong> {escape(dims)}</p>
        </div>
    </div>
    """


def ready_status(source: str, truck_name: str, variant_name: str) -> str:
    preset = get_preset(truck_name)
    dims = f"{preset.length_mm:,} x {preset.width_mm:,} x {preset.height_mm:,} mm"
    return (
        "### Ready for visual run setup\n"
        f"Dataset source: **{source}**\n\n"
        f"Truck class: **{preset.name}**\n\n"
        f"Body style: **{variant_name}**\n\n"
        f"Internal load space: **{dims}**"
    )


def update_dataset_source(source: str):
    return dataset_helper(source), gr.update(visible=source == "Upload dataset")


def update_truck_class(source: str, truck_name: str):
    selected_variant = default_variant_name(truck_name)
    return (
        gr.update(choices=variant_names(truck_name), value=selected_variant),
        format_dimensions(truck_name),
        truck_cards_html(truck_name),
        model_path_for(truck_name, selected_variant),
        selected_asset_html(truck_name, selected_variant),
        ready_status(source, truck_name, selected_variant),
    )


def update_body_style(source: str, truck_name: str, variant_name: str):
    return (
        model_path_for(truck_name, variant_name),
        selected_asset_html(truck_name, variant_name),
        ready_status(source, truck_name, variant_name),
    )


def run_placeholder(source: str, truck_name: str, variant_name: str) -> str:
    preset = get_preset(truck_name)
    variant = preset.get_variant(variant_name)
    dims = f"{preset.length_mm:,} x {preset.width_mm:,} x {preset.height_mm:,} mm"

    return (
        "### Proposed GA run queued for a later milestone\n"
        f"Dataset source: **{source}**\n\n"
        f"Truck class: **{preset.name}**\n\n"
        f"Indian-equivalent class: **{preset.indian_equivalent}**\n\n"
        f"Body style: **{variant.name}**\n\n"
        f"Internal load space: **{dims}**\n\n"
        "Validation, solver execution, and animated box loading remain placeholders in M2."
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
                <div class="strip-value">Two visual classes</div>
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


def truck_cards_html(selected_name: str) -> str:
    cards = []
    for name in preset_names():
        preset = get_preset(name)
        selected_class = " is-selected" if preset.name == selected_name else ""
        visuals = "".join(
            f"""
            <div class="truck-thumb">
                <img src="{image_data_uri(preview_path_for(preset.name, variant.name))}"
                     alt="{escape(variant.name)} preview">
            </div>
            """
            for variant in preset.variants
        )
        bodies = "".join(
            f'<span class="body-chip">{escape(variant.name)}</span>' for variant in preset.variants
        )
        cards.append(
            f"""
            <div class="truck-card{selected_class}">
                <div class="truck-card-visuals">{visuals}</div>
                <div class="truck-card-kicker">{escape(preset.indian_equivalent)}</div>
                <div class="truck-card-title">{escape(preset.name)}</div>
                <div class="truck-card-dims">
                    {preset.length_ft:g} ft x {preset.width_ft:g} ft x {preset.height_ft:g} ft<br>
                    {preset.length_mm:,} x {preset.width_mm:,} x {preset.height_mm:,} mm
                </div>
                <div class="truck-card-bodies">{bodies}</div>
            </div>
            """
        )
    return f'<div class="truck-card-grid">{"".join(cards)}</div>'


def model_stage_header_html() -> str:
    return """
    <div class="model-stage-header">
        <div>
            <div class="model-stage-kicker">Asset-backed truck selection</div>
            <div class="model-stage-title">3D truck preview</div>
            <div class="model-stage-copy">
                The selected Kenney model previews the truck body for the future packing scene.
                Actual box loading animation starts after validation and placement data are connected.
            </div>
        </div>
        <div class="model-pill">Kenney Car Kit - CC0</div>
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
    default_truck = preset_names()[0]
    default_variant = default_variant_name(default_truck)

    with gr.Blocks(title="GA-Based Truck Loading") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(hero_html())

            with gr.Row(equal_height=False, elem_classes=["main-workspace"]):
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
                    dataset_status = gr.Markdown(
                        dataset_helper("Demo dataset"),
                        elem_classes=["truck-details"],
                    )

                    gr.Markdown("## Truck selector")
                    truck_cards = gr.HTML(truck_cards_html(default_truck))
                    truck_preset = gr.Radio(
                        choices=preset_names(),
                        value=default_truck,
                        label="Truck class",
                        elem_classes=["truck-class-radio"],
                    )
                    truck_variant = gr.Radio(
                        choices=variant_names(default_truck),
                        value=default_variant,
                        label="Body style",
                        elem_classes=["body-style-radio"],
                    )
                    truck_dimensions = gr.Markdown(
                        format_dimensions(default_truck),
                        elem_classes=["truck-details"],
                    )

                    gr.Textbox(
                        value="Proposed packing-aware genetic algorithm",
                        label="Model",
                        interactive=False,
                    )

                    with gr.Row():
                        gr.Slider(
                            20,
                            100,
                            value=40,
                            step=10,
                            label="Population",
                            interactive=False,
                        )
                        gr.Slider(
                            10,
                            100,
                            value=50,
                            step=10,
                            label="Generations",
                            interactive=False,
                        )

                    run_button = gr.Button("Prepare visual run", variant="primary")
                    run_status = gr.Markdown(
                        ready_status("Demo dataset", default_truck, default_variant),
                        elem_classes=["run-status"],
                    )

                with gr.Column(scale=2, min_width=300, elem_classes=["stage-panel"]):
                    with gr.Column(elem_classes=["model-stage"]):
                        gr.HTML(model_stage_header_html())
                        with gr.Column(elem_classes=["model-frame"]):
                            truck_model = gr.Model3D(
                                value=model_path_for(default_truck, default_variant),
                                label="Selected truck model",
                                show_label=False,
                                clear_color=(0.06, 0.08, 0.1, 1.0),
                                display_mode="solid",
                                camera_position=(2.7, 1.8, 3.2),
                                height=470,
                            )
                        variant_description = gr.HTML(
                            selected_asset_html(default_truck, default_variant),
                        )

            with gr.Column(elem_classes=["result-panel"]):
                gr.Markdown("## Result preview")
                gr.HTML(metrics_html())
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
            fn=update_truck_class,
            inputs=[dataset_source, truck_preset],
            outputs=[
                truck_variant,
                truck_dimensions,
                truck_cards,
                truck_model,
                variant_description,
                run_status,
            ],
        )
        truck_variant.change(
            fn=update_body_style,
            inputs=[dataset_source, truck_preset, truck_variant],
            outputs=[truck_model, variant_description, run_status],
        )
        run_button.click(
            fn=run_placeholder,
            inputs=[dataset_source, truck_preset, truck_variant],
            outputs=run_status,
        )

    return demo


if __name__ == "__main__":
    build_app().launch(
        css=CUSTOM_CSS,
        allowed_paths=[str(ASSET_ROOT)],
        theme=gr.themes.Soft(primary_hue="cyan", secondary_hue="amber"),
    )
