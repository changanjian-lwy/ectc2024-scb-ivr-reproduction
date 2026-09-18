import unittest

import numpy as np

from scb_ivr.zero_start_descriptor import ZeroStartBoundary
from scb_ivr.zero_start_hybrid_solver import (
    complementarity_admissible,
    continue_zero_start_poincare,
    hybrid_step_from_named_state,
    named_hybrid_state,
    next_pwm_edge_s,
    next_periodic_sample_s,
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
        self.assertLess(
            max(
                step.descriptor_relative_backward_error
                for step in trajectory.steps
            ),
            1e-12,
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
        self.assertLess(
            summary.maximum_descriptor_relative_backward_error,
            1e-12,
        )

    def test_next_periodic_sample_is_strictly_after_initial_time(self):
        period = self.boundary.period_s
        self.assertAlmostEqual(next_periodic_sample_s(0.35 * period, period), period)
        self.assertAlmostEqual(next_periodic_sample_s(period, period), 2 * period)

    def test_continuation_samples_one_fixed_pwm_section(self):
        ramp = simulate_zero_start(
            self.boundary,
            stop_time_s=0.35 * self.boundary.period_s,
            maximum_step_s=2e-9,
        )
        continuation = continue_zero_start_poincare(
            self.boundary,
            ramp.final,
            periods=3,
            maximum_step_s=2e-9,
        )
        expected = np.array([1.0, 2.0, 3.0]) * self.boundary.period_s
        actual = np.array(
            [sample.checkpoint.time_s for sample in continuation.samples]
        )
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-18)
        self.assertTrue(
            all(
                sample.checkpoint.time_s > ramp.final.time_s
                for sample in continuation.samples
            )
        )

    def test_named_checkpoint_round_trip_preserves_full_state(self):
        trajectory = simulate_zero_start(
            self.boundary,
            stop_time_s=50e-9,
            maximum_step_s=2e-9,
        )
        original = trajectory.final
        restored = hybrid_step_from_named_state(
            self.boundary,
            time_s=original.time_s,
            state_by_variable=named_hybrid_state(original, self.boundary),
            high_side_on=original.mode.high_side_on,
            precharge_diode_on=original.mode.precharge_diode_on,
        )
        np.testing.assert_array_equal(restored.state, original.state)
        self.assertEqual(restored.mode, original.mode)

    def test_incomplete_named_checkpoint_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "checkpoint variables differ"):
            hybrid_step_from_named_state(
                self.boundary,
                time_s=0.0,
                state_by_variable={"out": 0.0},
                high_side_on=(True, False, False, False),
                precharge_diode_on=(False, False, False),
            )


if __name__ == "__main__":
    unittest.main()
