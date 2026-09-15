import json
from pathlib import Path
import unittest

from experiments.track_A_periodic_steady_state.build_a48_dead_time_feasibility_sweep import (
    COARSE_T_DEAD_NS,
    FINE_T_DEAD_NS,
    NEG_FRAC_ROWS,
    REFINEMENT_T_DEAD_NS,
)

RESULTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "experiments/track_A_periodic_steady_state/A48_dead_time_feasibility_sweep"
)


class A48BoundaryTests(unittest.TestCase):
    def test_grids_are_fixed_before_results(self):
        self.assertEqual(COARSE_T_DEAD_NS, (0.5, 1, 2, 3, 5, 7, 10, 15, 20))
        self.assertEqual(
            REFINEMENT_T_DEAD_NS,
            (2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0),
        )
        self.assertEqual(
            FINE_T_DEAD_NS,
            (2.10, 2.12, 2.14, 2.15, 2.16, 2.17, 2.18, 2.20, 2.22, 2.24),
        )

    def test_release_rows_reused_unchanged_from_a42(self):
        self.assertEqual(
            NEG_FRAC_ROWS,
            {
                "01pct": (0.01, "P24_EXPLICIT"),
                "02pct": (0.02, "P24_EXPLICIT"),
                "777bp": (0.0777, "A42_NATURAL_ZVS_REFERENCE"),
            },
        )

    def test_01_02_pct_never_reach_near_zero_residual_voltage(self):
        rows = json.loads((RESULTS_DIR / "coarse_results.json").read_text())
        for row in rows:
            if row["row"] in ("01pct", "02pct"):
                self.assertGreater(
                    abs(row["vds_at_forced_on_v"]),
                    1.0,
                    f"{row['case']} unexpectedly reached near-zero residual "
                    "voltage -- dead time cannot manufacture missing "
                    "negative-current margin",
                )

    def test_777pct_narrow_window_matches_a42_commutation_duration(self):
        fine_rows = {
            row["t_dead_ns_requested"]: row
            for row in json.loads((RESULTS_DIR / "fine_results.json").read_text())
        }
        # Exact zero at 2.15 ns, matching A42's own independently-measured
        # commutation duration (2.1516 ns) to within simulation resolution.
        self.assertLess(abs(fine_rows[2.15]["vds_at_forced_on_v"]), 1e-4)
        self.assertTrue(fine_rows[2.15]["forced_on_before_natural_zvs"])
        self.assertFalse(fine_rows[2.16]["forced_on_before_natural_zvs"])

    def test_hypothesis_any_dead_time_above_natural_duration_is_safe_is_rejected(self):
        # The coarse grid must directly falsify the naive hypothesis that any
        # T_DEAD above the natural commutation duration reproduces A42's
        # near-zero natural-ZVS result. This is asserted, not just narrated
        # in RESULTS.md, so a future data refresh cannot silently drop it.
        rows = {
            row["t_dead_ns_requested"]: row
            for row in json.loads((RESULTS_DIR / "coarse_results.json").read_text())
            if row["row"] == "777bp"
        }
        for t_dead in (5, 7, 15):
            self.assertGreater(abs(rows[t_dead]["vds_at_forced_on_v"]), 5.0)


if __name__ == "__main__":
    unittest.main()
