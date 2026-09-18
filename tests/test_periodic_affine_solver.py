import unittest

import numpy as np

from scb_ivr.periodic_affine_solver import (
    build_affine_period_map,
    periodic_orbit_metrics,
    propagate_fixed_diode_period,
    solve_periodic_fixed_point,
)
from scb_ivr.zero_start_descriptor import ZeroStartBoundary


class PeriodicAffineSolverTests(unittest.TestCase):
    def setUp(self):
        self.boundary = ZeroStartBoundary(input_ramp_s=1e-6)
        self.start_time = 5 * self.boundary.period_s

    def test_identified_map_reproduces_a_direct_period(self):
        period_map = build_affine_period_map(
            self.boundary,
            start_time_s=self.start_time,
            maximum_step_s=2e-9,
        )
        state = np.linspace(-0.25, 0.5, period_map.offset.size)
        direct = propagate_fixed_diode_period(
            self.boundary,
            state,
            start_time_s=self.start_time,
            maximum_step_s=2e-9,
        ).final.state
        predicted = period_map.matrix @ state + period_map.offset
        np.testing.assert_allclose(predicted, direct, rtol=2e-10, atol=2e-8)

    def test_fixed_point_closes_the_discretized_period_map(self):
        period_map = build_affine_period_map(
            self.boundary,
            start_time_s=self.start_time,
            maximum_step_s=2e-9,
        )
        fixed = solve_periodic_fixed_point(self.boundary, period_map)
        # Three post-precharge divider-charge coordinates evolve on the
        # artificial 1-Gohm leakage timescale and are numerically neutral over
        # one 200-ns period.  The fast converter subspace has rank 17.
        self.assertEqual(
            period_map.matrix.shape[0] - fixed.least_squares_rank,
            3,
        )
        self.assertLess(fixed.fixed_point_residual_inf, 1e-5)
        self.assertLess(fixed.orbit_closure_inf, 1e-5)
        self.assertTrue(fixed.diode_complementarity_valid)
        metrics = periodic_orbit_metrics(self.boundary, fixed)
        self.assertGreater(metrics.average_output_v, 0.0)
        self.assertGreater(metrics.average_load_power_w, 0.0)
        self.assertAlmostEqual(
            sum(metrics.average_phase_currents_a),
            metrics.average_output_v / self.boundary.load_resistance_ohm,
            delta=0.1,
        )


if __name__ == "__main__":
    unittest.main()
