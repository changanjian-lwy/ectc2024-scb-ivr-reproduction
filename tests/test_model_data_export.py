import unittest

from scb_ivr.model_data_export import export_model_dataset
from scb_ivr.periodic_affine_solver import (
    build_affine_period_map,
    solve_periodic_fixed_point,
)
from scb_ivr.zero_start_descriptor import ZeroStartBoundary


class ModelDataExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = ZeroStartBoundary(input_ramp_s=1e-6)
        start = 5 * cls.boundary.period_s
        period_map = build_affine_period_map(
            cls.boundary,
            start_time_s=start,
            maximum_step_s=2e-9,
        )
        cls.dataset = export_model_dataset(
            cls.boundary,
            solve_periodic_fixed_point(cls.boundary, period_map),
        )

    def test_exports_all_twenty_named_variables(self):
        schema = self.dataset["state_schema"]
        self.assertEqual(len(schema["variable_order"]), 20)
        for snapshot in self.dataset["event_snapshots"]:
            self.assertEqual(len(snapshot["raw_state_by_variable"]), 20)
            self.assertEqual(len(snapshot["phases"]), 4)

    def test_exports_nine_synchronized_left_limit_events(self):
        snapshots = self.dataset["event_snapshots"]
        self.assertEqual(len(snapshots), 9)
        self.assertTrue(all(item["sampling_side"] == "left_limit" for item in snapshots))
        self.assertEqual(snapshots[0]["transition"], "high_side_turn_on")
        self.assertEqual(
            snapshots[-1]["transition"], "next_period_high_side_turn_on"
        )

    def test_marks_all_three_slow_coordinates_as_nonunique(self):
        reliability = self.dataset["state_schema"]["reliability"]
        for name in ("tap3", "tap2", "tap1"):
            self.assertIn("NONUNIQUE_SLOW_COORDINATE", reliability[name])
        self.assertEqual(reliability["L1"], "FAST_PERIODIC_MANIFOLD_STATE")

    def test_first_event_contains_same_time_four_phase_currents(self):
        first = self.dataset["event_snapshots"][0]
        currents = [
            phase["inductor_current_first_to_second_a"]
            for phase in first["phases"]
        ]
        self.assertEqual(len(currents), 4)
        self.assertTrue(all(isinstance(value, float) for value in currents))

    def test_exports_complete_affine_period_map_in_same_variable_order(self):
        period_map = self.dataset["affine_period_map"]
        self.assertEqual(
            period_map["variable_order"],
            self.dataset["state_schema"]["variable_order"],
        )
        self.assertEqual(len(period_map["matrix_M"]), 20)
        self.assertTrue(all(len(row) == 20 for row in period_map["matrix_M"]))
        self.assertEqual(len(period_map["offset_c"]), 20)


if __name__ == "__main__":
    unittest.main()
