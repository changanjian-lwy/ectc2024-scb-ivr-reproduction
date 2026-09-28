import unittest
from dataclasses import replace

from scb_ivr.p25_native_events import Event, MODES, NativeBoundary, PeakReference
from scb_ivr.p25_event_guards import (
    Snapshot, ReverseBoundary, downward_bracket, gate_voltage_criterion,
    target_residual, reverse_boundary_status,
)


class P25GuardTests(unittest.TestCase):
    def setUp(self):
        self.gates = {m.name: m.gates for m in MODES}
        self.s = Snapshot(NativeBoundary(3, 2, 1, "dynamic_Co_current_ports", .05),
                          "synthetic", "absolute", 0, 0., 12., (8.,4.,0.,1.,0.,1.),
                          (2.,-.5,1.), self.gates["M5"])
        self.ref = PeakReference(2, 10., "declared_design_peak", "synthetic fixture, not paper data")

    def test_bracket_is_not_root_or_gate_admission(self):
        end = replace(self.s, time_s=1., voltage_v=(8.,9.,0.,1.,0.,1.))
        self.assertEqual(downward_bracket(self.s, end, Event.H2_ZERO).status, "BRACKET_ONLY")
        self.assertEqual(gate_voltage_criterion(end, "SH2", tolerance_v=.01).status, "VOLTAGE_REJECTED")

    def test_clock_advance_alone_is_not_an_event(self):
        end = replace(self.s, time_s=100.)
        self.assertEqual(downward_bracket(self.s, end, Event.H2_ZERO).status, "NOT_BRACKETED")

    def test_old_zero_does_not_qualify_later_gate_on(self):
        zero = replace(self.s, voltage_v=(8.,8.,0.,1.,0.,1.))
        rebound = replace(zero, time_s=1., voltage_v=(8.,7.,0.,1.,0.,1.))
        self.assertEqual(gate_voltage_criterion(zero, "SH2", tolerance_v=.01).status, "VOLTAGE_CRITERION_ONLY")
        self.assertEqual(gate_voltage_criterion(rebound, "SH2", tolerance_v=.01).status, "VOLTAGE_REJECTED")

    def test_wrong_mode_and_complementary_on_rejected(self):
        with self.assertRaises(ValueError):
            gate_voltage_criterion(replace(self.s, gates=self.gates["M4"]), "SH2", tolerance_v=.01)

    def test_second_phase_not_first_phase_zero(self):
        left = replace(self.s, gates=self.gates["M3"], current_a=(1.,1.,1.))
        right = replace(left, time_s=1., current_a=(-1.,.5,1.))
        self.assertEqual(downward_bracket(left, right, Event.I2_ZERO).status, "NOT_BRACKETED")
        right = replace(right, current_a=(1.,-.1,1.))
        self.assertEqual(downward_bracket(left, right, Event.I2_ZERO).status, "BRACKET_ONLY")

    def test_reverse_direction_is_not_downward_crossing(self):
        left = replace(self.s, gates=self.gates["M3"], current_a=(1.,-.1,1.))
        right = replace(left, time_s=1., current_a=(1.,.1,1.))
        self.assertEqual(downward_bracket(left, right, Event.I2_ZERO).status, "NOT_BRACKETED")

    def test_target_overshoot_not_silently_accepted(self):
        at = replace(self.s, gates=self.gates["M4"])
        self.assertEqual(target_residual(at, self.ref, tolerance_a=.001).status, "TARGET_CRITERION_ONLY")
        over = replace(at, current_a=(2.,-2.,1.))
        self.assertEqual(target_residual(over, self.ref, tolerance_a=.001).status, "TARGET_OVERSHOT")

    def test_target_crossing_requires_reference(self):
        left = replace(self.s, gates=self.gates["M4"], current_a=(2.,-.1,1.))
        right = replace(left, time_s=1., current_a=(2.,-.6,1.))
        with self.assertRaises(ValueError):
            downward_bracket(left, right, Event.I2_TARGET)
        self.assertEqual(downward_bracket(left, right, Event.I2_TARGET, reference=self.ref).status, "BRACKET_ONLY")

    def test_unknown_reverse_boundary_remains_unknown(self):
        self.assertEqual(reverse_boundary_status(self.s, "SH2", None).status, "UNRESOLVED")

    def test_declared_ideal_clamp_is_not_real_gan_model(self):
        rule = ReverseBoundary(0., "ideal_zero_voltage_clamp", "PROJECT_DECISION synthetic fixture")
        zero = replace(self.s, voltage_v=(8.,8.,0.,1.,0.,1.))
        self.assertEqual(reverse_boundary_status(zero, "SH2", rule).status, "REVERSE_MODEL_REQUIRED")
        self.assertEqual(reverse_boundary_status(self.s, "SH2", rule).status, "ABOVE_DECLARED_BOUNDARY")

    def test_gate_on_negative_voltage_not_an_off_reverse_event(self):
        self.assertEqual(reverse_boundary_status(self.s, "SL1", None).status, "NOT_APPLICABLE")

    def test_run_mixing_rejected(self):
        with self.assertRaises(ValueError):
            downward_bracket(self.s, replace(self.s, run_id="different", time_s=1.), Event.H2_ZERO)

    def test_invalid_tolerances_rejected(self):
        for tol in (-1., float("nan")):
            with self.assertRaises(ValueError):
                gate_voltage_criterion(self.s, "SH2", tolerance_v=tol)
