"""D02 synthetic fixtures validate contracts, not paper operating points."""
import unittest
from dataclasses import replace

from scb_ivr.p25_native_events import (
    Event, FIRST_HANDOFF, MODES, GateState, NativeBoundary, Occurrence,
    PeakReference, negative_ramp_duration_s, negative_target_a, validate_order,
)


class P25NativeEventsTests(unittest.TestCase):
    def setUp(self):
        self.boundary = NativeBoundary(3, 2, 1, "shared output not solved by this contract", 0.05)
        self.peak = PeakReference(2, 10.0, "previous_measured_peak", "synthetic fixture")
        self.events = tuple(Occurrence(e, i * 1e-9) for i, e in enumerate(FIRST_HANDOFF))

    def test_native_branch_cannot_silently_become_four_phase(self):
        for change in ({"nP": 4}, {"branch": "P24_PLUS_P25"}, {"nP": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.boundary, **change)

    def test_total_modules_and_output_boundary_are_required(self):
        for change in ({"nM": 0}, {"module": 3}, {"output_boundary": ""}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.boundary, **change)

    def test_valid_full_and_prefix_order(self):
        validate_order(self.boundary, self.events)
        validate_order(self.boundary, self.events[:5])

    def test_missing_zero_event_detected(self):
        with self.assertRaisesRegex(ValueError, "order"):
            validate_order(self.boundary, self.events[:2] + self.events[3:])

    def test_swapped_target_and_actual_off_detected(self):
        rows = list(self.events)
        rows[5], rows[6] = rows[6], rows[5]
        with self.assertRaisesRegex(ValueError, "order"):
            validate_order(self.boundary, tuple(rows))

    def test_zero_delay_allowed_without_equating_event_identity(self):
        rows = tuple(Occurrence(e, 0.0) for e in FIRST_HANDOFF)
        # Order-only validation deliberately does NOT assert electrical feasibility.
        validate_order(self.boundary, rows)
        self.assertNotEqual(Event.H2_ZERO, Event.H2_ON)

    def test_nonfinite_time_and_backward_time_rejected(self):
        for time in (float("nan"), float("inf"), -1):
            with self.subTest(time=time), self.assertRaisesRegex(ValueError, "times"):
                validate_order(self.boundary, self.events[:1] + (Occurrence(Event.H1_OFF, time),))

    def test_gate_patterns_follow_three_phase_modes(self):
        expected = {
            "M1": ((1, 0, 0), (0, 1, 1)),
            "M2": ((0, 0, 0), (0, 1, 1)),
            "M3": ((0, 0, 0), (1, 1, 1)),
            "M4": ((0, 0, 0), (1, 1, 1)),
            "M5": ((0, 0, 0), (1, 0, 1)),
            "M6": ((0, 1, 0), (1, 0, 1)),
        }
        for spec in MODES:
            if spec.name in expected:
                self.assertEqual((spec.gates.high, spec.gates.low), expected[spec.name])
        self.assertEqual(next(m for m in MODES if m.name == "M3").exit, Event.I2_ZERO)

    def test_reverse_conduction_is_not_commanded_on(self):
        for spec in MODES:
            if spec.name == "M2_PRIME_OPTIONAL":
                self.assertFalse(spec.gates.low[0])
            if spec.name == "M5_PRIME_OPTIONAL":
                self.assertFalse(spec.gates.high[1])

    def test_overlap_gate_mine_detected(self):
        with self.assertRaises(ValueError):
            GateState((True, False, False), (True, True, True))
        with self.assertRaises(ValueError):
            GateState((True, True, False), (False, False, True))

    def test_p24_fraction_cannot_enter_native_mode4(self):
        for alpha in (0.02, 0.22, float("nan")):
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                replace(self.boundary, alpha=alpha)
        for alpha in (0.05, 0.08, 0.10):
            self.assertAlmostEqual(negative_target_a(replace(self.boundary, alpha=alpha), self.peak), -alpha*10)

    def test_wrong_phase_peak_and_future_peak_mines_detected(self):
        with self.assertRaisesRegex(ValueError, "phase-2"):
            negative_target_a(self.boundary, replace(self.peak, phase=1))
        with self.assertRaisesRegex(ValueError, "future"):
            replace(self.peak, basis="future_cycle_maximum")

    def test_eq11_ramp_closes_at_negative_target(self):
        target = negative_target_a(self.boundary, self.peak)
        L, vo, drop = 2e-6, 2.0, 0.5  # artificial, not prototype data
        dt = negative_ramp_duration_s(inductance_h=L, vout_v=vo,
                                      reverse_drop_magnitude_v=drop, target_a=target)
        self.assertGreater(dt, 0)
        self.assertAlmostEqual(-(vo+drop)/L*dt, target)

    def test_ramp_scaling_and_ideal_zero_drop(self):
        args = dict(inductance_h=2e-6, vout_v=2, reverse_drop_magnitude_v=0, target_a=-1)
        dt = negative_ramp_duration_s(**args)
        self.assertAlmostEqual(negative_ramp_duration_s(**{**args, "inductance_h": 4e-6}), 2*dt)
        self.assertAlmostEqual(negative_ramp_duration_s(**{**args, "target_a": -2}), 2*dt)
        self.assertAlmostEqual(negative_ramp_duration_s(**{**args, "vout_v": 4}), dt/2)

    def test_signed_voltage_cannot_replace_reverse_drop_magnitude(self):
        with self.assertRaises(ValueError):
            negative_ramp_duration_s(inductance_h=2e-6, vout_v=2,
                                     reverse_drop_magnitude_v=-0.5, target_a=-1)

    def test_empty_trace_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            validate_order(self.boundary, ())
