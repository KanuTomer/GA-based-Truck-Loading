"""Guard tests for public demo labels and hosting-facing UI copy."""

from __future__ import annotations

import unittest

import app
from truck_loading.data import demo_dataset_options


class PublicSurfaceTests(unittest.TestCase):
    def test_public_badge_has_no_local_debug_copy(self) -> None:
        badge = app.build_badge_html()

        self.assertIn("Public demo build", badge)
        self.assertNotIn("M5", badge)
        self.assertNotIn("127.0.0.1", badge)
        self.assertNotIn("localhost", badge.lower())

    def test_truck_body_options_are_the_four_public_cards(self) -> None:
        self.assertEqual(
            app.TRUCK_BODY_OPTIONS,
            (
                ("City Mini Truck", "Open pickup body"),
                ("City Mini Truck", "Closed delivery van"),
                ("Medium Cargo Truck", "Covered cargo body"),
                ("Medium Cargo Truck", "Flatbed utility body"),
            ),
        )

    def test_demo_dataset_labels_are_public_grouped_labels(self) -> None:
        labels = demo_dataset_options()

        self.assertEqual(
            labels,
            [
                "G1 - 50",
                "G1 - 100",
                "G1 - 150",
                "G1 - 200",
                "G2 - 50",
                "G2 - 100",
                "G2 - 150",
                "G2 - 200",
            ],
        )
        self.assertFalse(any("XML" in label or "1111" in label or "1142" in label for label in labels))

    def test_public_surface_has_no_old_model_selector_copy(self) -> None:
        surface = "\n".join([app.hero_html(), app.build_badge_html(), app.footer_html()])

        self.assertNotIn("baseline_a", surface)
        self.assertNotIn("baseline_b", surface)
        self.assertNotIn("baseline_c", surface)
        self.assertNotIn("model selector", surface.lower())


if __name__ == "__main__":
    unittest.main()
