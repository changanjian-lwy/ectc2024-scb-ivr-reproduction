import unittest

import numpy as np

from scb_ivr.evidence import Evidence
from scb_ivr.zero_start_descriptor import (
    Mode,
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
    input_voltage_v,
    ideal_divider_ramp_current_a,
    minimum_ramp_time_for_divider_current_s,
    stored_energy_j,
    startup_dimensionless_groups,
    true_zero_initial_vector,
)


class ZeroStartDescriptorTests(unittest.TestCase):
    def setUp(self):
        self.boundary = ZeroStartBoundary()

    def test_boundary_is_explicitly_cross_paper_not_p24_startup(self):
        self.assertIs(self.boundary.evidence, Evidence.CROSS_PAPER_EXTENSION)

    def test_true_zero_vector_has_zero_stored_energy(self):
        z0 = true_zero_initial_vector(self.boundary)
        self.assertEqual(stored_energy_j(z0, self.boundary), 0.0)

    def test_input_ramp_is_bounded(self):
        self.assertEqual(input_voltage_v(0, self.boundary), 0)
        self.assertAlmostEqual(
            input_voltage_v(self.boundary.input_ramp_s / 2, self.boundary), 24
        )
        self.assertEqual(input_voltage_v(2 * self.boundary.input_ramp_s, self.boundary), 48)

    def test_commanded_gate_state_is_complementary_by_construction(self):
        mode = commanded_pwm_mode(0.0, self.boundary)
        self.assertEqual(sum(mode.high_side_on), 1)
        quarter = commanded_pwm_mode(self.boundary.period_s / 4, self.boundary)
        self.assertEqual(sum(quarter.high_side_on), 1)
        self.assertNotEqual(mode.high_side_on, quarter.high_side_on)

    def test_descriptor_has_full_matrix_pencil_rank(self):
        mode = Mode((True, False, False, False), (True, True, True))
        system = assemble_descriptor(self.boundary, mode, 1e-6)
        self.assertEqual(system.e.shape, system.a.shape)
        self.assertEqual(system.pencil_rank_at_one, system.size)
        self.assertGreater(system.differential_rank, 0)
        self.assertLess(system.differential_rank, system.size)

    def test_divider_is_a_removable_module(self):
        no_divider = ZeroStartBoundary(divider_enabled=False)
        mode = commanded_pwm_mode(0, no_divider)
        system = assemble_descriptor(no_divider, mode, 0)
        self.assertNotIn("tap1", system.node_names)
        self.assertLess(system.size, assemble_descriptor(self.boundary, commanded_pwm_mode(0, self.boundary), 0).size)

    def test_diode_state_is_illegal_without_divider(self):
        no_divider = ZeroStartBoundary(divider_enabled=False)
        with self.assertRaises(ValueError):
            assemble_descriptor(
                no_divider,
                Mode((True, False, False, False), (True, False, False)),
                0,
            )

    def test_matrices_are_finite(self):
        system = assemble_descriptor(
            self.boundary,
            Mode((False, True, False, False), (False, True, False)),
            5e-6,
        )
        self.assertTrue(np.isfinite(system.e).all())
        self.assertTrue(np.isfinite(system.a).all())
        self.assertTrue(np.isfinite(system.rhs).all())

    def test_roberts_margin_keeps_ramp_resonance_cycles_near_constant(self):
        small = ZeroStartBoundary(
            input_ramp_s=30.68e-6,
            flying_capacitances_f=(0.6e-6,) * 3,
        )
        large = ZeroStartBoundary(
            input_ramp_s=116.84e-6,
            flying_capacitances_f=(8.7e-6,) * 3,
        )
        small_groups = startup_dimensionless_groups(small)
        large_groups = startup_dimensionless_groups(large)
        self.assertAlmostEqual(small_groups.ramp_resonance_cycles, 10.5, places=2)
        self.assertAlmostEqual(large_groups.ramp_resonance_cycles, 10.5, places=2)

    def test_fixed_divider_cfly_sweep_also_changes_charge_ratio(self):
        small = ZeroStartBoundary(flying_capacitances_f=(0.6e-6,) * 3)
        large = ZeroStartBoundary(flying_capacitances_f=(8.7e-6,) * 3)
        small_ratio = startup_dimensionless_groups(small).divider_to_flying_ratio
        large_ratio = startup_dimensionless_groups(large).divider_to_flying_ratio
        self.assertAlmostEqual(small_ratio, 500.0)
        self.assertAlmostEqual(large_ratio, 300 / 8.7, places=8)
        self.assertNotEqual(small_ratio, large_ratio)

    def test_divider_charge_predicts_r04e18_current_scale(self):
        self.assertAlmostEqual(ideal_divider_ramp_current_a(self.boundary), 157.4115, places=3)

    def test_250a_divider_screen_requires_at_least_14p4us(self):
        self.assertAlmostEqual(
            minimum_ramp_time_for_divider_current_s(self.boundary, 250) * 1e6,
            14.4,
        )


if __name__ == "__main__":
    unittest.main()
