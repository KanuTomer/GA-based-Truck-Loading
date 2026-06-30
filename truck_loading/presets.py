"""Truck presets and 3D asset metadata for the visual loading demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from truck_loading.data.units import format_truck_dimensions


ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets" / "kenney-car-kit"
MODEL_ROOT = ASSET_ROOT / "models"
PREVIEW_ROOT = ASSET_ROOT / "previews"
DEFAULT_PRESET_NAME = "City Mini Truck"


@dataclass(frozen=True)
class TruckModelVariant:
    name: str
    model_file: str
    preview_file: str
    description: str

    @property
    def model_path(self) -> Path:
        return MODEL_ROOT / self.model_file

    @property
    def preview_path(self) -> Path:
        return PREVIEW_ROOT / self.preview_file


@dataclass(frozen=True)
class TruckPreset:
    name: str
    indian_equivalent: str
    length_ft: float
    width_ft: float
    height_ft: float
    length_mm: int
    width_mm: int
    height_mm: int
    description: str
    variants: tuple[TruckModelVariant, ...]
    default_variant: str

    @property
    def is_custom(self) -> bool:
        return False

    def get_variant(self, variant_name: str | None = None) -> TruckModelVariant:
        selected = variant_name or self.default_variant
        for variant in self.variants:
            if variant.name == selected:
                return variant
        return self.variants[0]


TRUCK_PRESETS: tuple[TruckPreset, ...] = (
    TruckPreset(
        name="City Mini Truck",
        indian_equivalent="Tata Ace / Mini Truck and Pickup / Bolero class",
        length_ft=7.0,
        width_ft=4.8,
        height_ft=4.8,
        length_mm=2134,
        width_mm=1463,
        height_mm=1463,
        description=(
            "Compact urban delivery profile for smaller customer drops and tight city routes."
        ),
        variants=(
            TruckModelVariant(
                name="Open pickup body",
                model_file="truck.glb",
                preview_file="truck.png",
                description="Open-bed pickup styling for a small Indian utility truck analogue.",
            ),
            TruckModelVariant(
                name="Closed delivery van",
                model_file="van.glb",
                preview_file="van.png",
                description="Closed-body van styling for parcel-style city delivery demos.",
            ),
        ),
        default_variant="Open pickup body",
    ),
    TruckPreset(
        name="Medium Cargo Truck",
        indian_equivalent="Tata 407 / Eicher 14 ft class",
        length_ft=14.0,
        width_ft=6.0,
        height_ft=6.5,
        length_mm=4267,
        width_mm=1829,
        height_mm=1981,
        description=(
            "Mid-size cargo profile with enough length and height to make the packed load readable."
        ),
        variants=(
            TruckModelVariant(
                name="Covered cargo body",
                model_file="delivery.glb",
                preview_file="delivery.png",
                description="Covered cargo styling for a regional delivery truck analogue.",
            ),
            TruckModelVariant(
                name="Flatbed utility body",
                model_file="truck-flat.glb",
                preview_file="truck-flat.png",
                description="Flatbed utility styling for visually open cargo-loading demos.",
            ),
        ),
        default_variant="Covered cargo body",
    ),
)


TRUCK_PRESET_BY_NAME = {preset.name: preset for preset in TRUCK_PRESETS}


def preset_names() -> list[str]:
    return [preset.name for preset in TRUCK_PRESETS]


def get_preset(name: str | None) -> TruckPreset:
    return TRUCK_PRESET_BY_NAME.get(name or DEFAULT_PRESET_NAME, TRUCK_PRESET_BY_NAME[DEFAULT_PRESET_NAME])


def variant_names(preset_name: str | None) -> list[str]:
    return [variant.name for variant in get_preset(preset_name).variants]


def default_variant_name(preset_name: str | None) -> str:
    return get_preset(preset_name).default_variant


def get_variant(preset_name: str | None, variant_name: str | None = None) -> TruckModelVariant:
    return get_preset(preset_name).get_variant(variant_name)


def model_path_for(preset_name: str | None, variant_name: str | None = None) -> str:
    return str(get_variant(preset_name, variant_name).model_path)


def preview_path_for(preset_name: str | None, variant_name: str | None = None) -> str:
    return str(get_variant(preset_name, variant_name).preview_path)


def format_dimensions(name: str | None) -> str:
    preset = get_preset(name)
    variants = ", ".join(variant.name for variant in preset.variants)

    return (
        f"### {preset.name}\n"
        f"{preset.description}\n\n"
        f"**Closest Indian equivalent:** {preset.indian_equivalent}\n\n"
        f"**Body styles:** {variants}\n\n"
        f"| Unit | Length | Width | Height |\n"
        f"|---|---:|---:|---:|\n"
        f"| Meters | {preset.length_mm / 1000:.1f} | {preset.width_mm / 1000:.1f} | {preset.height_mm / 1000:.1f} |\n"
        f"| Feet | {preset.length_mm / 304.8:.1f} | {preset.width_mm / 304.8:.1f} | {preset.height_mm / 304.8:.1f} |"
    )


def format_variant_description(preset_name: str | None, variant_name: str | None = None) -> str:
    preset = get_preset(preset_name)
    variant = preset.get_variant(variant_name)
    display_dims = format_truck_dimensions(preset.length_mm, preset.width_mm, preset.height_mm)

    return (
        f"### {variant.name}\n"
        f"{variant.description}\n\n"
        f"**Truck class:** {preset.name}\n\n"
        f"**Internal load space:** {display_dims}"
    )
