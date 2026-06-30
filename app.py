"""Gradio entry point for the GA-Based Truck Loading demo."""

from __future__ import annotations

import base64
import csv
import io
import json
from functools import lru_cache
from html import escape
from pathlib import Path

import gradio as gr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from truck_loading.data import (
    DatasetBundle,
    DatasetError,
    box_preview_rows,
    demo_dataset_options,
    format_liters,
    format_truck_dimensions,
    has_blocking_results,
    load_demo_dataset,
    load_uploaded_dataset,
    validate_data_quality,
)
from truck_loading.ga import ProposedGAConfig, run_proposed_ga
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
from truck_loading.visualization import packing_viewer_html, packing_viewer_placeholder


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600;700&family=Playfair+Display:wght@600;700;800&family=Space+Grotesk:wght@500;600;700;800&display=swap');

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
    --font-display: "Playfair Display", "Soria", Georgia, serif;
    --font-body: "Space Grotesk", Inter, "Segoe UI", Arial, sans-serif;
    --font-mono: "IBM Plex Mono", "JetBrains Mono", Consolas, monospace;
}

body,
gradio-app {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
    font-family: var(--font-body) !important;
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
    font-family: var(--font-display);
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
    font-family: var(--font-display) !important;
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

.dataset-summary-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.dataset-card {
    min-height: 92px;
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
    background:
        linear-gradient(145deg, rgba(34, 211, 197, 0.08), transparent 46%),
        #ffffff;
    padding: 12px;
}

.dataset-card-label {
    color: #66737e;
    font-size: 0.72rem;
    font-weight: 900;
    text-transform: uppercase;
}

.dataset-card-value {
    margin-top: 7px;
    color: #151b20;
    font-size: 1.08rem;
    font-weight: 900;
    line-height: 1.25;
}

.dataset-card-note {
    margin-top: 5px;
    color: #657480;
    font-size: 0.8rem;
    line-height: 1.35;
}

.dataset-warning {
    margin-top: 10px;
    border: 1px solid rgba(247, 201, 72, 0.44);
    border-radius: 12px;
    background: rgba(247, 201, 72, 0.14);
    color: #4d3a06;
    padding: 10px 12px;
    font-size: 0.86rem;
    font-weight: 800;
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
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
    font-family: var(--font-mono);
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

.convergence-svg {
    width: 100%;
    min-height: 180px;
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
}

.result-panel {
    overflow: hidden;
}

.result-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 14px;
}

.result-kicker,
.validation-kicker {
    color: #178b83;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.result-title {
    margin-top: 4px;
    color: #141a1f;
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
}

.result-copy {
    max-width: 760px;
    color: #5f6f7a;
    line-height: 1.45;
}

.result-pill {
    border: 1px solid rgba(34, 211, 197, 0.36);
    border-radius: 999px;
    background: rgba(34, 211, 197, 0.1);
    color: #146963;
    font-size: 0.78rem;
    font-weight: 900;
    padding: 8px 12px;
    white-space: nowrap;
}

.validation-panel {
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 12px;
    background: #ffffff;
    padding: 12px;
    margin-bottom: 12px;
}

.validation-items {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 10px;
}

.validation-item {
    border: 1px solid rgba(17, 20, 23, 0.1);
    border-radius: 10px;
    padding: 10px;
    background: #f8fbfb;
}

.validation-item.success {
    border-color: rgba(34, 211, 197, 0.42);
    background: rgba(34, 211, 197, 0.09);
}

.validation-item.warning {
    border-color: rgba(247, 201, 72, 0.5);
    background: rgba(247, 201, 72, 0.14);
}

.validation-item.error {
    border-color: rgba(255, 107, 95, 0.48);
    background: rgba(255, 107, 95, 0.11);
}

.validation-title {
    color: #141a1f;
    font-weight: 900;
}

.validation-message {
    margin-top: 4px;
    color: #5f6f7a;
    font-size: 0.84rem;
    line-height: 1.35;
}

.download-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.download-chip {
    min-height: 74px;
    border: 1px dashed rgba(17, 20, 23, 0.18);
    border-radius: 12px;
    background: #f8fbfb;
    padding: 12px;
    opacity: 0.78;
}

.download-chip-title {
    color: #141a1f;
    font-weight: 900;
}

.download-chip-note {
    margin-top: 4px;
    color: #6c7b86;
    font-size: 0.82rem;
    line-height: 1.35;
}

.download-chip.ready {
    border-style: solid;
    border-color: rgba(34, 211, 197, 0.42);
    background: rgba(34, 211, 197, 0.08);
    opacity: 1;
}

.download-chip a {
    color: #116b66;
    font-weight: 900;
    text-decoration: none;
}

.packing-viewer-section {
    margin-top: 16px;
}

.packing-viewer-frame {
    width: 100%;
    min-height: 620px;
    border: 1px solid rgba(17, 20, 23, 0.12);
    border-radius: 14px;
    background: #0b0f12;
    overflow: hidden;
}

.packing-viewer-empty {
    min-height: 280px;
    display: grid;
    align-content: center;
    border: 1px dashed rgba(17, 20, 23, 0.18);
    border-radius: 14px;
    background:
        radial-gradient(circle at 22% 18%, rgba(34, 211, 197, 0.1), transparent 28%),
        #f8fbfb;
    padding: 24px;
}

.viewer-kicker {
    color: #178b83;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.viewer-title {
    margin-top: 8px;
    color: #141a1f;
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
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

    .result-header {
        display: block;
    }

    .model-pill {
        display: inline-block;
        margin-top: 12px;
    }

    .result-pill {
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
    .dataset-summary-grid,
    .truck-card-grid,
    .validation-items,
    .download-grid {
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


BOX_PREVIEW_HEADERS = ["Box", "Dimensions", "Volume"]
ROUTE_PREVIEW_HEADERS = ["Route / stop", "Customers", "Distance / location", "Boxes", "Status"]


def default_demo_label() -> str:
    return demo_dataset_options()[0]


def current_dataset_bundle(
    source: str,
    demo_label: str | None,
    uploaded_file,
) -> DatasetBundle | None:
    if source == "Upload dataset":
        return load_uploaded_dataset(uploaded_file)
    return load_demo_dataset(demo_label)


def dataset_helper(source: str, bundle: DatasetBundle | None = None, error: str | None = None) -> str:
    if error:
        return (
            f"### {source}\n"
            f"{error}\n\n"
            "Expected JSON schema: top-level `customers`, `boxes`, and `container`."
        )

    if source == "Upload dataset":
        if bundle is None:
            return (
                "### Upload dataset\n"
                "Upload a normalized 3L-SDVRP JSON dataset to preview customers, boxes, "
                "container dimensions, and warnings."
            )
        return f"### Upload dataset\nLoaded **{bundle.summary.instance_name}**."

    if bundle is None:
        return "### Demo dataset\nChoose one of the bundled 50/100 customer demo datasets."
    return (
        "### Demo dataset\n"
        f"Loaded **{bundle.summary.instance_name}** from the bundled conference batch."
    )


def dataset_summary_html(bundle: DatasetBundle | None, error: str | None = None) -> str:
    if error:
        return f"""
        <div class="dataset-warning">{escape(error)}</div>
        """
    if bundle is None:
        return """
        <div class="dataset-warning">
            Upload a normalized JSON dataset or choose a bundled demo dataset.
        </div>
        """

    summary = bundle.summary
    cards = [
        ("Customers", f"{summary.real_customer_count}", f"{summary.customer_count} rows including depot"),
        ("Boxes", f"{summary.box_count}", f"Per customer: {summary.boxes_per_customer_display}"),
        ("Container", summary.container_dimensions_display, "Displayed as meters / feet"),
        ("Box volume", summary.total_box_volume_display, f"Estimated fill: {summary.fill_percentage:.1f}%"),
    ]
    items = "\n".join(
        f"""
        <div class="dataset-card">
            <div class="dataset-card-label">{escape(label)}</div>
            <div class="dataset-card-value">{escape(value)}</div>
            <div class="dataset-card-note">{escape(note)}</div>
        </div>
        """
        for label, value, note in cards
    )

    warnings = []
    if summary.thin_box_count:
        warnings.append(
            f"{summary.thin_box_count} thin boxes detected; small dimensions are shown in cm/inches."
        )
    if summary.oversized_box_count:
        warnings.append(f"{summary.oversized_box_count} boxes exceed the source container.")
    warning_html = (
        f'<div class="dataset-warning">{" ".join(escape(warning) for warning in warnings)}</div>'
        if warnings
        else ""
    )
    return f'<div class="dataset-summary-grid">{items}</div>{warning_html}'


def selected_truck_dimensions(truck_name: str) -> tuple[float, float, float]:
    preset = get_preset(truck_name)
    return (float(preset.length_mm), float(preset.width_mm), float(preset.height_mm))


def selected_truck_container(truck_name: str) -> dict[str, float]:
    length, width, height = selected_truck_dimensions(truck_name)
    return {"L": length, "W": width, "H": height}


def validation_results(bundle: DatasetBundle | None, truck_name: str):
    if bundle is None:
        return []
    return validate_data_quality(bundle.data, truck_dimensions_mm=selected_truck_dimensions(truck_name))


def validation_panel_html(bundle: DatasetBundle | None, truck_name: str, error: str | None = None) -> str:
    if error:
        return f"""
        <div class="validation-panel">
            <div class="validation-kicker">Readiness check</div>
            <div class="validation-items">
                <div class="validation-item error">
                    <div class="validation-title">Dataset unavailable</div>
                    <div class="validation-message">{escape(error)}</div>
                </div>
            </div>
        </div>
        """

    if bundle is None:
        return """
        <div class="validation-panel">
            <div class="validation-kicker">Readiness check</div>
            <div class="validation-items">
                <div class="validation-item warning">
                    <div class="validation-title">Awaiting dataset</div>
                    <div class="validation-message">Choose a demo dataset or upload JSON to enable readiness checks.</div>
                </div>
            </div>
        </div>
        """

    items = []
    for result in validation_results(bundle, truck_name):
        items.append(
            f"""
            <div class="validation-item {escape(result.severity)}">
                <div class="validation-title">{escape(result.title)}</div>
                <div class="validation-message">{escape(result.message)}</div>
            </div>
            """
        )
    return f"""
    <div class="validation-panel">
        <div class="validation-kicker">Readiness check</div>
        <div class="validation-items">{"".join(items)}</div>
    </div>
    """


def dashboard_header_html(bundle: DatasetBundle | None, truck_name: str, variant_name: str) -> str:
    dataset_name = bundle.summary.instance_name if bundle else "Awaiting dataset"
    return f"""
    <div class="result-header">
        <div>
            <div class="result-kicker">Visual results dashboard</div>
            <div class="result-title">Run story board</div>
            <div class="result-copy">
                Validate the dataset, run the proposed GA, then inspect route metrics and animated
                truck-loading placements.
            </div>
        </div>
        <div class="result-pill">{escape(dataset_name)} | {escape(truck_name)} | {escape(variant_name)}</div>
    </div>
    """


def run_dashboard_header_html(
    bundle: DatasetBundle,
    truck_name: str,
    variant_name: str,
    run_result: dict,
) -> str:
    best_info = run_result["best_info"]
    return f"""
    <div class="result-header">
        <div>
            <div class="result-kicker">Proposed GA completed</div>
            <div class="result-title">Packed route result</div>
            <div class="result-copy">
                The proposed GA produced {best_info["route_count"]} route(s), then the real
                packing engine generated 3D placements for the selected truck.
            </div>
        </div>
        <div class="result-pill">{escape(bundle.summary.instance_name)} | {escape(truck_name)} | {escape(variant_name)}</div>
    </div>
    """


def result_metrics_html(
    bundle: DatasetBundle | None,
    truck_name: str,
    variant_name: str,
    error: str | None = None,
) -> str:
    if error or bundle is None:
        cards = [
            ("Readiness", "Blocked", "Upload or select a valid dataset"),
            ("Customers", "Pending", "Waiting for dataset"),
            ("Boxes", "Pending", "Waiting for dataset"),
            ("Selected truck", truck_name, variant_name),
            ("Proposed GA", "Blocked", "Waiting for a valid dataset"),
        ]
    else:
        results = validation_results(bundle, truck_name)
        blocked = has_blocking_results(results)
        preset = get_preset(truck_name)
        truck_volume = preset.length_mm * preset.width_mm * preset.height_mm
        truck_fill = bundle.summary.total_box_volume_mm3 / truck_volume * 100 if truck_volume else 0
        warnings = sum(1 for result in results if result.severity == "warning")
        cards = [
            ("Readiness", "Blocked" if blocked else "Ready", "Validation gate for future run"),
            ("Customers", f"{bundle.summary.real_customer_count}", "Max hosted demo: 100"),
            ("Boxes", f"{bundle.summary.box_count}", f"Warnings: {warnings}"),
            ("Truck fill", f"{truck_fill:.1f}%", f"{format_liters(bundle.summary.total_box_volume_mm3)} total box volume"),
            ("Selected truck", preset.name, variant_name),
            ("Proposed GA", "Ready" if not blocked else "Blocked", "Runs in this milestone"),
        ]

    items = "\n".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            <div class="metric-note">{escape(note)}</div>
        </div>
        """
        for label, value, note in cards
    )
    return f'<div class="metric-grid">{items}</div>'


def run_metrics_html(run_result: dict, truck_name: str, variant_name: str) -> str:
    best_info = run_result["best_info"]
    cards = [
        ("Best score", f"{run_result['best_score']:.1f}", "Lower is better"),
        ("Routes", f"{best_info['route_count']}", f"{best_info['feasible_routes']} feasible"),
        ("Packed boxes", f"{best_info['boxes_packed']}/{best_info['boxes_total']}", f"Unpacked: {best_info['unpacked_boxes']}"),
        ("Truck fill", f"{best_info['avg_fill_rate'] * 100:.1f}%", f"Min route fill: {best_info['min_fill_rate'] * 100:.1f}%"),
        ("Distance", f"{best_info['total_distance']:.1f}", "Coordinate-space distance"),
        ("Runtime", f"{run_result['runtime_seconds']:.1f}s", f"{truck_name} | {variant_name}"),
    ]
    items = "\n".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            <div class="metric-note">{escape(note)}</div>
        </div>
        """
        for label, value, note in cards
    )
    return f'<div class="metric-grid">{items}</div>'


def route_preview_rows(bundle: DatasetBundle | None, limit: int = 8) -> list[list[str]]:
    if bundle is None:
        return []

    rows = []
    stop = 1
    for customer in bundle.data["customers"]:
        if customer.get("is_depot"):
            continue
        customer_id = customer.get("customer_id", customer.get("id", stop))
        customer_label = customer.get("customer_name") or customer.get("name") or f"Customer {customer_id}"
        location = coordinates_label(customer)
        box_count = len(customer.get("assigned_boxes", []))
        rows.append([f"Stop {stop}", str(customer_label), location, str(box_count), "Awaiting proposed GA"])
        stop += 1
        if len(rows) >= limit:
            break
    return rows


def route_result_rows(run_result: dict) -> list[list[str]]:
    rows = []
    for route in run_result["best_info"]["routes"]:
        customers = " -> ".join(route["customer_labels"][:4])
        if len(route["customer_labels"]) > 4:
            customers += " -> ..."
        status = "Packed" if route["feasible"] else f"{len(route['unpacked_box_ids'])} unpacked"
        rows.append(
            [
                f"Route {route['route_index']}",
                customers,
                f"{route['distance']:.1f}",
                f"{route['boxes_packed']}/{route['boxes_total']}",
                status,
            ]
        )
    return rows


def coordinates_label(customer: dict) -> str:
    try:
        return f"{float(customer['x']):.1f}, {float(customer['y']):.1f}"
    except (KeyError, TypeError, ValueError):
        return "Coordinates unavailable"


def route_plot_figure(bundle: DatasetBundle | None, run_result: dict | None = None):
    fig, ax = plt.subplots(figsize=(7.2, 4.2), facecolor="#f8fbfb")
    ax.set_facecolor("#f8fbfb")
    ax.grid(True, color="#dce5e8", linewidth=0.8)
    ax.tick_params(colors="#5e6d78")
    for spine in ax.spines.values():
        spine.set_color("#cbd7dc")

    if bundle is None:
        ax.text(0.5, 0.5, "Upload or choose a dataset to preview route geometry.", ha="center", va="center")
        ax.set_axis_off()
        return fig

    depot_points = []
    customer_points = []
    for customer in bundle.data["customers"]:
        try:
            point = (float(customer["x"]), float(customer["y"]))
        except (KeyError, TypeError, ValueError):
            continue
        if customer.get("is_depot"):
            depot_points.append(point)
        else:
            customer_points.append(point)

    if not customer_points and not depot_points:
        ax.text(0.5, 0.5, "Coordinates unavailable for this dataset.", ha="center", va="center")
        ax.set_axis_off()
        return fig

    if customer_points:
        xs, ys = zip(*customer_points, strict=True)
        ax.scatter(xs, ys, s=42, c="#22d3c5", edgecolors="#111417", linewidths=0.5, alpha=0.88, label="Customers")
    if depot_points:
        dx, dy = zip(*depot_points, strict=True)
        ax.scatter(dx, dy, s=95, marker="s", c="#ff6b5f", edgecolors="#111417", linewidths=0.7, label="Depot")

    if run_result is not None and depot_points:
        depot = depot_points[0]
        customer_lookup = {
            str(customer.get("customer_id", customer.get("id"))): customer
            for customer in bundle.data["customers"]
            if not customer.get("is_depot") and customer.get("customer_id", customer.get("id")) is not None
        }
        route_colors = ["#22d3c5", "#f7c948", "#ff6b5f", "#8aa0b4", "#7c3aed", "#16a34a"]
        for route in run_result["best_info"]["routes"][:8]:
            points = [depot]
            for customer_id in route["route"]:
                customer = customer_lookup.get(str(customer_id))
                if customer is not None:
                    points.append((float(customer.get("x", 0)), float(customer.get("y", 0))))
            points.append(depot)
            if len(points) > 2:
                xs, ys = zip(*points, strict=True)
                color = route_colors[(route["route_index"] - 1) % len(route_colors)]
                ax.plot(xs, ys, color=color, linewidth=1.4, alpha=0.72)

    title_prefix = "Proposed GA route geometry" if run_result is not None else "Customer layout preview"
    ax.set_title(f"{title_prefix} - {bundle.summary.instance_name}", color="#141a1f", fontsize=11, weight="bold")
    ax.set_xlabel("X coordinate", color="#45545f")
    ax.set_ylabel("Y coordinate", color="#45545f")
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    return fig


def convergence_placeholder_html(bundle: DatasetBundle | None = None) -> str:
    dataset_name = bundle.summary.instance_name if bundle else "awaiting dataset"
    return f"""
    <div class="placeholder-chart" aria-label="Convergence placeholder"></div>
    <p class="dataset-card-note">
        Future convergence trace for {escape(dataset_name)}. The chart remains a styled placeholder until
        proposed-GA execution is connected.
    </p>
    """


def convergence_result_html(run_result: dict) -> str:
    history = run_result.get("history") or []
    if not history:
        return '<div class="dataset-warning">No convergence history was produced.</div>'

    width = 720
    height = 220
    padding = 28
    low = min(history)
    high = max(history)
    spread = high - low or 1.0
    points = []
    for index, value in enumerate(history):
        x = padding + (width - padding * 2) * (index / max(len(history) - 1, 1))
        y = height - padding - (height - padding * 2) * ((value - low) / spread)
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    return f"""
    <svg viewBox="0 0 {width} {height}" class="convergence-svg" role="img" aria-label="Proposed GA convergence chart">
        <rect width="{width}" height="{height}" rx="12" fill="#f8fbfb" />
        <path d="M {padding} {height - padding} H {width - padding}" stroke="#d5e0e4" stroke-width="1" />
        <path d="M {padding} {padding} V {height - padding}" stroke="#d5e0e4" stroke-width="1" />
        <polyline points="{polyline}" fill="none" stroke="#22d3c5" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="6" fill="#ff6b5f" />
        <text x="{padding}" y="20" fill="#141a1f" font-size="13" font-weight="800">Best score by generation</text>
        <text x="{padding}" y="{height - 8}" fill="#657480" font-size="11">Start {history[0]:.1f} | Best {history[-1]:.1f}</text>
    </svg>
    """


def download_placeholder_html(bundle: DatasetBundle | None, blocked: bool) -> str:
    status = "Blocked by validation" if blocked else "Prepared after proposed GA run"
    dataset_name = bundle.summary.instance_name if bundle else "No dataset selected"
    chips = [
        ("Normalized dataset JSON", dataset_name),
        ("Result JSON", status),
        ("Metrics CSV", status),
    ]
    items = "\n".join(
        f"""
        <div class="download-chip">
            <div class="download-chip-title">{escape(title)}</div>
            <div class="download-chip-note">{escape(note)}</div>
        </div>
        """
        for title, note in chips
    )
    return f'<div class="download-grid">{items}</div>'


def downloads_result_html(bundle: DatasetBundle, run_result: dict, truck_name: str, variant_name: str) -> str:
    normalized = {
        "instance_name": bundle.summary.instance_name,
        "truck": {
            "class": truck_name,
            "body_style": variant_name,
            "container": selected_truck_container(truck_name),
        },
        "dataset": bundle.data,
    }
    metrics_rows = [
        ["metric", "value"],
        ["best_score", f"{run_result['best_score']:.6f}"],
        ["runtime_seconds", f"{run_result['runtime_seconds']:.6f}"],
        ["route_count", str(run_result["best_info"]["route_count"])],
        ["feasible_routes", str(run_result["best_info"]["feasible_routes"])],
        ["boxes_total", str(run_result["best_info"]["boxes_total"])],
        ["boxes_packed", str(run_result["best_info"]["boxes_packed"])],
        ["avg_fill_rate", f"{run_result['best_info']['avg_fill_rate']:.6f}"],
    ]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(metrics_rows)
    chips = [
        ("Normalized dataset JSON", "dataset.json", json.dumps(normalized, indent=2)),
        ("Result JSON", "proposed-ga-result.json", json.dumps(run_result, indent=2)),
        ("Metrics CSV", "metrics.csv", csv_buffer.getvalue()),
    ]
    items = "\n".join(
        f"""
        <div class="download-chip ready">
            <div class="download-chip-title">{escape(title)}</div>
            <div class="download-chip-note">
                <a download="{escape(filename)}" href="{_data_download_uri(content, 'text/csv' if filename.endswith('.csv') else 'application/json')}">
                    Download {escape(filename)}
                </a>
            </div>
        </div>
        """
        for title, filename, content in chips
    )
    return f'<div class="download-grid">{items}</div>'


def _data_download_uri(content: str, mime_type: str) -> str:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def viewer_payload(run_result: dict, truck_name: str, variant_name: str) -> dict:
    preset = get_preset(truck_name)
    routes = [
        route
        for route in run_result["best_info"]["routes"]
        if route.get("placements")
    ]
    if not routes:
        routes = run_result["best_info"]["routes"][:1]
    return {
        "truck": {"name": preset.name, "body_style": variant_name},
        "container": selected_truck_container(truck_name),
        "routes": routes,
    }


def dashboard_outputs(
    source: str,
    demo_label: str | None,
    uploaded_file,
    truck_name: str,
    variant_name: str,
):
    try:
        bundle = current_dataset_bundle(source, demo_label, uploaded_file)
    except DatasetError as exc:
        error = str(exc)
        return (
            dataset_helper(source, error=error),
            dataset_summary_html(None, error=error),
            [],
            ready_status(source, truck_name, variant_name),
            dashboard_header_html(None, truck_name, variant_name),
            validation_panel_html(None, truck_name, error=error),
            result_metrics_html(None, truck_name, variant_name, error=error),
            [],
            route_plot_figure(None),
            convergence_placeholder_html(None),
            download_placeholder_html(None, blocked=True),
            packing_viewer_placeholder(),
            gr.update(interactive=False),
        )

    results = validation_results(bundle, truck_name)
    blocked = has_blocking_results(results)
    return (
        dataset_helper(source, bundle=bundle),
        dataset_summary_html(bundle),
        box_preview_rows(bundle),
        ready_status(source, truck_name, variant_name, dataset_label=bundle.summary.instance_name),
        dashboard_header_html(bundle, truck_name, variant_name),
        validation_panel_html(bundle, truck_name),
        result_metrics_html(bundle, truck_name, variant_name),
        route_preview_rows(bundle),
        route_plot_figure(bundle),
        convergence_placeholder_html(bundle),
        download_placeholder_html(bundle, blocked=blocked),
        packing_viewer_placeholder(),
        gr.update(interactive=not blocked),
    )


def dataset_outputs(
    source: str,
    demo_label: str | None,
    uploaded_file,
    truck_name: str,
    variant_name: str,
):
    try:
        bundle = current_dataset_bundle(source, demo_label, uploaded_file)
    except DatasetError as exc:
        error = str(exc)
        return (
            dataset_helper(source, error=error),
            dataset_summary_html(None, error=error),
            [],
            ready_status(source, truck_name, variant_name),
        )

    return (
        dataset_helper(source, bundle=bundle),
        dataset_summary_html(bundle),
        box_preview_rows(bundle),
        ready_status(source, truck_name, variant_name, dataset_label=bundle.summary.instance_name),
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
    dims = format_truck_dimensions(preset.length_mm, preset.width_mm, preset.height_mm)

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


def ready_status(
    source: str,
    truck_name: str,
    variant_name: str,
    dataset_label: str | None = None,
) -> str:
    preset = get_preset(truck_name)
    dims = format_truck_dimensions(preset.length_mm, preset.width_mm, preset.height_mm)
    dataset_text = dataset_label or ("Awaiting upload" if source == "Upload dataset" else default_demo_label())
    return (
        "### Ready for visual run setup\n"
        f"Dataset source: **{source}**\n\n"
        f"Dataset: **{dataset_text}**\n\n"
        f"Truck class: **{preset.name}**\n\n"
        f"Body style: **{variant_name}**\n\n"
        f"Internal load space: **{dims}**"
    )


def update_dataset_source(source: str, demo_label: str, uploaded_file, truck_name: str, variant_name: str):
    outputs = dashboard_outputs(source, demo_label, uploaded_file, truck_name, variant_name)
    return (
        outputs[0],
        gr.update(visible=source == "Upload dataset"),
        gr.update(visible=source == "Demo dataset"),
        *outputs[1:],
    )


def update_dataset_selection(source: str, demo_label: str, uploaded_file, truck_name: str, variant_name: str):
    return dashboard_outputs(source, demo_label, uploaded_file, truck_name, variant_name)


def update_truck_class(source: str, demo_label: str, uploaded_file, truck_name: str):
    selected_variant = default_variant_name(truck_name)
    dashboard = dashboard_outputs(source, demo_label, uploaded_file, truck_name, selected_variant)
    return (
        gr.update(choices=variant_names(truck_name), value=selected_variant),
        format_dimensions(truck_name),
        truck_cards_html(truck_name),
        model_path_for(truck_name, selected_variant),
        selected_asset_html(truck_name, selected_variant),
        *dashboard[3:],
    )


def update_body_style(source: str, demo_label: str, uploaded_file, truck_name: str, variant_name: str):
    dashboard = dashboard_outputs(source, demo_label, uploaded_file, truck_name, variant_name)
    return (
        model_path_for(truck_name, variant_name),
        selected_asset_html(truck_name, variant_name),
        *dashboard[3:],
    )


def run_visual_demo(
    source: str,
    demo_label: str,
    uploaded_file,
    truck_name: str,
    variant_name: str,
    population_size: int | float,
    generations: int | float,
):
    preset = get_preset(truck_name)
    variant = preset.get_variant(variant_name)
    try:
        bundle = current_dataset_bundle(source, demo_label, uploaded_file)
    except DatasetError as exc:
        status = (
            "### Run blocked by validation\n"
            f"Dataset source: **{source}**\n\n"
            f"Dataset: **Unavailable ({exc})**\n\n"
            "Resolve the dataset issue before running the proposed GA."
        )
        return (
            status,
            dashboard_header_html(None, truck_name, variant_name),
            result_metrics_html(None, truck_name, variant_name, error=str(exc)),
            [],
            route_plot_figure(None),
            convergence_placeholder_html(None),
            download_placeholder_html(None, blocked=True),
            packing_viewer_placeholder(),
        )

    results = validation_results(bundle, truck_name)
    if has_blocking_results(results):
        blocking_titles = ", ".join(result.title for result in results if result.blocking)
        status = (
            "### Run blocked by validation\n"
            f"Dataset source: **{source}**\n\n"
            f"Dataset: **{bundle.summary.instance_name}**\n\n"
            f"Blocking checks: **{blocking_titles}**\n\n"
            "Fix the dataset before the proposed GA can produce route placements."
        )
        return (
            status,
            dashboard_header_html(bundle, truck_name, variant_name),
            result_metrics_html(bundle, truck_name, variant_name),
            route_preview_rows(bundle),
            route_plot_figure(bundle),
            convergence_placeholder_html(bundle),
            download_placeholder_html(bundle, blocked=True),
            packing_viewer_placeholder(),
        )

    config = ProposedGAConfig.capped(population_size, generations)
    run_result = run_proposed_ga(
        bundle.data,
        selected_truck_dimensions(truck_name),
        config=config,
    )
    best_info = run_result["best_info"]
    status = (
        "### Proposed GA run complete\n"
        f"Dataset: **{bundle.summary.instance_name}**\n\n"
        f"Truck class: **{preset.name}**\n\n"
        f"Body style: **{variant.name}**\n\n"
        f"Routes: **{best_info['route_count']}** | "
        f"Packed boxes: **{best_info['boxes_packed']}/{best_info['boxes_total']}** | "
        f"Average fill: **{best_info['avg_fill_rate'] * 100:.1f}%**\n\n"
        f"Runtime: **{run_result['runtime_seconds']:.1f}s** with "
        f"population **{config.population_size}** and **{config.generations}** generations."
    )
    return (
        status,
        run_dashboard_header_html(bundle, truck_name, variant_name, run_result),
        run_metrics_html(run_result, truck_name, variant_name),
        route_result_rows(run_result),
        route_plot_figure(bundle, run_result=run_result),
        convergence_result_html(run_result),
        downloads_result_html(bundle, run_result, truck_name, variant_name),
        packing_viewer_html(viewer_payload(run_result, truck_name, variant_name)),
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
                    {escape(format_truck_dimensions(preset.length_mm, preset.width_mm, preset.height_mm))}
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
    default_dataset = default_demo_label()
    default_bundle = load_demo_dataset(default_dataset)
    default_dashboard = dashboard_outputs(
        "Demo dataset",
        default_dataset,
        None,
        default_truck,
        default_variant,
    )

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
                        file_types=[".json"],
                        visible=False,
                    )
                    demo_dataset = gr.Dropdown(
                        choices=demo_dataset_options(),
                        value=default_dataset,
                        label="Demo dataset",
                    )
                    dataset_status = gr.Markdown(
                        dataset_helper("Demo dataset", bundle=default_bundle),
                        elem_classes=["truck-details"],
                    )
                    dataset_summary = gr.HTML(dataset_summary_html(default_bundle))
                    box_preview = gr.Dataframe(
                        headers=BOX_PREVIEW_HEADERS,
                        value=box_preview_rows(default_bundle),
                        label="Box preview",
                        interactive=False,
                        wrap=True,
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
                        population_slider = gr.Slider(
                            10,
                            60,
                            value=40,
                            step=10,
                            label="Population",
                            interactive=True,
                        )
                        generations_slider = gr.Slider(
                            2,
                            60,
                            value=50,
                            step=10,
                            label="Generations",
                            interactive=True,
                        )

                    run_button = gr.Button("Run proposed GA", variant="primary")
                    run_status = gr.Markdown(
                        default_dashboard[3],
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
                dashboard_header = gr.HTML(default_dashboard[4])
                validation_status = gr.HTML(default_dashboard[5])
                result_metrics = gr.HTML(default_dashboard[6])
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Convergence preview")
                        convergence_preview = gr.HTML(default_dashboard[9])
                    with gr.Column(scale=1):
                        gr.Markdown("### Customer geometry")
                        route_plot = gr.Plot(value=default_dashboard[8], show_label=False)
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Route preview")
                        route_summary = gr.Dataframe(
                            headers=ROUTE_PREVIEW_HEADERS,
                            value=default_dashboard[7],
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("### Downloads")
                        downloads_placeholder = gr.HTML(default_dashboard[10])

                with gr.Column(elem_classes=["packing-viewer-section"]):
                    gr.Markdown("### Animated 3D loading viewer")
                    packing_viewer = gr.HTML(default_dashboard[11])

        dataset_source.change(
            fn=update_dataset_source,
            inputs=[dataset_source, demo_dataset, upload_file, truck_preset, truck_variant],
            outputs=[
                dataset_status,
                upload_file,
                demo_dataset,
                dataset_summary,
                box_preview,
                run_status,
                dashboard_header,
                validation_status,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
                run_button,
            ],
        )
        demo_dataset.change(
            fn=update_dataset_selection,
            inputs=[dataset_source, demo_dataset, upload_file, truck_preset, truck_variant],
            outputs=[
                dataset_status,
                dataset_summary,
                box_preview,
                run_status,
                dashboard_header,
                validation_status,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
                run_button,
            ],
        )
        upload_file.change(
            fn=update_dataset_selection,
            inputs=[dataset_source, demo_dataset, upload_file, truck_preset, truck_variant],
            outputs=[
                dataset_status,
                dataset_summary,
                box_preview,
                run_status,
                dashboard_header,
                validation_status,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
                run_button,
            ],
        )
        truck_preset.change(
            fn=update_truck_class,
            inputs=[dataset_source, demo_dataset, upload_file, truck_preset],
            outputs=[
                truck_variant,
                truck_dimensions,
                truck_cards,
                truck_model,
                variant_description,
                run_status,
                dashboard_header,
                validation_status,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
                run_button,
            ],
        )
        truck_variant.change(
            fn=update_body_style,
            inputs=[dataset_source, demo_dataset, upload_file, truck_preset, truck_variant],
            outputs=[
                truck_model,
                variant_description,
                run_status,
                dashboard_header,
                validation_status,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
                run_button,
            ],
        )
        run_button.click(
            fn=run_visual_demo,
            inputs=[
                dataset_source,
                demo_dataset,
                upload_file,
                truck_preset,
                truck_variant,
                population_slider,
                generations_slider,
            ],
            outputs=[
                run_status,
                dashboard_header,
                result_metrics,
                route_summary,
                route_plot,
                convergence_preview,
                downloads_placeholder,
                packing_viewer,
            ],
        )

    return demo


if __name__ == "__main__":
    build_app().launch(
        css=CUSTOM_CSS,
        allowed_paths=[str(ASSET_ROOT)],
        theme=gr.themes.Soft(primary_hue="cyan", secondary_hue="amber"),
    )
