"""Tests for bundled demo datasets and unit display helpers."""

from __future__ import annotations

import unittest

from truck_loading.data import (
    DEMO_DATASET_FILES,
    demo_dataset_options,
    format_box_dimension,
    format_truck_dimension,
    load_demo_dataset,
    load_uploaded_dataset,
)


EXPECTED_COUNTS = {
    "50 customers - group 1": (50, 126),
    "50 customers - group 2": (50, 120),
    "100 customers - group 1": (100, 252),
    "100 customers - group 2": (100, 240),
}


class DatasetUtilityTests(unittest.TestCase):
    def test_all_bundled_demo_datasets_load(self) -> None:
        self.assertEqual(len(DEMO_DATASET_FILES), 4)
        self.assertEqual(demo_dataset_options(), list(EXPECTED_COUNTS))

        for label, (expected_customers, expected_boxes) in EXPECTED_COUNTS.items():
            with self.subTest(label=label):
                bundle = load_demo_dataset(label)
                self.assertEqual(bundle.summary.real_customer_count, expected_customers)
                self.assertEqual(bundle.summary.box_count, expected_boxes)

    def test_demo_boxes_fit_source_container(self) -> None:
        for label in demo_dataset_options():
            with self.subTest(label=label):
                bundle = load_demo_dataset(label)
                self.assertEqual(bundle.summary.oversized_box_count, 0)

    def test_uploaded_dataset_path_loads_expected_schema(self) -> None:
        sample = "samples/conference_batch/XML50_1111_01_merged_with_boxes_norm.json"
        bundle = load_uploaded_dataset({"path": sample})

        self.assertEqual(bundle.summary.real_customer_count, 50)
        self.assertEqual(bundle.summary.box_count, 126)
        self.assertIn("Uploaded -", bundle.label)

    def test_dimension_formatting(self) -> None:
        self.assertEqual(format_truck_dimension(4000), "4.0 m / 13.1 ft")
        self.assertEqual(format_box_dimension(25), "2.5 cm / 1.0 in")
        self.assertEqual(format_box_dimension(400), "0.4 m / 1.3 ft")


if __name__ == "__main__":
    unittest.main()
