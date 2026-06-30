"""Tests for M4 dataset readiness validation."""

from __future__ import annotations

import copy
import unittest

from truck_loading.data import (
    has_blocking_results,
    load_demo_dataset,
    validate_data_quality,
)


DEMO_LABELS = (
    "50 customers - group 1111 (XML50_1111_01)",
    "50 customers - group 1142 (XML50_1142_01)",
    "100 customers - group 1111 (XML100_1111_01)",
    "100 customers - group 1142 (XML100_1142_01)",
)


class ValidationTests(unittest.TestCase):
    def test_all_demo_datasets_are_ready(self) -> None:
        for label in DEMO_LABELS:
            with self.subTest(label=label):
                bundle = load_demo_dataset(label)
                results = validate_data_quality(bundle.data, truck_dimensions_mm=(4267, 1829, 1981))

                self.assertFalse(has_blocking_results(results))
                self.assertEqual(results[0].severity, "success")

    def test_missing_keys_are_blocking(self) -> None:
        results = validate_data_quality({"customers": [], "boxes": []})

        self.assertTrue(has_blocking_results(results))
        self.assertIn("Missing dataset keys", results[0].title)

    def test_oversized_boxes_are_blocking(self) -> None:
        data = copy.deepcopy(load_demo_dataset(DEMO_LABELS[0]).data)
        data["boxes"][0]["length"] = 9999

        results = validate_data_quality(data, truck_dimensions_mm=(4267, 1829, 1981))

        self.assertTrue(has_blocking_results(results))
        self.assertTrue(any("exceed" in result.title for result in results))

    def test_duplicate_and_missing_box_references_are_reported(self) -> None:
        data = copy.deepcopy(load_demo_dataset(DEMO_LABELS[0]).data)
        data["customers"][1]["assigned_boxes"].append("missing_box")
        data["customers"][2]["assigned_boxes"].append(data["customers"][1]["assigned_boxes"][0])

        results = validate_data_quality(data)

        self.assertTrue(has_blocking_results(results))
        titles = {result.title for result in results}
        self.assertIn("Missing box references", titles)
        self.assertIn("Duplicate box assignments", titles)

    def test_customer_cap_is_blocking(self) -> None:
        data = copy.deepcopy(load_demo_dataset(DEMO_LABELS[0]).data)
        template = copy.deepcopy(data["customers"][1])
        for customer_id in range(1000, 1052):
            extra = copy.deepcopy(template)
            extra["id"] = customer_id
            extra["customer_id"] = customer_id
            extra["assigned_boxes"] = []
            data["customers"].append(extra)

        results = validate_data_quality(data)

        self.assertTrue(has_blocking_results(results))
        self.assertTrue(any(result.title == "Customer cap exceeded" for result in results))


if __name__ == "__main__":
    unittest.main()
