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
    get_preset,
    preset_names,
    preview_path_for,
    variant_names,
)
from truck_loading.visualization import packing_viewer_html, packing_viewer_placeholder


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Code+Latin:wght@400;500;600;700&family=Press+Start+2P&family=VT323&display=swap');

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
    --font-title: "Press Start 2P";
    --font-heading: "VT323";
    --font-body: "M PLUS Code Latin";
    --font-mono: "M PLUS Code Latin";
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
    max-width: 100% !important;
    margin: 0 !important;
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
    padding: 16px;
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
    font-family: var(--font-title);
    font-size: clamp(1.45rem, 3.4vw, 3.2rem);
    line-height: 1.18;
    letter-spacing: 0;
}

.hero-copy {
    max-width: 850px;
    color: #d6dde3;
    font-size: 1.06rem;
    line-height: 1.55;
}

.site-footer {
    margin-top: 18px;
    border: 1px solid rgba(178, 246, 242, 0.16);
    border-radius: 14px;
    background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
        rgba(5, 10, 14, 0.76);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 16px 44px rgba(0, 0, 0, 0.24);
    color: #d7e4e8;
    padding: 16px 18px;
}

.footer-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.footer-credit {
    color: #9fb0bb;
    font-size: 0.82rem;
}

.footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.footer-link {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid rgba(178, 246, 242, 0.16);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.035);
    color: #e7f1f4 !important;
    padding: 8px 10px;
    text-decoration: none !important;
    font-size: 0.78rem;
    font-weight: 700;
}

.footer-link:hover {
    border-color: rgba(34, 211, 197, 0.5);
    background: rgba(34, 211, 197, 0.12);
}

.footer-icon {
    display: inline-grid;
    place-items: center;
    width: 20px;
    height: 20px;
    border-radius: 999px;
    border: 1px solid rgba(34, 211, 197, 0.34);
    color: #22d3c5;
    font-size: 0.72rem;
    line-height: 1;
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
    font-family: var(--font-heading) !important;
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

.stage-panel .result-title {
    color: var(--text-main);
}

.stage-panel .result-copy {
    color: #c7d0d8;
}

.stage-panel .result-pill {
    color: #d9fffb;
    background: rgba(34, 211, 197, 0.08);
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
    font-family: var(--font-heading);
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
    margin-top: 12px;
}

.packing-viewer-frame {
    width: 100%;
    min-height: 640px;
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
    font-family: var(--font-heading);
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
}

/* Midnight glass theme */
body,
gradio-app {
    background: #05090d !important;
}

.gradio-container {
    background:
        radial-gradient(circle at 18% 12%, rgba(34, 211, 197, 0.14), transparent 24%),
        radial-gradient(circle at 84% 8%, rgba(138, 160, 180, 0.12), transparent 22%),
        linear-gradient(180deg, #05090d 0%, #081017 42%, #0b1118 100%) !important;
    color: #e7f1f4 !important;
}

.control-panel,
.result-panel,
.stage-panel {
    border-color: rgba(125, 246, 239, 0.18) !important;
    background: rgba(10, 16, 23, 0.72) !important;
    box-shadow: 0 28px 80px rgba(0, 0, 0, 0.28) !important;
    backdrop-filter: blur(18px);
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
    color: #e7f1f4 !important;
}

.control-panel .prose p,
.control-panel .prose li,
.result-panel .prose p,
.result-panel .prose li {
    color: #b8c6cf !important;
}

.truck-details,
.run-status,
.dataset-card,
.validation-panel,
.validation-item,
.download-chip {
    border-color: rgba(125, 246, 239, 0.14) !important;
    background: rgba(255, 255, 255, 0.055) !important;
    color: #e7f1f4 !important;
}

.dataset-card-value,
.dataset-card-label,
.dataset-card-note,
.validation-title,
.validation-message,
.download-chip-title,
.download-chip-note {
    color: #e7f1f4 !important;
}

.packing-viewer-frame {
    min-height: 540px;
    border-color: rgba(125, 246, 239, 0.18);
}

.packing-viewer-empty {
    min-height: 390px;
    border-color: rgba(125, 246, 239, 0.18);
    background:
        radial-gradient(circle at 32% 18%, rgba(34, 211, 197, 0.12), transparent 30%),
        rgba(255, 255, 255, 0.045);
}

.viewer-title {
    color: #e7f1f4;
    font-size: 1.45rem;
}

.viewer-kicker,
.result-kicker,
.validation-kicker {
    color: #22d3c5;
}

.stage-panel .metric-grid {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding: 4px 2px 8px;
}

.stage-panel .metric-card {
    min-width: 168px;
    min-height: 84px;
    flex: 0 0 168px;
    border-color: rgba(125, 246, 239, 0.14);
    background: rgba(255, 255, 255, 0.065);
}

.stage-panel .metric-value,
.stage-panel .metric-label,
.stage-panel .metric-note {
    color: #e7f1f4;
}

.stage-panel .metric-value {
    font-size: 1.05rem;
}

.control-panel input,
.control-panel textarea,
.control-panel select,
.control-panel button,
.control-panel .wrap,
.control-panel .container,
.control-panel .secondary-wrap,
.control-panel .svelte-1gfkn6j {
    color: #e7f1f4 !important;
}

/* Dashboard layout and midnight polish */
.build-badge {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 12px 0;
    border: 1px solid rgba(125, 246, 239, 0.18);
    border-radius: 999px;
    background: rgba(10, 16, 23, 0.62);
    color: #d9fffb;
    padding: 10px 14px;
    font-size: 0.76rem;
    font-weight: 800;
    backdrop-filter: blur(16px);
}

.build-badge span:last-child {
    color: #8aa0b4;
}

.secondary-panel {
    margin-top: 14px;
}

.secondary-grid {
    display: grid !important;
    grid-template-columns: minmax(280px, 0.9fr) minmax(360px, 1.1fr);
    gap: 14px !important;
    align-items: start;
}

.secondary-grid > div {
    min-width: 0 !important;
}

.control-panel .block,
.result-panel .block {
    background: rgba(255, 255, 255, 0.045) !important;
    border-color: rgba(125, 246, 239, 0.12) !important;
}

.control-panel [data-testid="block-label"],
.result-panel [data-testid="block-label"] {
    color: #22d3c5 !important;
}

.control-panel input,
.control-panel textarea,
.control-panel select {
    background: rgba(255, 255, 255, 0.06) !important;
    border-color: rgba(125, 246, 239, 0.16) !important;
    color: #e7f1f4 !important;
}

.control-panel .wrap,
.result-panel .wrap {
    background: rgba(255, 255, 255, 0.04) !important;
    border-color: rgba(125, 246, 239, 0.12) !important;
}

.secondary-panel table,
.secondary-panel td,
.secondary-panel th {
    color: #e7f1f4 !important;
    background: rgba(5, 9, 13, 0.74) !important;
}

.secondary-panel .dataframe,
.secondary-panel .table-wrap {
    border-color: rgba(125, 246, 239, 0.14) !important;
}

@media (max-width: 900px) {
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .result-header {
        display: block;
    }

    .result-pill {
        display: inline-block;
        margin-top: 12px;
    }
}

@media (max-width: 1180px) {
    .secondary-grid {
        display: flex !important;
        flex-direction: column !important;
    }
}

/* Stage-first horizontal layout */
.command-panel,
.stage-viewer-panel,
.run-output-strip > div,
.run-status-panel,
.metrics-strip-panel {
    border: 1px solid rgba(125, 246, 239, 0.18);
    border-radius: 14px;
    background: rgba(10, 16, 23, 0.72);
    box-shadow: 0 28px 80px rgba(0, 0, 0, 0.28);
    backdrop-filter: blur(18px);
    padding: 14px;
}

.command-panel {
    margin-bottom: 14px;
}

.command-panel h2,
.run-status-panel h2,
.stage-viewer-panel h2,
.secondary-panel h2,
.secondary-panel h3 {
    color: #e7f1f4 !important;
}

.command-bar {
    display: grid !important;
    grid-template-columns: minmax(250px, 1fr) minmax(360px, 1.45fr) minmax(270px, 0.95fr);
    gap: 12px !important;
    align-items: start !important;
}

.command-bar > div,
.command-cell {
    min-width: 0 !important;
    width: 100% !important;
}

.command-cell {
    border: 1px solid rgba(125, 246, 239, 0.12);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.045);
    padding: 12px;
    overflow: hidden !important;
}

.command-panel,
.command-panel *,
.command-cell,
.command-cell * {
    scrollbar-width: none !important;
}

.command-panel::-webkit-scrollbar,
.command-panel *::-webkit-scrollbar,
.command-cell::-webkit-scrollbar,
.command-cell *::-webkit-scrollbar {
    width: 0 !important;
    height: 0 !important;
    display: none !important;
}

.dataset-status-strip {
    margin-top: 10px;
    padding: 10px 12px;
}

.dataset-status-strip h3,
.dataset-status-strip p {
    display: inline;
    margin-right: 10px;
}

.visually-hidden-panel {
    display: none !important;
}

.visually-hidden-panel,
.visually-hidden-panel *,
.command-cell .visually-hidden-panel,
.command-cell .visually-hidden-panel *,
.command-cell .block:has(.visually-hidden-panel),
.command-cell .wrap:has(.visually-hidden-panel) {
    display: none !important;
}

.stage-viewer-panel {
    margin-bottom: 14px;
    padding: 16px;
}

.stage-viewer-panel .result-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 12px;
}

.stage-viewer-panel .result-title {
    color: #e7f1f4;
    font-size: 1.55rem;
}

.stage-viewer-panel .result-copy {
    color: #9fb0bb;
    font-size: 0.86rem;
}

.stage-viewer-panel .packing-viewer-section {
    margin-top: 0;
}

.stage-viewer-panel .packing-viewer-section h3 {
    display: none;
}

.stage-viewer-panel .packing-viewer-frame {
    min-height: 720px;
    height: min(74vh, 820px);
    border-color: rgba(125, 246, 239, 0.24);
}

.stage-viewer-panel .packing-viewer-empty {
    min-height: 560px;
}

.run-output-strip {
    display: grid !important;
    grid-template-columns: minmax(300px, 0.56fr) minmax(620px, 2fr);
    gap: 14px !important;
    align-items: start !important;
    margin-bottom: 14px;
}

.run-output-strip > div {
    min-width: 0 !important;
    width: 100% !important;
}

.metrics-strip-panel .metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    overflow: visible;
    padding-bottom: 0;
}

.metrics-strip-panel .metric-card {
    min-width: 0;
    min-height: 82px;
    border-color: rgba(125, 246, 239, 0.16);
    background: rgba(255, 255, 255, 0.065);
}

.metrics-strip-panel .metric-label,
.metrics-strip-panel .metric-value,
.metrics-strip-panel .metric-note,
.metric-card,
.metric-card * {
    color: #e7f1f4 !important;
}

.metrics-strip-panel .metric-note,
.metric-note {
    color: #9fb0bb !important;
}

.secondary-panel {
    margin-top: 0;
}

.secondary-panel .dataset-summary-grid {
    margin-bottom: 12px;
}

.gradio-container,
.gradio-container label,
.gradio-container button,
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container table,
.gradio-container th,
.gradio-container td,
.gradio-container .prose,
.gradio-container .prose *,
.gradio-container .wrap,
.gradio-container .block,
.gradio-container .form,
.gradio-container .container {
    color: #e7f1f4 !important;
}

.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container .wrap,
.gradio-container .block,
.gradio-container .form {
    background-color: rgba(255, 255, 255, 0.045) !important;
    border-color: rgba(125, 246, 239, 0.14) !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #8aa0b4 !important;
}

.dataset-warning {
    color: #ffe39a !important;
    background: rgba(247, 201, 72, 0.12) !important;
}

.command-bar select,
.command-bar input,
.command-bar textarea,
.command-bar [role="combobox"],
.command-bar .wrap,
.command-bar .container {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

.command-bar select,
.command-bar input {
    padding-right: 34px !important;
}

.command-bar .dropdown,
.command-bar [data-testid="dropdown"],
.command-bar .secondary-wrap {
    min-width: 0 !important;
    max-width: 100% !important;
}

.metric-card .metric-value,
.metric-card .metric-label,
.metric-card .metric-note {
    opacity: 1 !important;
}

.metric-card .metric-value {
    color: #f4f7f9 !important;
}

.metric-card .metric-label {
    color: #9fb0bb !important;
}

.metric-card .metric-note {
    color: #b8c6cf !important;
}

.run-status,
.run-status *,
.dataset-status-strip,
.dataset-status-strip * {
    color: #e7f1f4 !important;
}

/* Glossy glass controls */
.command-panel,
.stage-viewer-panel,
.run-output-strip > div,
.result-panel,
.command-cell,
.metric-card,
.dataset-card,
.validation-panel,
.validation-item,
.truck-details,
.run-status {
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.018) 42%, rgba(255, 255, 255, 0.006)),
        linear-gradient(180deg, rgba(125, 246, 239, 0.026), rgba(5, 9, 13, 0.08)),
        rgba(11, 18, 24, 0.72) !important;
    border-color: rgba(178, 246, 242, 0.16) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.11),
        inset 1px 0 0 rgba(255, 255, 255, 0.045),
        inset 0 -18px 42px rgba(0, 0, 0, 0.11),
        0 18px 54px rgba(0, 0, 0, 0.24) !important;
}

.command-panel::before,
.stage-viewer-panel::before,
.run-output-strip > div::before,
.result-panel::before,
.command-cell::before,
.metric-card::before,
.dataset-card::before,
.truck-details::before,
.run-status::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(118deg, rgba(255, 255, 255, 0.075), rgba(255, 255, 255, 0.016) 16%, transparent 30%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.028), transparent 34%);
    opacity: 0.58;
}

.command-panel > *,
.stage-viewer-panel > *,
.run-output-strip > div > *,
.result-panel > *,
.command-cell > *,
.metric-card > *,
.dataset-card > *,
.truck-details > *,
.run-status > * {
    position: relative;
    z-index: 1;
}

.gradio-container input[type="range"] {
    width: 100% !important;
    height: 10px !important;
    accent-color: #22d3c5 !important;
    cursor: pointer;
    background: transparent !important;
    padding: 0 !important;
}

.gradio-container input[type="range"]::-webkit-slider-runnable-track {
    height: 10px;
    border-radius: 999px;
    background: rgba(126, 145, 156, 0.18);
    box-shadow: inset 0 0 0 1px rgba(178, 246, 242, 0.08);
}

.gradio-container input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    width: 24px;
    height: 24px;
    margin-top: -7px;
    border-radius: 50%;
    border: 4px solid #e7fffb;
    background: radial-gradient(circle at 32% 28%, #ffffff, #35ead9 58%, #087a76);
    box-shadow: 0 0 0 5px rgba(34, 211, 197, 0.18), 0 8px 18px rgba(0, 0, 0, 0.38);
}

.gradio-container input[type="range"]::-moz-range-track {
    height: 10px;
    border-radius: 999px;
    background: rgba(126, 145, 156, 0.18);
}

.gradio-container input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border: 3px solid #e7fffb;
    background: #22d3c5;
    box-shadow: 0 0 0 4px rgba(34, 211, 197, 0.18);
}

.command-cell input[type="number"],
.command-cell .number input {
    background: rgba(255, 255, 255, 0.105) !important;
    border: 1px solid rgba(178, 246, 242, 0.16) !important;
    color: #ffffff !important;
    font-weight: 900 !important;
}

.gradio-container input[type="number"] {
    appearance: textfield !important;
    -moz-appearance: textfield !important;
}

.gradio-container input[type="number"]::-webkit-inner-spin-button,
.gradio-container input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none !important;
    appearance: none !important;
    display: none !important;
    margin: 0 !important;
}

.command-cell label:has(input[type="radio"]) {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(178, 246, 242, 0.12) !important;
    background: rgba(255, 255, 255, 0.045) !important;
    color: #d5e4ea !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.command-cell label:has(input[type="radio"]:checked) {
    border-color: rgba(34, 211, 197, 0.62) !important;
    background:
        linear-gradient(135deg, rgba(34, 211, 197, 0.34), rgba(34, 211, 197, 0.16)),
        rgba(255, 255, 255, 0.06) !important;
    color: #ffffff !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16), 0 8px 24px rgba(34, 211, 197, 0.12);
}

.command-cell input[type="radio"] {
    appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    min-width: 18px !important;
    border: 1px solid rgba(178, 246, 242, 0.3) !important;
    border-radius: 50% !important;
    background: rgba(255, 255, 255, 0.055) !important;
    accent-color: #22d3c5 !important;
    filter: drop-shadow(0 0 6px rgba(34, 211, 197, 0.42));
}

.command-cell input[type="radio"]:checked {
    border-color: rgba(34, 211, 197, 0.84) !important;
    background:
        radial-gradient(circle, #e7fffb 0 24%, transparent 27%),
        rgba(34, 211, 197, 0.18) !important;
}

.command-cell .form,
.command-cell .wrap,
.command-cell .container {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* Control cleanup: remove Gradio's nested grey wrapper slabs. */
.command-cell .block,
.command-cell .form,
.command-cell .wrap,
.command-cell .container,
.command-cell .input-container,
.command-cell .radio,
.command-cell .checkbox-group,
.command-cell .secondary-wrap,
.command-cell [data-testid="radio-group"],
.command-cell [data-testid="checkbox-group"],
.command-cell [data-testid="dropdown"] {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

.command-cell .block,
.command-cell .form,
.command-cell .wrap,
.command-cell .container,
.command-cell [data-testid="radio-group"],
.command-cell [data-testid="dropdown"] {
    border-color: transparent !important;
}

.command-cell [data-testid="dropdown"] input,
.command-cell select,
.command-cell input[type="text"] {
    border: 1px solid rgba(178, 246, 242, 0.12) !important;
    border-radius: 8px !important;
    background: rgba(255, 255, 255, 0.045) !important;
    color: #e7f1f4 !important;
}

.command-cell .slider,
.command-cell [data-testid="slider"] {
    background: transparent !important;
    overflow: visible !important;
}

.command-cell .slider input[type="range"],
.command-cell [data-testid="slider"] input[type="range"] {
    width: calc(100% - 32px) !important;
    margin: 8px 16px 2px !important;
}

.command-cell .slider .wrap,
.command-cell [data-testid="slider"] .wrap {
    overflow: visible !important;
}

.command-panel,
.command-cell,
.dataset-select,
.dataset-select .wrap,
.dataset-select .container,
.dataset-select [data-testid="dropdown"] {
    overflow: visible !important;
}

.dataset-select input,
.dataset-select [role="combobox"] {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.dataset-button-radio {
    width: 100%;
}

.dataset-button-radio .wrap,
.dataset-button-radio .form,
.dataset-button-radio .container,
.dataset-button-radio [role="radiogroup"],
.dataset-button-radio [data-testid="radio-group"] {
    overflow: visible !important;
    background: transparent !important;
    box-shadow: none !important;
}

.dataset-button-radio [role="radiogroup"],
.dataset-button-radio [data-testid="radio-group"],
.dataset-button-radio .wrap > div {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px !important;
}

.dataset-button-radio .wrap,
.dataset-button-radio .wrap > div,
.dataset-button-radio [role="radiogroup"],
.dataset-button-radio [data-testid="radio-group"] {
    width: 100% !important;
}

.dataset-button-radio label:has(input[type="radio"]) {
    flex: 0 0 calc(50% - 4px) !important;
    width: calc(50% - 4px) !important;
    max-width: calc(50% - 4px) !important;
}

.dataset-button-radio label:has(input[type="radio"]) {
    min-height: 38px !important;
    padding: 8px 9px 8px 34px !important;
    justify-content: flex-start !important;
    font-size: 0.72rem !important;
    white-space: nowrap !important;
}

.dataset-button-radio label:has(input[type="radio"])::before {
    left: 11px !important;
    width: 16px !important;
    height: 16px !important;
}

.dataset-button-radio label:has(input[type="radio"]:checked)::after {
    left: 16px !important;
    width: 6px !important;
    height: 6px !important;
}

/* Global wrapper cleanup: keep Gradio wrappers invisible outside real surfaces. */
.app-shell .wrap,
.app-shell .block,
.app-shell .form,
.app-shell .container,
.app-shell .input-container,
.app-shell .table-wrap,
.app-shell .dataframe,
.app-shell .plot-container,
.app-shell .plot,
.stage-viewer-panel .wrap,
.stage-viewer-panel .block,
.stage-viewer-panel .form,
.stage-viewer-panel .container,
.run-output-strip .wrap,
.run-output-strip .block,
.run-output-strip .form,
.run-output-strip .container,
.result-panel .wrap,
.result-panel .block,
.result-panel .form,
.result-panel .container,
.secondary-panel .wrap,
.secondary-panel .block,
.secondary-panel .form,
.secondary-panel .container,
.metrics-strip-panel .wrap,
.metrics-strip-panel .block,
.metrics-strip-panel .form,
.metrics-strip-panel .container,
.packing-viewer-section .wrap,
.packing-viewer-section .block,
.packing-viewer-section .form,
.packing-viewer-section .container {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

.app-shell .wrap,
.app-shell .block,
.app-shell .form,
.app-shell .container,
.app-shell .input-container,
.app-shell .table-wrap,
.app-shell .dataframe,
.app-shell .plot-container,
.app-shell .plot {
    border-color: transparent !important;
}

.stage-viewer-panel .result-header,
.stage-viewer-panel .packing-viewer-section,
.run-output-strip,
.metrics-strip-panel .metric-grid,
.secondary-panel .dataset-summary-grid,
.secondary-panel .download-grid {
    background: transparent !important;
    box-shadow: none !important;
}

.app-shell .metric-card,
.app-shell .dataset-card,
.app-shell .download-chip,
.app-shell .validation-item,
.app-shell .run-status,
.app-shell .dataset-warning,
.app-shell .truck-details {
    border-color: rgba(178, 246, 242, 0.16) !important;
}

.secondary-panel table,
.secondary-panel td,
.secondary-panel th {
    background: rgba(5, 10, 14, 0.82) !important;
    border-color: rgba(125, 246, 239, 0.12) !important;
    color: #e7f1f4 !important;
}

.secondary-panel thead th,
.secondary-panel table th {
    background: rgba(7, 14, 19, 0.94) !important;
    color: #f4f7f9 !important;
}

.secondary-panel .dataframe,
.secondary-panel .table-wrap,
.secondary-panel .plot-container,
.secondary-panel .plot,
.secondary-panel canvas,
.secondary-panel svg {
    border-radius: 12px !important;
    overflow: hidden !important;
}

.stage-viewer-panel .result-pill {
    background: rgba(34, 211, 197, 0.12) !important;
    border-color: rgba(34, 211, 197, 0.32) !important;
}

.packing-viewer-frame {
    background: #05090d !important;
}

/* Live-demo cleanup: plain labels, centered sliders, dark SVG plots. */
.field-heading,
.field-heading .prose,
.field-heading p {
    margin: 0 0 8px !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    color: #dff7f5 !important;
    font-family: var(--font-heading) !important;
    font-size: 1.7rem !important;
    line-height: 0.9 !important;
    letter-spacing: 0 !important;
}

.command-panel h2,
.stage-viewer-panel .result-title,
.secondary-panel h3,
.secondary-panel h2 {
    font-family: var(--font-heading) !important;
    font-size: clamp(2.05rem, 2.5vw, 2.75rem) !important;
    line-height: 0.9 !important;
    letter-spacing: 0 !important;
}

.hero-kicker,
.result-kicker,
.validation-kicker {
    font-family: var(--font-body) !important;
}

.app-shell [data-testid="block-label"],
.app-shell .label-wrap,
.app-shell .block-label {
    padding: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #dff7f5 !important;
    font-family: var(--font-heading) !important;
    font-size: 1.45rem !important;
}

.command-panel,
.stage-viewer-panel,
.run-output-strip > div,
.result-panel {
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        0 16px 40px rgba(0, 0, 0, 0.18) !important;
}

.command-cell,
.metric-card,
.dataset-card,
.validation-panel,
.validation-item,
.truck-details,
.run-status,
.download-chip {
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.07),
        0 10px 26px rgba(0, 0, 0, 0.16) !important;
}

.command-panel::before,
.stage-viewer-panel::before,
.run-output-strip > div::before,
.result-panel::before,
.command-cell::before,
.metric-card::before,
.dataset-card::before,
.truck-details::before,
.run-status::before {
    opacity: 0.18 !important;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.04), transparent 24%) !important;
}

.command-cell label:has(input[type="radio"]) {
    position: relative !important;
    padding-left: 56px !important;
    min-height: 44px !important;
}

.command-cell label:has(input[type="radio"]) input[type="radio"] {
    position: absolute !important;
    left: 18px !important;
    top: 50% !important;
    width: 20px !important;
    height: 20px !important;
    margin: 0 !important;
    opacity: 0 !important;
}

.command-cell label:has(input[type="radio"])::before {
    content: "" !important;
    position: absolute !important;
    left: 18px !important;
    top: 50% !important;
    width: 22px !important;
    height: 22px !important;
    transform: translateY(-50%) !important;
    border-radius: 50% !important;
    border: 1px solid rgba(178, 246, 242, 0.42) !important;
    background: rgba(255, 255, 255, 0.055) !important;
    box-shadow: none !important;
}

.command-cell label:has(input[type="radio"]:checked)::after {
    content: "" !important;
    position: absolute !important;
    left: 25px !important;
    top: 50% !important;
    width: 8px !important;
    height: 8px !important;
    transform: translateY(-50%) !important;
    border-radius: 50% !important;
    background: #ecfffb !important;
    box-shadow: 0 0 10px rgba(34, 211, 197, 0.72) !important;
}

.slider-stack {
    width: 100% !important;
    gap: 0 !important;
}

.slider-stack .wrap,
.slider-stack .block,
.slider-stack .form,
.slider-stack .container {
    overflow: visible !important;
}

.slider-stack input[type="range"],
.command-cell .slider input[type="range"],
.command-cell [data-testid="slider"] input[type="range"] {
    width: 100% !important;
    max-width: 100% !important;
    margin: 10px 0 16px !important;
    padding: 0 !important;
    overflow: visible !important;
}

.slider-stack > div {
    overflow: visible !important;
}

.dataset-select,
.dataset-select *,
.command-cell [data-testid="dropdown"],
.command-cell [data-testid="dropdown"] * {
    overflow: visible !important;
}

.dataset-select input,
.dataset-select [role="combobox"] {
    min-width: 0 !important;
    padding-right: 42px !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

.dataset-button-radio {
    width: 100%;
}

.dataset-button-radio [role="radiogroup"],
.dataset-button-radio [data-testid="radio-group"],
.dataset-button-radio .wrap > div {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px !important;
}

.dataset-button-radio .wrap,
.dataset-button-radio .wrap > div,
.dataset-button-radio [role="radiogroup"],
.dataset-button-radio [data-testid="radio-group"] {
    width: 100% !important;
}

.truck-body-card-radio {
    width: 100% !important;
}

.truck-body-card-radio .wrap,
.truck-body-card-radio .form,
.truck-body-card-radio .container,
.truck-body-card-radio [role="radiogroup"],
.truck-body-card-radio [data-testid="radio-group"],
.truck-body-card-radio .wrap > div {
    width: 100% !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.truck-body-card-radio [role="radiogroup"],
.truck-body-card-radio [data-testid="radio-group"],
.truck-body-card-radio .wrap > div {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
}

.truck-body-card-radio label:has(input[type="radio"]) {
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    min-height: 92px !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 14px 16px 14px 116px !important;
    border: 1px solid rgba(178, 246, 242, 0.2) !important;
    border-radius: 14px !important;
    background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
        rgba(9, 16, 21, 0.82) !important;
    color: #dce8ed !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 10px 22px rgba(0, 0, 0, 0.18) !important;
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    line-height: 1.45 !important;
    white-space: normal !important;
    overflow: hidden !important;
}

.truck-body-card-radio label:has(input[type="radio"]:checked) {
    border-color: rgba(34, 211, 197, 0.78) !important;
    background:
        linear-gradient(135deg, rgba(34, 211, 197, 0.27), rgba(34, 211, 197, 0.1)),
        rgba(11, 28, 31, 0.9) !important;
    color: #f4ffff !important;
}

.truck-body-card-radio label:has(input[type="radio"])::after {
    content: "" !important;
    position: absolute !important;
    left: 18px !important;
    top: 50% !important;
    width: 72px !important;
    height: 72px !important;
    transform: translateY(-50%) !important;
    border: 1px solid rgba(178, 246, 242, 0.2) !important;
    border-radius: 13px !important;
    background-color: rgba(255, 255, 255, 0.055) !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 64px 64px !important;
    overflow: hidden !important;
}

.truck-body-card-radio label:has(input[type="radio"]:checked)::after {
    content: "" !important;
    left: 18px !important;
    top: 50% !important;
    width: 72px !important;
    height: 72px !important;
    transform: translateY(-50%) !important;
    border-radius: 13px !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 64px 64px !important;
    box-shadow: none !important;
}

.truck-body-card-radio label:has(input[type="radio"])::before {
    display: none !important;
    content: none !important;
}

.truck-body-card-radio label:has(input[type="radio"]:checked)::before {
    display: none !important;
    content: none !important;
}

.truck-body-card-radio label:has(input[type="radio"]:checked) input + span,
.truck-body-card-radio label:has(input[type="radio"]:checked) span {
    color: #f4ffff !important;
}

.hidden-state-controls,
.hidden-state-controls *,
.hidden-state-controls .wrap,
.hidden-state-controls .block,
.hidden-state-controls .form,
.hidden-state-controls .container {
    display: none !important;
}

.run-action-cell {
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    gap: 14px !important;
}

.run-action-copy {
    color: #9fb0bb !important;
    font-size: 0.76rem !important;
    line-height: 1.45 !important;
}

.command-panel input[type="number"],
.command-panel input[type="number"] *,
.command-panel input[type="number"]::-webkit-outer-spin-button,
.command-panel input[type="number"]::-webkit-inner-spin-button {
    appearance: textfield !important;
    -moz-appearance: textfield !important;
    -webkit-appearance: none !important;
    margin: 0 !important;
}

.command-panel button[aria-label*="Reset"],
.command-panel button[title*="Reset"],
.command-panel button[aria-label*="Increase"],
.command-panel button[aria-label*="Decrease"],
.command-panel .reset-button,
.command-panel .stepper,
.command-panel .number-control {
    display: none !important;
}

.command-panel > .prose,
.stage-viewer-panel > .prose,
.result-panel > .prose,
.secondary-panel > .prose,
.secondary-grid > div > .prose,
.secondary-grid .prose,
.secondary-panel h2,
.secondary-panel h3,
.stage-viewer-panel h2,
.run-output-strip h2 {
    margin-left: 0 !important;
    padding-left: 0 !important;
    text-align: left !important;
}

.secondary-grid > div {
    padding-left: 0 !important;
}

.route-geometry-card {
    width: 100%;
    min-height: 360px;
    border: 1px solid rgba(178, 246, 242, 0.14);
    border-radius: 14px;
    background:
        radial-gradient(circle at 18% 14%, rgba(34, 211, 197, 0.12), transparent 28%),
        rgba(5, 10, 14, 0.78);
    padding: 14px;
    color: #e7f1f4;
    overflow: hidden;
}

.route-geometry-card.empty {
    display: grid;
    align-content: center;
}

.route-geometry-title {
    color: #f3fbfb;
    font-family: var(--font-body);
    font-weight: 800;
    font-size: 0.9rem;
    margin-bottom: 10px;
}

.route-geometry-card p {
    color: #9fb0bb;
    margin: 0;
}

.route-geometry-svg {
    width: 100%;
    display: block;
    min-height: 300px;
    font-family: var(--font-body);
}

.route-geometry-svg .plot-bg {
    fill: rgba(6, 11, 16, 0.92);
    stroke: rgba(178, 246, 242, 0.14);
}

.route-geometry-svg .plot-grid line {
    stroke: rgba(178, 246, 242, 0.08);
    stroke-width: 1;
}

.route-geometry-svg .customer-dot {
    fill: #22d3c5;
    stroke: #0a1117;
    stroke-width: 1.2;
}

.route-geometry-svg .depot-dot {
    fill: #ff6b5f;
    stroke: #0a1117;
    stroke-width: 1.2;
}

.route-geometry-svg text {
    fill: #d9e6ea;
    font-family: var(--font-body);
    font-size: 13px;
    font-weight: 700;
}

.convergence-svg rect {
    fill: rgba(6, 11, 16, 0.92) !important;
}

.convergence-svg text {
    fill: #e7f1f4 !important;
    font-family: var(--font-body) !important;
}

@media (max-width: 1180px) {
    .command-bar,
    .run-output-strip {
        display: flex !important;
        flex-direction: column !important;
    }

    .stage-viewer-panel .packing-viewer-frame {
        min-height: 560px;
        height: 68vh;
    }

    .metrics-strip-panel .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 720px) {
    .metrics-strip-panel .metric-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 640px) {
    .app-shell {
        padding: 10px;
    }

    .hero {
        padding: 20px;
    }

    .metric-grid,
    .dataset-summary-grid,
    .validation-items,
    .download-grid {
        grid-template-columns: 1fr;
    }
}
"""


BOX_PREVIEW_HEADERS = ["Box", "Dimensions", "Volume"]
ROUTE_PREVIEW_HEADERS = ["Route / stop", "Customers", "Distance / location", "Boxes", "Status"]
BUILD_LABEL = "Public demo build"

TRUCK_BODY_OPTIONS = (
    ("City Mini Truck", "Open pickup body"),
    ("City Mini Truck", "Closed delivery van"),
    ("Medium Cargo Truck", "Covered cargo body"),
    ("Medium Cargo Truck", "Flatbed utility body"),
)


def truck_body_key(truck_name: str, variant_name: str) -> str:
    return f"{truck_name}::{variant_name}"


def truck_body_choice_label(truck_name: str, variant_name: str) -> str:
    preset = get_preset(truck_name)
    dims = format_truck_dimensions(preset.length_mm, preset.width_mm, preset.height_mm)
    return f"{variant_name} | {truck_name} | {dims}"


TRUCK_BODY_CHOICES = [
    (truck_body_choice_label(truck_name, variant_name), truck_body_key(truck_name, variant_name))
    for truck_name, variant_name in TRUCK_BODY_OPTIONS
]
TRUCK_BODY_STATE = {
    truck_body_key(truck_name, variant_name): (truck_name, variant_name)
    for truck_name, variant_name in TRUCK_BODY_OPTIONS
}


def default_truck_body_key() -> str:
    return truck_body_key(TRUCK_BODY_OPTIONS[0][0], TRUCK_BODY_OPTIONS[0][1])


def parse_truck_body_choice(choice_key: str | None) -> tuple[str, str]:
    if choice_key in TRUCK_BODY_STATE:
        return TRUCK_BODY_STATE[choice_key]
    return TRUCK_BODY_OPTIONS[0]


def default_demo_label() -> str:
    return demo_dataset_options()[0]


def build_badge_html() -> str:
    return f"""
    <div class="build-badge">
        <span>{BUILD_LABEL}</span>
        <span>Proposed GA only | Quick defaults 10 x 2</span>
    </div>
    """


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
        return "### Demo dataset\nChoose one of the bundled 50/100/150/200 customer demo datasets."
    return (
        "### Demo dataset\n"
        f"Loaded **{bundle.summary.instance_name}** from the bundled demo datasets."
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
            <div class="result-title">Viewer stage</div>
            <div class="result-copy">
                Validate the dataset, run the proposed GA, then inspect the animated truck-loading scene.
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
            <div class="result-title">Packed route scene</div>
            <div class="result-copy">
                {best_info["route_count"]} route(s) generated with exact final packing placements.
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
            ("Readiness", "Blocked" if blocked else "Ready", "Validation gate for this run"),
            ("Customers", f"{bundle.summary.real_customer_count}", "Max hosted demo: 200"),
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
    first_route = (best_info.get("routes") or [{}])[0]
    truck_volume_liters = float(first_route.get("truck_volume_liters") or 0.0)
    total_route_liters = sum(float(route.get("route_box_volume_liters") or 0.0) for route in best_info.get("routes", []))
    strategies = sorted({str(route.get("packing_strategy", "unknown")) for route in best_info.get("routes", [])})
    diagnostics = run_result.get("diagnostics", {})
    cards = [
        ("Best score", f"{run_result['best_score']:.1f}", "Lower is better"),
        ("Routes", f"{best_info['route_count']}", f"{best_info['feasible_routes']} feasible"),
        ("Packed boxes", f"{best_info['boxes_packed']}/{best_info['boxes_total']}", f"Unpacked: {best_info['unpacked_boxes']}"),
        ("Truck fill", f"{best_info['avg_fill_rate'] * 100:.1f}%", f"Min route fill: {best_info['min_fill_rate'] * 100:.1f}%"),
        ("Load volume", f"{total_route_liters:.1f} L", f"Truck capacity: {truck_volume_liters:.1f} L per route"),
        ("Packing order", ", ".join(strategies[:2]), "Best deterministic strategy per route"),
        ("Distance", f"{best_info['total_distance']:.1f}", "Coordinate-space distance"),
        ("Runtime", f"{run_result['runtime_seconds']:.1f}s", f"{truck_name} | {variant_name}"),
        ("GA search", f"{float(diagnostics.get('ga_search_time_seconds', 0.0)):.2f}s", "Capacity-estimated search"),
        ("Exact packing", f"{float(diagnostics.get('exact_packing_time_seconds', 0.0)):.2f}s", "Final placement pass"),
        ("Cache", f"{int(diagnostics.get('packing_cache_hits', 0))} hits", f"{int(diagnostics.get('packing_cache_misses', 0))} exact route evals"),
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
        strategy = route.get("packing_strategy", "unknown")
        status = f"Packed | {strategy}" if route["feasible"] else f"{len(route['unpacked_box_ids'])} unpacked | {strategy}"
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


def route_geometry_html(bundle: DatasetBundle | None, run_result: dict | None = None) -> str:
    if bundle is None:
        return """
        <div class="route-geometry-card empty">
            <div class="route-geometry-title">Customer layout preview</div>
            <p>Choose a demo dataset or upload JSON data to preview customer coordinates.</p>
        </div>
        """

    depot_points: list[tuple[float, float]] = []
    customer_points: list[tuple[float, float]] = []
    for customer in bundle.data["customers"]:
        try:
            point = (float(customer["x"]), float(customer["y"]))
        except (KeyError, TypeError, ValueError):
            continue
        if customer.get("is_depot"):
            depot_points.append(point)
        else:
            customer_points.append(point)

    all_points = customer_points + depot_points
    if not all_points:
        return f"""
        <div class="route-geometry-card empty">
            <div class="route-geometry-title">Customer layout preview</div>
            <p>Coordinates are unavailable for {escape(bundle.summary.instance_name)}.</p>
        </div>
        """

    width = 760
    height = 420
    pad = 34
    min_x = min(x for x, _ in all_points)
    max_x = max(x for x, _ in all_points)
    min_y = min(y for _, y in all_points)
    max_y = max(y for _, y in all_points)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    def project(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        sx = pad + (x - min_x) / span_x * (width - pad * 2)
        sy = height - pad - (y - min_y) / span_y * (height - pad * 2)
        return sx, sy

    grid_lines = []
    for index in range(6):
        x = pad + index * (width - pad * 2) / 5
        y = pad + index * (height - pad * 2) / 5
        grid_lines.append(f'<line x1="{x:.1f}" y1="{pad}" x2="{x:.1f}" y2="{height - pad}" />')
        grid_lines.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{width - pad}" y2="{y:.1f}" />')

    route_paths = []
    if run_result is not None and depot_points:
        depot = depot_points[0]
        customer_lookup = {
            str(customer.get("customer_id", customer.get("id"))): customer
            for customer in bundle.data["customers"]
            if not customer.get("is_depot") and customer.get("customer_id", customer.get("id")) is not None
        }
        route_colors = ["#22d3c5", "#f7c948", "#ff6b5f", "#9b8cff", "#87d37c", "#ff9f43"]
        for route in run_result["best_info"]["routes"][:8]:
            points = [depot]
            for customer_id in route["route"]:
                customer = customer_lookup.get(str(customer_id))
                if customer is not None:
                    points.append((float(customer.get("x", 0)), float(customer.get("y", 0))))
            points.append(depot)
            if len(points) > 2:
                projected = [project(point) for point in points]
                line_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
                color = route_colors[(route["route_index"] - 1) % len(route_colors)]
                route_paths.append(
                    f'<polyline points="{line_points}" fill="none" stroke="{color}" stroke-width="2.2" opacity="0.78" />'
                )

    customer_marks = []
    for point in customer_points:
        x, y = project(point)
        customer_marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" class="customer-dot" />')
    depot_marks = []
    for point in depot_points:
        x, y = project(point)
        depot_marks.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" class="depot-dot" />')

    title_prefix = "Proposed GA route geometry" if run_result is not None else "Customer layout preview"
    return f"""
    <div class="route-geometry-card">
        <div class="route-geometry-title">{escape(title_prefix)} - {escape(bundle.summary.instance_name)}</div>
        <svg viewBox="0 0 {width} {height}" class="route-geometry-svg" role="img" aria-label="{escape(title_prefix)}">
            <rect x="0" y="0" width="{width}" height="{height}" rx="18" class="plot-bg" />
            <g class="plot-grid">{"".join(grid_lines)}</g>
            <g class="route-lines">{"".join(route_paths)}</g>
            <g>{"".join(customer_marks)}{"".join(depot_marks)}</g>
            <g class="plot-legend">
                <circle cx="{pad + 10}" cy="{pad - 12}" r="4.4" class="customer-dot" />
                <text x="{pad + 22}" y="{pad - 8}">Customers</text>
                <rect x="{pad + 128}" y="{pad - 17}" width="10" height="10" class="depot-dot" />
                <text x="{pad + 144}" y="{pad - 8}">Depot</text>
            </g>
        </svg>
    </div>
    """


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
    container = selected_truck_container(truck_name)
    routes = [
        route
        for route in run_result["best_info"]["routes"]
        if route.get("placements")
    ]
    if not routes:
        routes = run_result["best_info"]["routes"][:1]
    return {
        "truck": {"name": preset.name, "body_style": variant_name},
        "container": container,
        "axis_labels": {
            "length": f"Length {container['L'] / 1000:.1f} m / {container['L'] / 304.8:.1f} ft",
            "width": f"Width {container['W'] / 1000:.1f} m / {container['W'] / 304.8:.1f} ft",
            "height": f"Height {container['H'] / 1000:.1f} m / {container['H'] / 304.8:.1f} ft",
        },
        "axis_callouts": [
            {"axis": "length", "label": f"{container['L'] / 1000:.1f} m / {container['L'] / 304.8:.1f} ft"},
            {"axis": "width", "label": f"{container['W'] / 1000:.1f} m / {container['W'] / 304.8:.1f} ft"},
            {"axis": "height", "label": f"{container['H'] / 1000:.1f} m / {container['H'] / 304.8:.1f} ft"},
        ],
        "show_grid": False,
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
            route_geometry_html(None),
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
        route_geometry_html(bundle),
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


def truck_body_card_asset_css() -> str:
    lines = []
    for index, (truck_name, variant_name) in enumerate(TRUCK_BODY_OPTIONS, start=1):
        preview_src = image_data_uri(preview_path_for(truck_name, variant_name))
        lines.append(
            f"""
            .truck-body-card-radio label:has(input[type="radio"]):nth-of-type({index})::after {{
                background-image: url("{preview_src}") !important;
            }}
            """
        )
    return "\n".join(lines)


CUSTOM_CSS += truck_body_card_asset_css()


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


def update_truck_body_choice(source: str, demo_label: str, uploaded_file, choice_key: str):
    truck_name, variant_name = parse_truck_body_choice(choice_key)
    dashboard = dashboard_outputs(source, demo_label, uploaded_file, truck_name, variant_name)
    return (
        gr.update(value=truck_name),
        gr.update(choices=variant_names(truck_name), value=variant_name),
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
            route_geometry_html(None),
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
            route_geometry_html(bundle),
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
    diagnostics = run_result.get("diagnostics", {})
    status = (
        "### Proposed GA run complete\n"
        f"Dataset: **{bundle.summary.instance_name}**\n\n"
        f"Truck class: **{preset.name}**\n\n"
        f"Body style: **{variant.name}**\n\n"
        f"Routes: **{best_info['route_count']}** | "
        f"Packed boxes: **{best_info['boxes_packed']}/{best_info['boxes_total']}** | "
        f"Average fill: **{best_info['avg_fill_rate'] * 100:.1f}%**\n\n"
        f"Runtime: **{run_result['runtime_seconds']:.1f}s** with "
        f"population **{config.population_size}** and **{config.generations}** generations.\n\n"
        f"GA search: **{float(diagnostics.get('ga_search_time_seconds', 0.0)):.2f}s** | "
        f"Exact packing: **{float(diagnostics.get('exact_packing_time_seconds', 0.0)):.2f}s** | "
        f"Cache: **{int(diagnostics.get('packing_cache_hits', 0))} hits / "
        f"{int(diagnostics.get('packing_cache_misses', 0))} exact route evals**."
    )
    return (
        status,
        run_dashboard_header_html(bundle, truck_name, variant_name, run_result),
        run_metrics_html(run_result, truck_name, variant_name),
        route_result_rows(run_result),
        route_geometry_html(bundle, run_result=run_result),
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
    </section>
    """


def footer_html() -> str:
    return """
    <footer class="site-footer">
        <div class="footer-row">
            <div class="footer-credit">
                Truck visuals use
                <a class="footer-link" href="https://kenney.nl/assets/car-kit" target="_blank" rel="noopener noreferrer">
                    <span class="footer-icon">K</span> Kenney Car Kit
                </a>
                assets under CC0.
            </div>
            <div class="footer-links">
                <a class="footer-link" href="https://www.linkedin.com/in/kanu-tomer/" target="_blank" rel="noopener noreferrer">
                    <span class="footer-icon">in</span> LinkedIn
                </a>
                <a class="footer-link" href="https://github.com/KanuTomer" target="_blank" rel="noopener noreferrer">
                    <span class="footer-icon">GH</span> GitHub
                </a>
                <a class="footer-link" href="mailto:kanutomer123@gmail.com">
                    <span class="footer-icon">@</span> Email
                </a>
            </div>
        </div>
    </footer>
    """


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
            gr.HTML(build_badge_html())

            with gr.Column(elem_classes=["command-panel"]):
                gr.Markdown("## Run setup")
                with gr.Row(equal_height=False, elem_classes=["command-bar"]):
                    with gr.Column(scale=1, min_width=220, elem_classes=["command-cell"]):
                        gr.Markdown("Dataset source", elem_classes=["field-heading"])
                        dataset_source = gr.Radio(
                            choices=["Demo dataset", "Upload dataset"],
                            value="Demo dataset",
                            label=None,
                            show_label=False,
                        )
                        gr.Markdown("Demo dataset", elem_classes=["field-heading"])
                        demo_dataset = gr.Radio(
                            choices=demo_dataset_options(),
                            value=default_dataset,
                            label=None,
                            show_label=False,
                            elem_classes=["dataset-button-radio"],
                        )
                        upload_file = gr.File(
                            label="Dataset file",
                            file_types=[".json"],
                            visible=False,
                        )
                    with gr.Column(scale=1, min_width=320, elem_classes=["command-cell"]):
                        gr.Markdown("Truck body", elem_classes=["field-heading"])
                        truck_body_choice = gr.Radio(
                            choices=TRUCK_BODY_CHOICES,
                            value=default_truck_body_key(),
                            label=None,
                            show_label=False,
                            elem_classes=["truck-body-card-radio"],
                        )
                        with gr.Column(elem_classes=["hidden-state-controls"]):
                            truck_preset = gr.Radio(
                                choices=preset_names(),
                                value=default_truck,
                                label=None,
                                show_label=False,
                            )
                            truck_variant = gr.Radio(
                                choices=variant_names(default_truck),
                                value=default_variant,
                                label=None,
                                show_label=False,
                            )
                    with gr.Column(scale=1, min_width=230, elem_classes=["command-cell"]):
                        with gr.Row():
                            with gr.Column(elem_classes=["slider-stack"]):
                                gr.Markdown("Population", elem_classes=["field-heading"])
                                population_slider = gr.Slider(
                                    10,
                                    60,
                                    value=10,
                                    step=10,
                                    label=None,
                                    show_label=False,
                                    interactive=True,
                                )
                                gr.Markdown("Generations", elem_classes=["field-heading"])
                                generations_slider = gr.Slider(
                                    2,
                                    60,
                                    value=2,
                                    step=1,
                                    label=None,
                                    show_label=False,
                                    interactive=True,
                                )
                        run_button = gr.Button("Run proposed GA", variant="primary")
                dataset_status = gr.Markdown(
                    dataset_helper("Demo dataset", bundle=default_bundle),
                    elem_classes=["truck-details", "dataset-status-strip"],
                )

            with gr.Column(elem_classes=["stage-viewer-panel"]):
                dashboard_header = gr.HTML(default_dashboard[4])
                with gr.Column(elem_classes=["packing-viewer-section"]):
                    gr.Markdown("### Animated 3D loading viewer")
                    packing_viewer = gr.HTML(default_dashboard[11])

            with gr.Row(equal_height=False, elem_classes=["run-output-strip"]):
                with gr.Column(scale=1, min_width=260, elem_classes=["run-status-panel"]):
                    run_status = gr.Markdown(
                        default_dashboard[3],
                        elem_classes=["run-status"],
                    )
                with gr.Column(scale=3, min_width=420, elem_classes=["metrics-strip-panel"]):
                    result_metrics = gr.HTML(default_dashboard[6])

            with gr.Column(elem_classes=["result-panel", "secondary-panel"]):
                dataset_summary = gr.HTML(dataset_summary_html(default_bundle))
                validation_status = gr.HTML(default_dashboard[5])
                with gr.Row(elem_classes=["secondary-grid"]):
                    with gr.Column(scale=1):
                        gr.Markdown("### Box preview")
                        box_preview = gr.Dataframe(
                            headers=BOX_PREVIEW_HEADERS,
                            value=box_preview_rows(default_bundle),
                            label="Box preview",
                            show_label=False,
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("### Convergence preview")
                        convergence_preview = gr.HTML(default_dashboard[9])
                with gr.Row(elem_classes=["secondary-grid"]):
                    with gr.Column(scale=1):
                        gr.Markdown("### Customer geometry")
                        route_plot = gr.HTML(default_dashboard[8])
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

            gr.HTML(footer_html())

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
        truck_body_choice.change(
            fn=update_truck_body_choice,
            inputs=[dataset_source, demo_dataset, upload_file, truck_body_choice],
            outputs=[
                truck_preset,
                truck_variant,
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
