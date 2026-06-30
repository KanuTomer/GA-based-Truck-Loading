"""Validation results for dataset readiness and dashboard gating."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAX_REAL_CUSTOMERS = 200


@dataclass(frozen=True)
class ValidationResult:
    severity: str
    title: str
    message: str
    blocking: bool = False


def has_blocking_results(results: list[ValidationResult]) -> bool:
    return any(result.blocking for result in results)


def validate_data_quality(
    data: dict[str, Any],
    truck_dimensions_mm: tuple[float, float, float] | None = None,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    missing = {"customers", "boxes", "container"} - set(data)
    if missing:
        return [
            ValidationResult(
                severity="error",
                title="Missing dataset keys",
                message=f"Dataset is missing required keys: {', '.join(sorted(missing))}.",
                blocking=True,
            )
        ]

    customers = data.get("customers")
    boxes = data.get("boxes")
    container = data.get("container")
    if not isinstance(customers, list) or not isinstance(boxes, list):
        return [
            ValidationResult(
                severity="error",
                title="Invalid dataset lists",
                message="Customers and boxes must both be JSON lists.",
                blocking=True,
            )
        ]
    if not isinstance(container, dict) or not {"L", "W", "H"} <= set(container):
        return [
            ValidationResult(
                severity="error",
                title="Invalid container",
                message="Container must include numeric L, W, and H dimensions.",
                blocking=True,
            )
        ]

    container_dims = _numeric_dimensions(container, ("L", "W", "H"))
    if container_dims is None:
        results.append(
            ValidationResult(
                severity="error",
                title="Invalid container dimensions",
                message="Container dimensions must be positive numbers.",
                blocking=True,
            )
        )
        container_dims = (0.0, 0.0, 0.0)

    real_customers = [customer for customer in customers if not customer.get("is_depot")]
    if not real_customers:
        results.append(
            ValidationResult(
                severity="error",
                title="No real customers",
                message="At least one non-depot customer is required before a run can be prepared.",
                blocking=True,
            )
        )
    if len(real_customers) > MAX_REAL_CUSTOMERS:
        results.append(
            ValidationResult(
                severity="error",
                title="Customer cap exceeded",
                message=(
                    f"{len(real_customers)} real customers found; hosted demo runs are capped "
                    f"at {MAX_REAL_CUSTOMERS}."
                ),
                blocking=True,
            )
        )
    if not boxes:
        results.append(
            ValidationResult(
                severity="error",
                title="No boxes",
                message="At least one box is required for truck-loading visualization.",
                blocking=True,
            )
        )

    _validate_customer_ids(customers, results)
    box_ids, usable_boxes = _validate_boxes(boxes, results)
    _validate_assignments(real_customers, box_ids, results)
    _validate_oversized_boxes(usable_boxes, container_dims, "source container", results)
    if truck_dimensions_mm is not None:
        _validate_oversized_boxes(usable_boxes, truck_dimensions_mm, "selected truck", results)

    if not has_blocking_results(results):
        warning_count = sum(1 for result in results if result.severity == "warning")
        message = "Dataset is ready for the proposed-GA execution step."
        if warning_count:
            message = f"Dataset is usable with {warning_count} non-blocking warning(s)."
        results.insert(
            0,
            ValidationResult(
                severity="success",
                title="Dataset ready",
                message=message,
                blocking=False,
            ),
        )
    return results


def _numeric_dimensions(item: dict[str, Any], keys: tuple[str, str, str]) -> tuple[float, float, float] | None:
    try:
        values = tuple(float(item[key]) for key in keys)
    except (KeyError, TypeError, ValueError):
        return None
    if any(value <= 0 for value in values):
        return None
    return values


def _validate_customer_ids(customers: list[dict[str, Any]], results: list[ValidationResult]) -> None:
    ids: list[str] = []
    for index, customer in enumerate(customers, start=1):
        customer_id = customer.get("customer_id", customer.get("id"))
        if customer_id is None:
            results.append(
                ValidationResult(
                    severity="error",
                    title="Missing customer ID",
                    message=f"Customer row #{index} is missing customer_id/id.",
                    blocking=True,
                )
            )
            continue
        ids.append(str(customer_id))

    duplicates = sorted({customer_id for customer_id in ids if ids.count(customer_id) > 1})
    if duplicates:
        results.append(
            ValidationResult(
                severity="error",
                title="Duplicate customer IDs",
                message=f"Duplicate customer IDs found: {', '.join(duplicates[:5])}.",
                blocking=True,
            )
        )


def _validate_boxes(
    boxes: list[dict[str, Any]],
    results: list[ValidationResult],
) -> tuple[set[str], list[dict[str, float | str]]]:
    box_ids: list[str] = []
    usable_boxes: list[dict[str, float | str]] = []
    for index, box in enumerate(boxes, start=1):
        missing = {"box_id", "length", "width", "height"} - set(box)
        if missing:
            results.append(
                ValidationResult(
                    severity="error",
                    title="Invalid box row",
                    message=f"Box row #{index} is missing: {', '.join(sorted(missing))}.",
                    blocking=True,
                )
            )
            continue

        dims = _numeric_dimensions(box, ("length", "width", "height"))
        if dims is None:
            results.append(
                ValidationResult(
                    severity="error",
                    title="Invalid box dimensions",
                    message=f"Box {box.get('box_id', index)} has non-positive dimensions.",
                    blocking=True,
                )
            )
            continue

        box_id = str(box["box_id"])
        box_ids.append(box_id)
        length, width, height = dims
        usable_boxes.append({"box_id": box_id, "length": length, "width": width, "height": height})

    duplicates = sorted({box_id for box_id in box_ids if box_ids.count(box_id) > 1})
    if duplicates:
        results.append(
            ValidationResult(
                severity="error",
                title="Duplicate box IDs",
                message=f"Duplicate box IDs found: {', '.join(duplicates[:5])}.",
                blocking=True,
            )
        )
    return set(box_ids), usable_boxes


def _validate_assignments(
    real_customers: list[dict[str, Any]],
    box_ids: set[str],
    results: list[ValidationResult],
) -> None:
    assigned: list[str] = []
    missing_refs: list[str] = []
    for customer in real_customers:
        assigned_boxes = customer.get("assigned_boxes", [])
        if not isinstance(assigned_boxes, list):
            results.append(
                ValidationResult(
                    severity="error",
                    title="Invalid assigned boxes",
                    message="Each customer assigned_boxes field must be a list.",
                    blocking=True,
                )
            )
            continue
        for box_id in assigned_boxes:
            normalized = str(box_id)
            assigned.append(normalized)
            if normalized not in box_ids:
                missing_refs.append(normalized)

    duplicate_refs = sorted({box_id for box_id in assigned if assigned.count(box_id) > 1})
    if missing_refs:
        results.append(
            ValidationResult(
                severity="error",
                title="Missing box references",
                message=f"Assigned boxes not present in boxes list: {', '.join(sorted(set(missing_refs))[:5])}.",
                blocking=True,
            )
        )
    if duplicate_refs:
        results.append(
            ValidationResult(
                severity="error",
                title="Duplicate box assignments",
                message=f"Boxes assigned to more than one customer: {', '.join(duplicate_refs[:5])}.",
                blocking=True,
            )
        )

    unassigned = sorted(box_ids - set(assigned))
    if unassigned:
        results.append(
            ValidationResult(
                severity="warning",
                title="Unassigned boxes",
                message=f"{len(unassigned)} box(es) are not assigned to any non-depot customer.",
                blocking=False,
            )
        )


def _validate_oversized_boxes(
    boxes: list[dict[str, float | str]],
    dimensions: tuple[float, float, float],
    target_name: str,
    results: list[ValidationResult],
) -> None:
    length, width, height = dimensions
    oversized = [
        str(box["box_id"])
        for box in boxes
        if float(box["length"]) > length
        or float(box["width"]) > width
        or float(box["height"]) > height
    ]
    if oversized:
        results.append(
            ValidationResult(
                severity="error",
                title=f"Boxes exceed {target_name}",
                message=f"{len(oversized)} box(es) exceed the {target_name}: {', '.join(oversized[:5])}.",
                blocking=True,
            )
        )
