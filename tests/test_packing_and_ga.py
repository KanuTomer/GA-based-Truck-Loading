"""Tests for M5 packing placements and proposed-GA output."""

from __future__ import annotations

import unittest

from truck_loading.data import load_demo_dataset
from truck_loading.ga import ProposedGAConfig, run_proposed_ga
from truck_loading.packing import (
    place_boxes_in_container,
    placement_inside_container,
    placements_overlap,
)
from truck_loading.presets import get_preset


class PackingAndGATests(unittest.TestCase):
    def test_packer_places_rotated_boxes_inside_container(self) -> None:
        container = {"L": 100.0, "W": 80.0, "H": 60.0}
        boxes = [
            {"box_id": "wide", "length": 80.0, "width": 100.0, "height": 20.0},
            {"box_id": "small", "length": 20.0, "width": 20.0, "height": 20.0},
        ]

        placements, _packed_volume, placed_count = place_boxes_in_container(container, boxes)

        self.assertEqual(placed_count, 2)
        self.assertTrue(all(placement_inside_container(placement, container) for placement in placements))
        self.assertFalse(placements_overlap(placements[0], placements[1]))

    def test_proposed_ga_returns_routes_history_and_metadata(self) -> None:
        bundle = load_demo_dataset("50 customers - group 1111 (XML50_1111_01)")
        preset = get_preset("Medium Cargo Truck")
        result = run_proposed_ga(
            bundle.data,
            (preset.length_mm, preset.width_mm, preset.height_mm),
            ProposedGAConfig(population_size=10, generations=3, seed=7, max_boxes_per_route=48),
        )

        self.assertEqual(result["model"], "proposed_ga")
        self.assertEqual(len(result["history"]), 3)
        self.assertGreater(result["best_info"]["route_count"], 0)
        self.assertEqual(result["best_info"]["boxes_total"], bundle.summary.box_count)

        first_route = result["best_info"]["routes"][0]
        self.assertIn("placements", first_route)
        self.assertGreater(first_route["boxes_packed"], 0)
        first_placement = first_route["placements"][0]
        self.assertIn("customer_id", first_placement)
        self.assertIn("customer_label", first_placement)
        self.assertIn("color", first_placement)

    def test_unplaceable_box_is_reported_as_unpacked(self) -> None:
        data = {
            "container": {"L": 100, "W": 100, "H": 100},
            "customers": [
                {"id": 0, "customer_id": 0, "x": 0, "y": 0, "is_depot": True, "assigned_boxes": []},
                {"id": 1, "customer_id": 1, "x": 1, "y": 1, "assigned_boxes": ["too_big"]},
            ],
            "boxes": [{"box_id": "too_big", "length": 200, "width": 100, "height": 100}],
        }

        result = run_proposed_ga(
            data,
            (100.0, 100.0, 100.0),
            ProposedGAConfig(population_size=10, generations=2, seed=3),
        )

        route = result["best_info"]["routes"][0]
        self.assertFalse(route["feasible"])
        self.assertEqual(route["boxes_packed"], 0)
        self.assertEqual(route["unpacked_box_ids"], ["too_big"])


if __name__ == "__main__":
    unittest.main()
