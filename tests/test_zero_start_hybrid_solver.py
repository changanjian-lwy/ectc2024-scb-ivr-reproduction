import unittest

import numpy as np

from scb_ivr.zero_start_descriptor import ZeroStartBoundary
from scb_ivr.zero_start_hybrid_solver import (
    complementarity_admissible,
    next_pwm_edge_s,
    simulate_zero_start,
    simulate_zero_start_checkpoints,
)


class ZeroStartHybridSolverTests(unittest.TestCase):
    def setUp(self):
        self.boundary = ZeroStartBoundary(input_ramp_s=1e-6)

    def test_first_pwm_edge_is_on_time(self):
        self.assertAlmostEqual(
            next_pwm_edge_s(0.0, self.boundary), self.boundary.on_time_s
        )

    def test_solver_hits_pwm_edge_exactly(self):
        trajectory = simulate_zero_start(
            self.boundary,
            stop_time_s=25e-9,
            maximum_step_s=10e-9,
        )
        times = [step.time_s for step in trajectory.steps]
        self.assertTrue(
            any(abs(time - self.boundary.on_time_s) < 1e-18 for time in times)
        )

    def test_every_accepted_step_satisfies_diode_complementarity(self):
        trajectory = simulate_zero_start(
            self.boundary,
            stop_time_s=50e-9,
            maximum_step_s=2e-9,
        )
        for step in trajectory.steps[1:]:
            self.assertTrue(
                complementarity_admissible(
                    step.diode_observation,
                    step.mode.precharge_diode_on,
                    voltage_tolerance_v=1e-9,
                    current_tolerance_a=1e-9,
                )
            )

    def test_short_trajectory_is_finite_and_residual_is_small(self):
        trajectory = simulate_zero_start(
            self.boundary,
            stop_time_s=50e-9,
            maximum_step_s=2e-9,
        )
        self.assertTrue(np.isfinite(trajectory.final.state).all())
        self.assertLess(
            max(step.descriptor_residual_inf for step in trajectory.steps),
            1e-4,
        )

    def test_timestep_larger_than_on_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            simulate_zero_start(
                self.boundary,
                stop_time_s=50e-9,
                maximum_step_s=20e-9,
            )

    def test_period_map_records_exact_period_boundaries(self):
        summary = simulate_zero_start_checkpoints(
            self.boundary,
            stop_time_s=2 * self.boundary.period_s,
            maximum_step_s=2e-9,
        )
        self.assertEqual(
            [point.completed_periods for point in summary.checkpoints],
            [0, 1, 2],
        )
        self.assertAlmostEqual(
            summary.checkpoints[-1].time_s, 2 * self.boundary.period_s
        )

    def test_period_map_summary_is_finite(self):
        summary = simulate_zero_start_checkpoints(
            self.boundary,
            stop_time_s=2 * self.boundary.period_s,
            maximum_step_s=2e-9,
        )
        self.assertTrue(np.isfinite(summary.maximum_abs_phase_current_a))
        self.assertTrue(np.isfinite(summary.maximum_abs_input_inductor_current_a))
        self.assertGreaterEqual(summary.diode_transition_count, 0)
        self.assertEqual(summary.diode_transition_count, len(summary.diode_transitions))
        self.assertTrue(np.isfinite(summary.maximum_descriptor_residual_inf))


if __name__ == "__main__":
    unittest.main()
