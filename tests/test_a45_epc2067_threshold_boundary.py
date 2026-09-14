import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a45_stage2_interval3_sweep import (
    NEGATIVE_PERCENTAGES,
    source_label,
)
from experiments.track_A_periodic_steady_state.build_a45_stage2_refinement import (
    NEGATIVE_BASIS_POINTS,
)
from experiments.track_A_periodic_steady_state.build_a45_stage2_fine_refinement import (
    NEGATIVE_BASIS_POINTS as FINE_NEGATIVE_BASIS_POINTS,
)


class A45BoundaryTests(unittest.TestCase):
    def test_grid_matches_a42_convention(self):
        self.assertEqual(NEGATIVE_PERCENTAGES, tuple(range(1, 11)))

    def test_source_regions_remain_distinct(self):
        self.assertEqual(source_label(1), "P24_EXPLICIT")
        self.assertEqual(source_label(2), "P24_EXPLICIT")
        self.assertEqual(source_label(3), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(4), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(5), "P25_SUPPLEMENT")
        self.assertEqual(source_label(10), "P25_SUPPLEMENT")

    def test_refinement_grid_is_predeclared(self):
        self.assertEqual(NEGATIVE_BASIS_POINTS, tuple(range(2200, 2301, 10)))

    def test_fine_refinement_grid_is_predeclared(self):
        self.assertEqual(FINE_NEGATIVE_BASIS_POINTS, tuple(range(2200, 2211)))

    def test_coarse_grid_never_reaches_zvs(self):
        # Documents the honest EXPECTED_FAILURE-shaped observation that the
        # A42-convention 1%-10% grid does not bracket the EPC2067-candidate
        # threshold (unlike A42's GS61008T-based grid, which did): the much
        # larger CH_TOTAL/CL_TOTAL pushes the threshold well outside 1%-10%.
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A45_epc2067_table3_candidate_commutation/coarse_results.json"
        )
        rows = json.loads(path.read_text())
        self.assertEqual(len(rows), 10)
        self.assertFalse(any(row["natural_zvs_after_release"] for row in rows))

    def test_recorded_threshold_remains_a_bracket(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A45_epc2067_table3_candidate_commutation/refinement_results.json"
        )
        rows = json.loads(path.read_text())
        fine = {
            row["negative_fraction_pct"]: row
            for row in rows
            if row["case"].startswith("a45_fine")
        }
        self.assertFalse(fine[22.04]["natural_zvs_after_release"])
        self.assertTrue(fine[22.05]["natural_zvs_after_release"])
        self.assertFalse(fine[22.04]["high_side_admitted"])
        self.assertTrue(fine[22.05]["high_side_admitted"])

    def test_threshold_moved_up_relative_to_a42_gs61008t_bracket(self):
        # A42's GS61008T-based bracket was 7.76%-7.77%. EPC2067's ~9.7x/7.2x
        # larger CH_TOTAL/CL_TOTAL should require MORE negative current, not
        # less -- this is the physical-direction check RESULTS.md reports.
        path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A45_epc2067_table3_candidate_commutation/refinement_results.json"
        )
        rows = json.loads(path.read_text())
        fine = {
            row["negative_fraction_pct"]: row
            for row in rows
            if row["case"].startswith("a45_fine")
        }
        self.assertGreater(22.05, 7.77)
        self.assertTrue(fine[22.05]["natural_zvs_after_release"])


if __name__ == "__main__":
    unittest.main()
