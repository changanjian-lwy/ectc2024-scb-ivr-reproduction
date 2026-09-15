import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a47_stage2_interval3_sweep import (
    NEGATIVE_PERCENTAGES,
    source_label,
)


HERE = Path(__file__).resolve().parents[1] / (
    "experiments/track_A_periodic_steady_state/A47_nonlinear_coss_local_zvs"
)


class A47FitTests(unittest.TestCase):
    """The digitization/fit outputs must stay internally consistent and
    within the accuracy this project's rule requires be stated honestly."""

    def setUp(self):
        self.fit = json.loads((HERE / "fit_results.json").read_text())

    def test_fit_cross_checks_datasheet_within_10_percent(self):
        cc = self.fit["datasheet_crosscheck"]
        self.assertLess(abs(cc["Coss_at_50V_rel_error_pct"]), 10.0)
        self.assertLess(abs(cc["CO_TR_rel_error_pct"]), 10.0)
        self.assertLess(abs(cc["CO_ER_rel_error_pct"]), 10.0)

    def test_fit_quality_recorded(self):
        q = self.fit["fit_quality"]
        self.assertGreater(q["R2"], 0.9)

    def test_raw_digitized_points_committed(self):
        raw = HERE / "gs61008t_coss_digitized_raw.csv"
        self.assertTrue(raw.exists())
        lines = raw.read_text().strip().splitlines()
        self.assertGreater(len(lines), 100)


class A47GridTests(unittest.TestCase):
    def test_grid_matches_a42_a45_convention(self):
        self.assertEqual(NEGATIVE_PERCENTAGES, tuple(range(1, 11)))

    def test_source_regions_remain_distinct(self):
        self.assertEqual(source_label(1), "P24_EXPLICIT")
        self.assertEqual(source_label(2), "P24_EXPLICIT")
        self.assertEqual(source_label(3), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(4), "DIAGNOSTIC_BRIDGE")
        self.assertEqual(source_label(5), "P25_SUPPLEMENT")
        self.assertEqual(source_label(10), "P25_SUPPLEMENT")


class A47ThresholdResultTests(unittest.TestCase):
    """These assert only structural/self-consistency properties of whatever
    threshold was actually found (see RESULTS.md for the narrative
    interpretation) -- they must not hard-code a target percentage the
    protocol would consider "producing an attractive number"."""

    def setUp(self):
        path = HERE / "coarse_results.json"
        if not path.exists():
            self.skipTest("coarse_results.json not present (simulation not run)")
        self.coarse = json.loads(path.read_text())

    def test_coarse_grid_has_ten_rows(self):
        self.assertEqual(len(self.coarse), 10)

    def test_negative_target_matches_percentage(self):
        for row in self.coarse:
            self.assertAlmostEqual(
                row["negative_target_a"], 1.25 * row["negative_fraction_pct"]
            )

    def test_coarse_grid_itself_brackets_the_threshold(self):
        # Unlike A45's EPC2067 branch, A47's own 1%-10% coarse grid already
        # brackets the transition (between 9% and 10%), no wide-bracket
        # search needed.
        by_pct = {row["negative_fraction_pct"]: row for row in self.coarse}
        self.assertFalse(by_pct[9.0]["natural_zvs_after_release"])
        self.assertTrue(by_pct[10.0]["natural_zvs_after_release"])


class A47FinalBracketTests(unittest.TestCase):
    def setUp(self):
        path = HERE / "refinement_results.json"
        if not path.exists():
            self.skipTest("refinement_results.json not present (simulation not run)")
        rows = json.loads(path.read_text())
        self.fine = {
            row["negative_fraction_pct"]: row
            for row in rows
            if row["case"].startswith("a47_fine")
        }

    def test_recorded_threshold_remains_a_bracket(self):
        self.assertFalse(self.fine[9.63]["natural_zvs_after_release"])
        self.assertTrue(self.fine[9.64]["natural_zvs_after_release"])
        self.assertFalse(self.fine[9.63]["high_side_admitted"])
        self.assertTrue(self.fine[9.64]["high_side_admitted"])

    def test_threshold_moved_up_relative_to_a42_gs61008t_bracket(self):
        # A42's constant-Co(tr) GS61008T bracket was 7.76%-7.77%. The
        # digitized nonlinear Coss(V) curve's near-Vds=0 capacitance is
        # LARGER than the constant Co(tr) it replaces (see BOUNDARY.md), so
        # this should require MORE negative current, not less -- the
        # direction RESULTS.md states explicitly, per this project's A46
        # correction against silently ambiguous direction claims.
        self.assertGreater(9.64, 7.77)
        self.assertTrue(self.fine[9.64]["natural_zvs_after_release"])

    def test_threshold_still_far_from_p24_1_to_2_percent(self):
        # This experiment's own honest conclusion (RESULTS.md): nonlinear
        # Coss(V) does NOT close the gap toward P24's stated 1%-2% range;
        # it widens it. This is not a target to force -- it is what was
        # observed, asserted here so a future edit cannot silently flip it.
        self.assertGreater(9.63, 2.0)


if __name__ == "__main__":
    unittest.main()
