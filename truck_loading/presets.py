"""Truck/container presets for the visual loading demo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TruckPreset:
    name: str
    length_ft: float | None
    width_ft: float | None
    height_ft: float | None
    length_mm: int | None
    width_mm: int | None
    height_mm: int | None
    description: str

    @property
    def is_custom(self) -> bool:
        return self.length_mm is None or self.width_mm is None or self.height_mm is None


TRUCK_PRESETS: tuple[TruckPreset, ...] = (
    TruckPreset(
        name="Three-Wheeler Cargo",
        length_ft=5.5,
        width_ft=4.5,
        height_ft=5.0,
        length_mm=1676,
        width_mm=1372,
        height_mm=1524,
        description="Compact city cargo profile for small parcel-style loads.",
    ),
    TruckPreset(
        name="Tata Ace / Mini Truck",
        length_ft=7.0,
        width_ft=4.8,
        height_ft=4.8,
        length_mm=2134,
        width_mm=1463,
        height_mm=1463,
        description="Small commercial load body for dense urban delivery demos.",
    ),
    TruckPreset(
        name="Pickup / Bolero Type",
        length_ft=8.0,
        width_ft=5.0,
        height_ft=4.8,
        length_mm=2438,
        width_mm=1524,
        height_mm=1463,
        description="Pickup-sized load bay for short regional routes.",
    ),
    TruckPreset(
        name="Tata 407 Type",
        length_ft=9.0,
        width_ft=5.5,
        height_ft=5.5,
        length_mm=2743,
        width_mm=1676,
        height_mm=1676,
        description="Classic light truck profile for balanced small-fleet demos.",
    ),
    TruckPreset(
        name="Eicher 14 ft",
        length_ft=14.0,
        width_ft=6.0,
        height_ft=6.5,
        length_mm=4267,
        width_mm=1829,
        height_mm=1981,
        description="Mid-size commercial cargo space with more visible packing depth.",
    ),
    TruckPreset(
        name="Eicher 17 ft",
        length_ft=17.0,
        width_ft=6.5,
        height_ft=7.0,
        length_mm=5182,
        width_mm=1981,
        height_mm=2134,
        description="Larger load body for multi-route packing demonstrations.",
    ),
    TruckPreset(
        name="Eicher 19 ft",
        length_ft=19.0,
        width_ft=7.0,
        height_ft=7.0,
        length_mm=5791,
        width_mm=2134,
        height_mm=2134,
        description="High-capacity rigid truck profile with wide visual staging.",
    ),
    TruckPreset(
        name="Taurus / 22 ft Truck",
        length_ft=22.0,
        width_ft=7.5,
        height_ft=7.0,
        length_mm=6706,
        width_mm=2286,
        height_mm=2134,
        description="Large truck body for dramatic loading animations.",
    ),
    TruckPreset(
        name="24 ft Container Body",
        length_ft=24.0,
        width_ft=7.5,
        height_ft=7.5,
        length_mm=7315,
        width_mm=2286,
        height_mm=2286,
        description="Container-style body for high-volume route packing.",
    ),
    TruckPreset(
        name="32 ft Container Body",
        length_ft=32.0,
        width_ft=8.0,
        height_ft=8.0,
        length_mm=9754,
        width_mm=2438,
        height_mm=2438,
        description="Full-scale container body for maximum visual contrast.",
    ),
    TruckPreset(
        name="Custom",
        length_ft=None,
        width_ft=None,
        height_ft=None,
        length_mm=None,
        width_mm=None,
        height_mm=None,
        description="Use manually entered internal cargo dimensions.",
    ),
)


TRUCK_PRESET_BY_NAME = {preset.name: preset for preset in TRUCK_PRESETS}


def preset_names() -> list[str]:
    return [preset.name for preset in TRUCK_PRESETS]


def get_preset(name: str) -> TruckPreset:
    return TRUCK_PRESET_BY_NAME.get(name, TRUCK_PRESET_BY_NAME["Tata 407 Type"])


def format_dimensions(name: str) -> str:
    preset = get_preset(name)
    if preset.is_custom:
        return (
            "### Custom cargo body\n"
            "Enter internal load-space dimensions in millimeters. These values will drive "
            "validation and the future 3D truck-packing scene."
        )

    return (
        f"### {preset.name}\n"
        f"{preset.description}\n\n"
        f"| Unit | Length | Width | Height |\n"
        f"|---|---:|---:|---:|\n"
        f"| Feet | {preset.length_ft:g} | {preset.width_ft:g} | {preset.height_ft:g} |\n"
        f"| Millimeters | {preset.length_mm:,} | {preset.width_mm:,} | {preset.height_mm:,} |"
    )

