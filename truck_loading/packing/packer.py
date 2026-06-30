"""Rotation-enabled free-space packing for truck loading visualizations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any


ORIENTATIONS: tuple[tuple[str, str, str], ...] = (
    ("l", "w", "h"),
    ("l", "h", "w"),
    ("w", "l", "h"),
    ("w", "h", "l"),
    ("h", "l", "w"),
    ("h", "w", "l"),
)
EPSILON = 1e-6


@dataclass(frozen=True)
class FreeSpace:
    x: float
    y: float
    z: float
    l: float
    w: float
    h: float

    def fits(self, l: float, w: float, h: float) -> bool:
        return l <= self.l + EPSILON and w <= self.w + EPSILON and h <= self.h + EPSILON


def _box_dims(box: dict[str, Any]) -> dict[str, float]:
    return {
        "l": float(box["length"]),
        "w": float(box["width"]),
        "h": float(box["height"]),
    }


def try_place_box_in_space(box: dict[str, Any], free_space: FreeSpace) -> tuple[float, float, float] | None:
    dims = _box_dims(box)
    candidates: list[tuple[float, tuple[float, float, float]]] = []
    for orientation in ORIENTATIONS:
        l = dims[orientation[0]]
        w = dims[orientation[1]]
        h = dims[orientation[2]]
        if free_space.fits(l, w, h):
            leftover = max(free_space.l - l, 0) * max(free_space.w - w, 0) * max(free_space.h - h, 0)
            candidates.append((leftover, (l, w, h)))
    if not candidates:
        return None
    candidates.sort(key=lambda candidate: candidate[0])
    return candidates[0][1]


def place_boxes_in_container(
    container: dict[str, float],
    boxes: list[dict[str, Any]],
    max_boxes: int | None = None,
) -> tuple[list[dict[str, float | str]], float, int]:
    """Place boxes with a deterministic first-fit free-space heuristic.

    This is adapted from the source packer and kept app-local so the original
    research prototype remains separate.
    """
    free_spaces = [FreeSpace(0, 0, 0, float(container["L"]), float(container["W"]), float(container["H"]))]
    placements: list[dict[str, float | str]] = []
    packed_volume = 0.0

    for box in boxes:
        if max_boxes is not None and len(placements) >= max_boxes:
            break

        for index, free_space in enumerate(free_spaces):
            chosen = try_place_box_in_space(box, free_space)
            if chosen is None:
                continue

            l, w, h = chosen
            placement = {
                "box_id": str(box["box_id"]),
                "x": free_space.x,
                "y": free_space.y,
                "z": free_space.z,
                "l": l,
                "w": w,
                "h": h,
            }
            placements.append(placement)
            packed_volume += l * w * h

            right = FreeSpace(free_space.x + l, free_space.y, free_space.z, free_space.l - l, free_space.w, free_space.h)
            front = FreeSpace(free_space.x, free_space.y + w, free_space.z, l, free_space.w - w, free_space.h)
            top = FreeSpace(free_space.x, free_space.y, free_space.z + h, l, w, free_space.h - h)
            children = [
                space
                for space in (right, front, top)
                if space.l > EPSILON and space.w > EPSILON and space.h > EPSILON
            ]
            del free_spaces[index]
            free_spaces = children + free_spaces
            break

    return placements, packed_volume, len(placements)


def placement_inside_container(placement: dict[str, Any], container: dict[str, float]) -> bool:
    return (
        float(placement["x"]) >= -EPSILON
        and float(placement["y"]) >= -EPSILON
        and float(placement["z"]) >= -EPSILON
        and float(placement["x"]) + float(placement["l"]) <= float(container["L"]) + EPSILON
        and float(placement["y"]) + float(placement["w"]) <= float(container["W"]) + EPSILON
        and float(placement["z"]) + float(placement["h"]) <= float(container["H"]) + EPSILON
    )


def placements_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return not (
        float(first["x"]) + float(first["l"]) <= float(second["x"]) + EPSILON
        or float(second["x"]) + float(second["l"]) <= float(first["x"]) + EPSILON
        or float(first["y"]) + float(first["w"]) <= float(second["y"]) + EPSILON
        or float(second["y"]) + float(second["w"]) <= float(first["y"]) + EPSILON
        or float(first["z"]) + float(first["h"]) <= float(second["z"]) + EPSILON
        or float(second["z"]) + float(second["h"]) <= float(first["z"]) + EPSILON
    )


def validate_placements(placements: list[dict[str, Any]], container: dict[str, float]) -> list[str]:
    errors: list[str] = []
    for placement in placements:
        if not placement_inside_container(placement, container):
            errors.append(f"Box {placement.get('box_id')} exceeds container bounds.")
    for first, second in combinations(placements, 2):
        if placements_overlap(first, second):
            errors.append(f"Boxes {first.get('box_id')} and {second.get('box_id')} overlap.")
    return errors
