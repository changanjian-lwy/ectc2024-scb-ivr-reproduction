"""Synthetic topology/algebra tests. No values represent the paper prototype."""
import unittest
from dataclasses import replace

import numpy as np

from scb_ivr.p25_native_events import NativeBoundary
from scb_ivr.p25_nodal_contract import (
    CAPACITORS, ENDS, NODES, Components, incidence, instantaneous_rates,
    reduced_commutation_coefficients,
    assert_continuous_energy_state,
)


class P25NodalTests(unittest.TestCase):
    def setUp(self):
        self.boundary = NativeBoundary(3, 2, 1, "dynamic_Co_current_ports", 0.05)
        self.parts = Components((2., 3., 5., 7., 11., 13.), (0.,)*6,
                                (17., 19.), 23., (2., 3., 4.), (0.,)*3,
                                "synthetic F/H fixtures, not physical design data")
        self.states = {
            "M1": [12, 4, 4, 0, 0, 1],
            "M2": [8, 4, 2, 0, 0, 1],
            "M3": [8, 4, 0, 0, 0, 1],
            "M4": [8, 4, 0, 0, 0, 1],
            "M5": [8, 4, 0, 1, 0, 1],
            "M6": [8, 8, 0, 4, 0, 1],
        }

    def run_mode(self, mode, **changes):
        params = dict(voltage_v=self.states[mode], current_a=[2, -0.5, 1],
                      vin_v=12, dvin_v_s=0, load_current_a=2,
                      other_modules_current_a=0, constraint_tolerance_v=1e-12,
                      reverse_path_regime="off_reverse_channels_excluded_until_admission")
        params.update(changes)
        return instantaneous_rates(self.boundary, self.parts, mode, **params)

    def test_endpoint_map_against_fig1(self):
        expected = {"SH1": ("vin", "a1"), "SH2": ("a1", "a2"),
                    "SH3": ("a2", "x3"), "SL1": ("x1", None),
                    "SL2": ("x2", None), "SL3": ("x3", None),
                    "Cs1": ("a1", "x1"), "Cs2": ("a2", "x2"), "Co": ("out", None)}
        self.assertEqual(dict(zip(CAPACITORS, ENDS)), expected)

    def test_capacitance_matrix_keeps_nonworking_high_sides(self):
        af = incidence()
        c = (af*self.parts.capacitances())@af.T
        expected_internal = np.array([
            [22, -3, -17, 0, 0, 0],
            [-3, 27, 0, -19, -5, 0],
            [-17, 0, 24, 0, 0, 0],
            [0, -19, 0, 30, 0, 0],
            [0, -5, 0, 0, 18, 0],
            [0, 0, 0, 0, 0, 23]])
        np.testing.assert_array_equal(c[1:, 1:], expected_internal)
        self.assertGreater(np.linalg.eigvalsh(c[1:, 1:]).min(), 0)

    def test_all_modes_kcl_constraint_and_energy(self):
        for mode in self.states:
            with self.subTest(mode=mode):
                r = self.run_mode(mode)
                np.testing.assert_allclose(r.kcl_residual_a, 0, atol=1e-12)
                np.testing.assert_allclose(r.constraint_rate_error_v_s, 0, atol=1e-12)
                self.assertAlmostEqual(r.energy_rate_w, r.supplied_minus_dissipated_w, places=11)

    def test_changing_input_voltage_is_not_silently_ac_grounded(self):
        for mode in self.states:
            with self.subTest(mode=mode):
                r = self.run_mode(mode, dvin_v_s=0.7)
                np.testing.assert_allclose(r.kcl_residual_a, 0, atol=1e-12)
                self.assertAlmostEqual(r.energy_rate_w, r.supplied_minus_dissipated_w, places=10)

    def test_output_is_dynamic_and_other_module_port_is_explicit(self):
        r = self.run_mode("M5", load_current_a=7, other_modules_current_a=3)
        self.assertAlmostEqual(r.voltage_rate_v_s[-1], (2-0.5+1+3-7)/23)
        self.assertAlmostEqual(r.energy_rate_w, r.supplied_minus_dissipated_w, places=11)

    def test_m6_kvl_subtracts_output_voltage(self):
        r = self.run_mode("M6")
        self.assertAlmostEqual(r.current_rate_a_s[1], (8-4-1)/3)
        self.assertNotEqual(r.current_rate_a_s[1], (8-4)/3)

    def test_negative_entry_current_is_not_reset(self):
        current = np.array([2., -0.5, 1.])
        before = current.copy()
        self.run_mode("M6", current_a=current)
        np.testing.assert_array_equal(current, before)

    def test_winding_loss_and_signed_current(self):
        self.parts = replace(self.parts, winding_ohm=(0.2, 0.3, 0.4))
        r = self.run_mode("M4")
        self.assertAlmostEqual(r.current_rate_a_s[1], (-1+0.3*0.5)/3)
        self.assertAlmostEqual(r.energy_rate_w, r.supplied_minus_dissipated_w, places=11)

    def test_schur_reductions_match_full_network(self):
        for mode, xindex, active_current in (("M2", 2, 2), ("M5", 3, -0.5)):
            with self.subTest(mode=mode):
                r = self.run_mode(mode)
                reduction = reduced_commutation_coefficients(self.parts, mode)
                dx = -active_current/reduction["ceff_f"]
                self.assertAlmostEqual(r.voltage_rate_v_s[xindex], dx)
                self.assertAlmostEqual(r.voltage_rate_v_s[0], reduction["a1_over_x"]*dx)
                self.assertAlmostEqual(r.voltage_rate_v_s[1], reduction["a2_over_x"]*dx)
                actual = r.voltage_rate_v_s[2] if mode == "M2" else r.voltage_rate_v_s[0]-r.voltage_rate_v_s[1]
                self.assertAlmostEqual(actual, reduction["target_gain"]*dx)
                self.assertLess(actual, 0)

    def test_nonworking_capacitance_changes_commutation(self):
        before = reduced_commutation_coefficients(self.parts, "M5")["ceff_f"]
        changed = replace(self.parts, coss_f=(2., 3., 10., 7., 11., 13.))
        after = reduced_commutation_coefficients(changed, "M5")["ceff_f"]
        self.assertGreater(after, before)  # CH3 affects phase-2 commutation

    def test_snubber_and_coss_kept_separate_but_electrically_add(self):
        self.parts = replace(self.parts, snubber_f=(1.,)*6)
        r = self.run_mode("M5")
        self.parts = replace(self.parts, coss_f=(3., 4., 6., 8., 12., 14.), snubber_f=(0.,)*6)
        s = self.run_mode("M5")
        np.testing.assert_allclose(r.voltage_rate_v_s, s.voltage_rate_v_s)

    def test_illegal_ideal_gate_closure_rejected_not_projected(self):
        # Mine: nonzero capacitor voltage across SH2 before ideal SH2 closure.
        with self.assertRaisesRegex(ValueError, "no projection"):
            self.run_mode("M6", voltage_v=[8, 4, 0, 4, 0, 1])

    def test_prime_modes_not_silently_run_without_clamp(self):
        with self.assertRaises(ValueError):
            self.run_mode("M5", reverse_path_regime="GaN_clamp_already_on")
        with self.assertRaises(ValueError):
            instantaneous_rates(self.boundary, self.parts, "M5_PRIME_OPTIONAL",
                                voltage_v=self.states["M5"], current_a=[2,-0.5,1], vin_v=12,
                                dvin_v_s=0, load_current_a=2, other_modules_current_a=0,
                                constraint_tolerance_v=1e-12,
                                reverse_path_regime="off_reverse_channels_excluded_until_admission")

    def test_single_module_cannot_hide_other_module_injection(self):
        self.boundary = replace(self.boundary, nM=1)
        with self.assertRaisesRegex(ValueError, "single-module"):
            self.run_mode("M5", other_modules_current_a=1)

    def test_output_boundary_cannot_silently_switch_to_clamp(self):
        self.boundary = replace(self.boundary, output_boundary="ideal_1V_clamp")
        with self.assertRaisesRegex(ValueError, "output boundary"):
            self.run_mode("M5")

    def test_invalid_values_do_not_enter_matrix(self):
        with self.assertRaises(ValueError):
            replace(self.parts, inductance_h=(0., 1., 1.))
        with self.assertRaises(ValueError):
            replace(self.parts, snubber_f=(-1.,)*6)
        with self.assertRaises(ValueError):
            self.run_mode("M5", current_a=[1, float("nan"), 2])

    def test_independent_branch_power_detects_wrong_incidence_sign(self):
        # A deliberately wrong SH2 terminal sign breaks node/branch power identity.
        v = np.arange(1., 8.)
        currents = np.arange(1., 10.)
        correct = incidence()
        wrong = correct.copy()
        wrong[NODES.index("a2"), CAPACITORS.index("SH2")] *= -1
        self.assertAlmostEqual(v@(correct@currents), (correct.T@v)@currents)
        self.assertNotEqual(v@(wrong@currents), (correct.T@v)@currents)

    def test_unchanged_energy_state_passes_event_boundary(self):
        assert_continuous_energy_state(
            voltage_before_v=self.states["M6"], voltage_after_v=self.states["M6"],
            vin_before_v=12, vin_after_v=12, current_before_a=[2,-0.5,1], current_after_a=[2,-0.5,1],
            capacitor_tolerance_v=1e-12, current_tolerance_a=1e-12)

    def test_resetting_negative_current_at_h2_on_is_detected(self):
        with self.assertRaisesRegex(ValueError, "L2"):
            assert_continuous_energy_state(
                voltage_before_v=self.states["M6"], voltage_after_v=self.states["M6"],
                vin_before_v=12, vin_after_v=12, current_before_a=[2,-0.5,1], current_after_a=[2,0,1],
                capacitor_tolerance_v=1e-12, current_tolerance_a=1e-12)

    def test_forcing_capacitor_to_zvs_value_is_detected(self):
        with self.assertRaisesRegex(ValueError, "capacitor voltage discontinuity"):
            assert_continuous_energy_state(
                voltage_before_v=self.states["M5"], voltage_after_v=self.states["M6"],
                vin_before_v=12, vin_after_v=12, current_before_a=[2,-0.5,1], current_after_a=[2,-0.5,1],
                capacitor_tolerance_v=1e-12, current_tolerance_a=1e-12)
