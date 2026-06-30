"""Tests for M5 packing placements and proposed-GA output."""

from __future__ import annotations

import unittest

from truck_loading.data import load_demo_dataset
from truck_loading.ga import ProposedGAConfig, run_proposed_ga
from truck_loading.ga.proposed import PackingCache
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
        self.assertIn("packing_strategy", first_route)
        self.assertIn("truck_volume_liters", first_route)
        self.assertIn("route_box_volume_liters", first_route)
        self.assertIn("diagnostics", result)
        self.assertIn("ga_search_time_seconds", result["diagnostics"])
        self.assertIn("exact_packing_time_seconds", result["diagnostics"])
        self.assertIn("packing_cache_hits", result["diagnostics"])
        first_placement = first_route["placements"][0]
        self.assertIn("customer_id", first_placement)
        self.assertIn("customer_label", first_placement)
        self.assertIn("color", first_placement)

    def test_route_splitting_uses_truck_packability_not_fixed_box_count(self) -> None:
        bundle = load_demo_dataset("50 customers - group 1111 (XML50_1111_01)")
        preset = get_preset("City Mini Truck")
        result = run_proposed_ga(
            bundle.data,
            (preset.length_mm, preset.width_mm, preset.height_mm),
            ProposedGAConfig(population_size=10, generations=2, seed=7),
        )

        route_box_counts = [route["boxes_total"] for route in result["best_info"]["routes"]]
        self.assertNotIn(48, route_box_counts)
        self.assertEqual(sum(route_box_counts), bundle.summary.box_count)

    def test_medium_truck_capacity_can_reduce_route_count(self) -> None:
        data = _capacity_sensitive_dataset()
        city = get_preset("City Mini Truck")
        medium = get_preset("Medium Cargo Truck")

        city_result = run_proposed_ga(
            data,
            (city.length_mm, city.width_mm, city.height_mm),
            ProposedGAConfig(population_size=10, generations=2, seed=1),
        )
        medium_result = run_proposed_ga(
            data,
            (medium.length_mm, medium.width_mm, medium.height_mm),
            ProposedGAConfig(population_size=10, generations=2, seed=1),
        )

        self.assertGreater(city_result["best_info"]["route_count"], medium_result["best_info"]["route_count"])
        self.assertEqual(medium_result["best_info"]["route_count"], 1)
        self.assertGreaterEqual(
            medium_result["best_info"]["boxes_packed"],
            city_result["best_info"]["boxes_packed"],
        )

    def test_search_uses_fast_estimator_before_exact_final_packing(self) -> None:
        bundle = load_demo_dataset("50 customers - group 1111 (XML50_1111_01)")
        preset = get_preset("City Mini Truck")
        config = ProposedGAConfig(population_size=10, generations=2, seed=11)

        result = run_proposed_ga(bundle.data, (preset.length_mm, preset.width_mm, preset.height_mm), config)

        diagnostics = result["diagnostics"]
        self.assertEqual(diagnostics["estimated_route_evaluations"], config.population_size * config.generations)
        self.assertLess(
            diagnostics["exact_route_evaluations"],
            diagnostics["estimated_route_evaluations"] * bundle.summary.real_customer_count,
        )
        self.assertGreater(result["best_info"]["boxes_packed"], 0)

    def test_packing_cache_reuses_repeated_route_evaluations(self) -> None:
        container = {"L": 1000.0, "W": 1000.0, "H": 1000.0}
        boxes = [
            {"box_id": "a", "length": 200, "width": 200, "height": 200},
            {"box_id": "b", "length": 300, "width": 200, "height": 100},
        ]
        cache = PackingCache(container)

        first = cache.best_result(boxes)
        second = cache.best_result(boxes)

        self.assertIs(first, second)
        self.assertEqual(cache.misses, 1)
        self.assertEqual(cache.hits, 1)

    def test_viewer_payload_includes_axis_labels(self) -> None:
        import app

        preset = get_preset("Medium Cargo Truck")
        result = {
            "best_info": {
                "routes": [
                    {
                        "route_index": 1,
                        "placements": [],
                    }
                ]
            }
        }

        payload = app.viewer_payload(result, preset.name, "Covered cargo body")

        self.assertIn("axis_labels", payload)
        self.assertIn("Length", payload["axis_labels"]["length"])
        self.assertIn("Width", payload["axis_labels"]["width"])
        self.assertIn("Height", payload["axis_labels"]["height"])
        self.assertFalse(payload["show_grid"])
        self.assertEqual({item["axis"] for item in payload["axis_callouts"]}, {"length", "width", "height"})

    def test_viewer_template_has_rotation_reset_and_no_grid_helper(self) -> None:
        from truck_loading.visualization.viewer import packing_viewer_html

        html = packing_viewer_html(
            {
                "container": {"L": 1000, "W": 800, "H": 600},
                "axis_labels": {"length": "Length 1.0 m", "width": "Width 0.8 m", "height": "Height 0.6 m"},
                "show_grid": False,
                "routes": [
                    {
                        "route_index": 1,
                        "customer_count": 1,
                        "boxes_packed": 0,
                        "boxes_total": 0,
                        "fill_rate": 0,
                        "distance": 0,
                        "customer_labels": ["Customer 1"],
                        "placements": [],
                    }
                ],
            }
        )

        self.assertIn("Reset view", html)
        self.assertIn("pointermove", html)
        self.assertIn("root.position.set(-center.x, -center.y, -center.z)", html)
        self.assertIn("camera.lookAt(0, 0, 0)", html)
        self.assertIn("Front", html)
        self.assertIn("Back", html)
        self.assertIn("const fixedPitch", html)
        self.assertNotIn("viewPitch += dy", html)
        self.assertNotIn("clientY - lastPointer.y", html)
        self.assertNotIn("GridHelper", html)

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

def _capacity_sensitive_dataset() -> dict:
    customers = [{"id": 0, "customer_id": 0, "x": 0, "y": 0, "is_depot": True, "assigned_boxes": []}]
    boxes = []
    for index in range(1, 8):
        box_id = f"box_{index}"
        customers.append(
            {
                "id": index,
                "customer_id": index,
                "x": index * 10,
                "y": index * 7,
                "assigned_boxes": [box_id],
            }
        )
        boxes.append(
            {
                "box_id": box_id,
                "length": 1000,
                "width": 1000,
                "height": 700,
            }
        )
    return {
        "container": {"L": 4267, "W": 1829, "H": 1981},
        "customers": customers,
        "boxes": boxes,
    }


if __name__ == "__main__":
    unittest.main()
