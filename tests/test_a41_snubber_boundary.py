import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a41_snubber_local_sensitivity import (
    BRANCHES,
    CAPS_PF,
    NEGATIVE_FRACTIONS,
)


class A41BoundaryTests(unittest.TestCase):
    def test_p24_thresholds_remain_separate(self):
        self.assertEqual(NEGATIVE_FRACTIONS, (0.01, 0.02))

    def test_declared_capacitance_grid(self):
        self.assertEqual(CAPS_PF, (0, 50, 100, 250, 500, 1000, 2000))

    def test_high_only_does_not_modify_low_side(self):
        self.assertEqual(BRANCHES["high_only"][1], "{CL_TOTAL}")

    def test_symmetric_changes_both_positions_equally(self):
        self.assertIn("CSNUB", BRANCHES["symmetric"][0])
        self.assertIn("CSNUB", BRANCHES["symmetric"][1])

    def test_recorded_sweep_does_not_silently_promote_a_zvs_case(self):
        result_path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A41_p24_snubber_local_sensitivity/results.json"
        )
        rows = json.loads(result_path.read_text())
        self.assertEqual(len(rows), 28)
        self.assertTrue(all(not row["natural_zvs_after_release"] for row in rows))
        self.assertTrue(all(row["controller_guard_pass"] for row in rows))

    def test_added_capacitance_monotonically_worsens_post_release_minimum(self):
        result_path = (
            Path(__file__).resolve().parents[1]
            / "experiments/track_A_periodic_steady_state/"
            "A41_p24_snubber_local_sensitivity/results.json"
        )
        rows = json.loads(result_path.read_text())
        for pct in (1, 2):
            for branch in ("high_only", "symmetric"):
                group = sorted(
                    (row for row in rows if row["negative_fraction_pct"] == pct
                     and row["branch"] == branch),
                    key=lambda row: row["added_snubber_pf"],
                )
                minima = [row["minimum_vds_high_after_release_v"] for row in group]
                self.assertTrue(all(b > a for a, b in zip(minima, minima[1:])))


if __name__ == "__main__":
    unittest.main()
