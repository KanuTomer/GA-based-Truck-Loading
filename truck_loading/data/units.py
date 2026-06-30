"""User-facing dimension and volume formatting helpers."""

from __future__ import annotations

MM_PER_METER = 1000.0
MM_PER_FOOT = 304.8
MM_PER_CM = 10.0
MM_PER_INCH = 25.4
MM3_PER_LITER = 1_000_000.0


def meters(mm: float) -> float:
    return mm / MM_PER_METER


def feet(mm: float) -> float:
    return mm / MM_PER_FOOT


def centimeters(mm: float) -> float:
    return mm / MM_PER_CM


def inches(mm: float) -> float:
    return mm / MM_PER_INCH


def liters(mm3: float) -> float:
    return mm3 / MM3_PER_LITER


def format_truck_dimension(mm: float) -> str:
    """Format truck/container dimensions using meters and feet to one decimal."""
    return f"{meters(mm):.1f} m / {feet(mm):.1f} ft"


def format_truck_dimensions(length_mm: float, width_mm: float, height_mm: float) -> str:
    return (
        f"{format_truck_dimension(length_mm)} x "
        f"{format_truck_dimension(width_mm)} x "
        f"{format_truck_dimension(height_mm)}"
    )


def format_box_dimension(mm: float) -> str:
    """Use cm/in for small boxes that would round to 0.0 m."""
    if round(meters(mm), 1) == 0.0:
        return f"{centimeters(mm):.1f} cm / {inches(mm):.1f} in"
    return format_truck_dimension(mm)


def format_box_dimensions(length_mm: float, width_mm: float, height_mm: float) -> str:
    return (
        f"{format_box_dimension(length_mm)} x "
        f"{format_box_dimension(width_mm)} x "
        f"{format_box_dimension(height_mm)}"
    )


def format_liters(mm3: float) -> str:
    return f"{liters(mm3):.1f} L"
