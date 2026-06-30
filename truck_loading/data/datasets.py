"""Dataset loading, validation, and summaries for demo/uploaded datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .units import format_box_dimensions, format_liters, format_truck_dimensions


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_DATASET_ROOT = REPO_ROOT / "samples" / "conference_batch"
DEMO_DATASET_FILES: tuple[str, ...] = (
    "XML50_1111_01_merged_with_boxes_norm.json",
    "XML50_1142_01_merged_with_boxes_norm.json",
    "XML100_1111_01_merged_with_boxes_norm.json",
    "XML100_1142_01_merged_with_boxes_norm.json",
    "XML150_1111_01_merged_with_boxes_norm.json",
    "XML150_1142_01_merged_with_boxes_norm.json",
    "XML200_1111_01_merged_with_boxes_norm.json",
    "XML200_1142_01_merged_with_boxes_norm.json",
)
DEMO_DATASET_LABELS: tuple[str, ...] = (
    "50 customers - group 1",
    "50 customers - group 2",
    "100 customers - group 1",
    "100 customers - group 2",
    "150 customers - group 1",
    "150 customers - group 2",
    "200 customers - group 1",
    "200 customers - group 2",
)
THIN_BOX_THRESHOLD_MM = 75.0


class DatasetError(ValueError):
    """Raised when a JSON dataset does not match the expected app schema."""


@dataclass(frozen=True)
class DatasetSummary:
    label: str
    instance_name: str
    real_customer_count: int
    customer_count: int
    box_count: int
    boxes_per_customer_min: int
    boxes_per_customer_mean: float
    boxes_per_customer_max: int
    container_length_mm: float
    container_width_mm: float
    container_height_mm: float
    total_box_volume_mm3: float
    fill_percentage: float
    thin_box_count: int
    oversized_box_count: int

    @property
    def container_dimensions_display(self) -> str:
        return format_truck_dimensions(
            self.container_length_mm,
            self.container_width_mm,
            self.container_height_mm,
        )

    @property
    def total_box_volume_display(self) -> str:
        return format_liters(self.total_box_volume_mm3)

    @property
    def boxes_per_customer_display(self) -> str:
        return (
            f"{self.boxes_per_customer_min} - {self.boxes_per_customer_max} "
            f"(avg {self.boxes_per_customer_mean:.1f})"
        )


@dataclass(frozen=True)
class DatasetBundle:
    label: str
    data: dict[str, Any]
    summary: DatasetSummary


def demo_dataset_label(file_name: str) -> str:
    labels = dict(zip(DEMO_DATASET_FILES, DEMO_DATASET_LABELS, strict=True))
    return labels.get(file_name, file_name.replace("_merged_with_boxes_norm.json", ""))


def demo_dataset_options() -> list[str]:
    return list(DEMO_DATASET_LABELS)


def demo_dataset_path(label: str | None) -> Path:
    labels = dict(zip(demo_dataset_options(), DEMO_DATASET_FILES, strict=True))
    file_name = labels.get(label or "", DEMO_DATASET_FILES[0])
    return DEMO_DATASET_ROOT / file_name


def load_demo_dataset(label: str | None = None) -> DatasetBundle:
    path = demo_dataset_path(label)
    return load_dataset(path, label=demo_dataset_label(path.name))


def uploaded_file_path(uploaded_file: Any) -> Path | None:
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, (str, Path)):
        return Path(uploaded_file)
    if isinstance(uploaded_file, dict):
        value = uploaded_file.get("path") or uploaded_file.get("name")
        return Path(value) if value else None
    value = getattr(uploaded_file, "name", None)
    return Path(value) if value else None


def load_uploaded_dataset(uploaded_file: Any) -> DatasetBundle:
    path = uploaded_file_path(uploaded_file)
    if path is None:
        raise DatasetError("Upload a JSON dataset to preview its customers and boxes.")
    return load_dataset(path, label=f"Uploaded - {path.name}")


def load_dataset(path: Path, label: str | None = None) -> DatasetBundle:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DatasetError(f"Dataset file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetError(f"Dataset is not valid JSON: {path.name}") from exc

    validate_dataset(data)
    summary = summarize_dataset(data, label or data.get("instance_name") or path.name)
    return DatasetBundle(label=summary.label, data=data, summary=summary)


def validate_dataset(data: dict[str, Any]) -> None:
    missing = {"customers", "boxes", "container"} - set(data)
    if missing:
        raise DatasetError(f"Dataset is missing required keys: {', '.join(sorted(missing))}")
    if not isinstance(data["customers"], list) or not isinstance(data["boxes"], list):
        raise DatasetError("Dataset customers and boxes must be lists.")
    container = data["container"]
    if not isinstance(container, dict) or not {"L", "W", "H"} <= set(container):
        raise DatasetError("Dataset container must include L, W, and H dimensions.")

    for index, box in enumerate(data["boxes"], start=1):
        if not {"box_id", "length", "width", "height"} <= set(box):
            raise DatasetError(f"Box #{index} is missing box_id/length/width/height.")


def summarize_dataset(data: dict[str, Any], label: str) -> DatasetSummary:
    customers = data["customers"]
    boxes = data["boxes"]
    container = data["container"]
    real_customers = [customer for customer in customers if not customer.get("is_depot")]
    box_counts = [len(customer.get("assigned_boxes", [])) for customer in real_customers]
    if not box_counts:
        box_counts = [0]

    container_l = float(container["L"])
    container_w = float(container["W"])
    container_h = float(container["H"])
    container_volume = container_l * container_w * container_h
    volumes = [
        float(box["length"]) * float(box["width"]) * float(box["height"])
        for box in boxes
    ]
    total_volume = sum(volumes)
    thin_boxes = [
        box
        for box in boxes
        if min(float(box["length"]), float(box["width"]), float(box["height"]))
        < THIN_BOX_THRESHOLD_MM
    ]
    oversized_boxes = [
        box
        for box in boxes
        if float(box["length"]) > container_l
        or float(box["width"]) > container_w
        or float(box["height"]) > container_h
    ]

    return DatasetSummary(
        label=label,
        instance_name=label,
        real_customer_count=len(real_customers),
        customer_count=len(customers),
        box_count=len(boxes),
        boxes_per_customer_min=min(box_counts),
        boxes_per_customer_mean=mean(box_counts),
        boxes_per_customer_max=max(box_counts),
        container_length_mm=container_l,
        container_width_mm=container_w,
        container_height_mm=container_h,
        total_box_volume_mm3=total_volume,
        fill_percentage=(total_volume / container_volume * 100) if container_volume else 0,
        thin_box_count=len(thin_boxes),
        oversized_box_count=len(oversized_boxes),
    )


def box_preview_rows(bundle: DatasetBundle, limit: int = 8) -> list[list[str]]:
    rows: list[list[str]] = []
    for box in bundle.data["boxes"][:limit]:
        volume = float(box["length"]) * float(box["width"]) * float(box["height"])
        rows.append(
            [
                str(box["box_id"]),
                format_box_dimensions(
                    float(box["length"]),
                    float(box["width"]),
                    float(box["height"]),
                ),
                format_liters(volume),
            ]
        )
    return rows
