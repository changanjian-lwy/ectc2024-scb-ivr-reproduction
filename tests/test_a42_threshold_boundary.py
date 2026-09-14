import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a42_negative_current_threshold import (
    NEGATIVE_PERCENTAGES,
    source_label,
)
from experiments.track_A_periodic_steady_state.build_a42_threshold_refinement import (
    NEGATIVE_BASIS_POINTS,
)
from experiments.track_A_periodic_steady_state.build_a42_threshold_fine_refinement import (
    NEGATIVE_BASIS_POINTS as FINE_NEGATIVE_BASIS_POINTS,
)


class A42BoundaryTests(unittest.TestCase):
    def test_grid_is_fixed_before_results(self):
        self.assertEqual(NEGATIVE_PERCENTAGES, tuple(range(1, 11)))

    def test_source_regions_remain_distinct(self):
        self.assertEqual(source_label(1), "P24_EXPLICIT")
        self.assertEqual(source_label(2), "P24_EXPLICIT")
        self.assertEqual(source_label(3), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(4), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(5), "P25_SUPPLEMENT")
        self.assertEqual(source_label(10), "P25_SUPPLEMENT")

    def test_refinement_grid_is_predeclared(self):
        self.assertEqual(NEGATIVE_BASIS_POINTS, tuple(range(700, 801, 10)))

    def test_fine_refinement_grid_is_predeclared(self):
        self.assertEqual(FINE_NEGATIVE_BASIS_POINTS, tuple(range(770, 781)))

    def test_recorded_threshold_remains_a_bracket(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A42_zero_snubber_negative_current_threshold/refinement_results.json"
        )
        rows = json.loads(path.read_text())
        fine = {row["negative_fraction_pct"]: row for row in rows if row["case"].startswith("a42_fine")}
        self.assertFalse(fine[7.76]["natural_zvs_after_release"])
        self.assertTrue(fine[7.77]["natural_zvs_after_release"])
        self.assertFalse(fine[7.76]["high_side_admitted"])
        self.assertTrue(fine[7.77]["high_side_admitted"])


if __name__ == "__main__":
    unittest.main()
