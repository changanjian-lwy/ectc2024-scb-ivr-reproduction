"""D41 single-sensor (phase-shift) control: contract tests and one P25-scale cycle.

The unit tests use the synthetic F/H fixture. The integration test uses the
P25 orders of magnitude from scripts/audit_p25_single_sensor_closure.py
(P25_SUPPLEMENT; not fitted). No paper operating point is claimed.
"""
from dataclasses import replace
import unittest

import numpy as np

from scb_ivr.p25_control_memory import (KnownPeak, Memory, Policy, Stage, Trigger, phase_shift_due,
                                        start_at_high_on, transition)
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import ConstantPorts, LocalFlow
from scb_ivr.p25_native_events import MODES, NativeBoundary, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_negative_handoff import reach_phase_shift_due
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings
from scripts import audit_p25_single_sensor_closure as A


class PolicyAndMemoryTests(unittest.TestCase):
    def test_phase_shift_validation(self):
        for bad in ((1.,), (2., 1.), (0., 1.), (1., float("nan")), [1., 2.]):
            with self.assertRaises(ValueError):
                Policy((.02,)*3, 1e-8, 1e-8, 1e-9, True, "synthetic", bad)
        p = Policy((.02,)*3, 1e-8, 1e-8, 1e-9, True, "synthetic", (1., 2.))
        self.assertEqual((p.timed(1), p.timed(2), p.timed(3)), (False, True, True))
        self.assertFalse(Policy((.02,)*3, 1e-8, 1e-8, 1e-9, True, "synthetic").timed(2))

    def test_section_sets_timer_origin(self):
        s = Snapshot(NativeBoundary(3, 1, 1, "dynamic_Co_current_ports", .05), "synthetic", "clock", 0, 3., 12.,
                     (12., 4., 2., 0., 0., 1.), (20., 2., 3.), cycle_mode("M1").gates)
        m = start_at_high_on(s, phase=1, peaks=(None,)*3,
                             policy=Policy((.02,)*3, 1e-8, 1e-8, 1e-9, True, "synthetic", (1., 2.)))
        self.assertEqual(m.reference_s, 3.)


class TimedTransitionTests(unittest.TestCase):
    def setUp(self):
        self.parts = Components((1.,)*6, (0.,)*6, (17., 19.), 23., (2., 3., 4.), (0.,)*3, "synthetic F/H fixture")
        self.ports = ConstantPorts(1., 0., "constant synthetic")
        self.policy = Policy((.02,)*3, 1e-8, 1e-8, 1e-9, True, "synthetic", (.5, 1.))
        self.reverse = ReverseModel("ideal_zero_drop", (0.,)*6, "ideal")
        self.root = RootSettings(1e-9, 1e-8, 100, "affine continuation")
        s = Snapshot(NativeBoundary(3, 1, 1, "dynamic_Co_current_ports", .05), "synthetic", "clock", 0, 0., 12.,
                     (8., 4., 0., 0., 0., 1.), (20., 0., 20.), {m.name: m.gates for m in MODES}["M4"])
        peak = KnownPeak(PeakReference(2, 20., "declared_design_peak", "synthetic not measured"), 0.)
        self.m = Memory(1, Stage.NEGATIVE, 0., s, (None, peak, None), -1., -0.1)   # timer origin 0.1 s earlier

    def at(self, t):
        return LocalFlow(self.m.last_event, self.parts, "M4", self.ports, voltage_tolerance_v=1e-8).at(t)

    def test_current_target_trigger_rejected_for_timed_phase(self):
        with self.assertRaises(ValueError):
            transition(self.m, Trigger.NEGATIVE_TARGET, self.at(.2), left=self.at(.1), policy=self.policy)

    def test_timer_must_be_located_exactly(self):
        due = phase_shift_due(self.m, self.policy, 2)
        self.assertAlmostEqual(due, .4)
        with self.assertRaises(ValueError):
            transition(self.m, Trigger.PHASE_SHIFT_DUE, self.at(due + 1e-3), policy=self.policy)
        after = transition(self.m, Trigger.PHASE_SHIFT_DUE, self.at(due), policy=self.policy)
        self.assertEqual(after.stage, Stage.UP_COMM)
        self.assertEqual(after.reference_s, -0.1)

    def test_timed_stage_reaches_due_and_keeps_state(self):
        r = reach_phase_shift_due(self.m, self.parts, self.ports, self.policy, self.reverse, end_s=10., intervals=200,
                                  voltage_root=self.root, current_root=self.root,
                                  electrical=Tolerances(1e-8, 1e-8, 1e-8), current_rate_tolerance_a_s=1e-10)
        self.assertEqual(r.status, "CONDITIONAL_M5_ENTRY", r.reason)
        self.assertAlmostEqual(r.memory.last_event.time_s, .4)
        self.assertEqual(r.memory.last_event.current_a, self.at(.4).current_a)


class P25ScaleCycleTests(unittest.TestCase):
    def test_single_sensor_cycle_completes_with_timed_low_offs(self):
        contract, options = A.context(A.P25_SCALE["phase_shift_s"])
        f, r = A.section_map(contract, options, np.array(A.SEED0, float))
        self.assertIsNotNone(f, r.attempt.failed_mode)
        steps = {s.mode: s.outcome.memory for s in r.attempt.steps}
        shifts = A.P25_SCALE["phase_shift_s"]
        self.assertAlmostEqual(steps["M4"].last_event.time_s, shifts[0], delta=1e-14)   # SL2 off (timed)
        self.assertAlmostEqual(steps["M9"].last_event.time_s, shifts[1], delta=1e-14)   # SL3 off (timed)
        self.assertLess(steps["M4"].last_event.current_a[1], 0.)                        # negative at SL2 off
        self.assertLess(steps["M9"].last_event.current_a[2], 0.)
        self.assertEqual(r.attempt.end.reference_s, r.attempt.end.last_event.time_s)    # new timer origin

    def test_timer_before_own_current_zero_is_reported_not_forced(self):
        contract, options = A.context((50e-9, 1.3333e-6))
        f, r = A.section_map(contract, options, np.array(A.SEED0, float))
        self.assertIsNone(f)
        self.assertEqual(r.attempt.failed_mode, "M3")
        self.assertEqual(r.attempt.steps[-1].outcome.status, "PHASE_SHIFT_DUE_BEFORE_NEXT_CURRENT_ZERO")


if __name__ == "__main__":
    unittest.main()
