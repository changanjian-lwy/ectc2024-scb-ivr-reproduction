"""Synthetic unit fixtures, never paper-derived operating points."""
import unittest
from dataclasses import replace

from scb_ivr.evidence import Evidence
from scb_ivr.timing_contract import (
    DurationKind as D, TimingKind as K, TimingContext, TimingEvent, duration_s,
)


class TimingContractTests(unittest.TestCase):
    def setUp(self):
        self.context = TimingContext("P24", "synthetic-test", "absolute", 4, 1, 1, 1, 0)

    def event(self, kind, t, switch="H", **kwargs):
        return TimingEvent(kwargs.get("context", self.context), switch, kind, t,
                           Evidence.PROJECT_DECISION, "synthetic unit fixture")

    def test_duration_definitions(self):
        pairs = [(D.NOMINAL_ON, K.NOMINAL_ON, K.NOMINAL_OFF, "H"),
                 (D.COMMAND_ON, K.COMMAND_ON, K.COMMAND_OFF, "H"),
                 (D.GATE_ON, K.GATE_ON, K.GATE_OFF, "H"),
                 (D.COMMAND_DEADTIME, K.COMMAND_OFF, K.COMMAND_ON, "L"),
                 (D.GATE_DEADTIME, K.GATE_OFF, K.GATE_ON, "L"),
                 (D.COMMUTATION, K.GATE_OFF, K.VDS_ZERO, "L")]
        for definition, a, b, switch in pairs:
            with self.subTest(definition=definition):
                self.assertAlmostEqual(duration_s(definition, self.event(a, 1e-9),
                                                   self.event(b, 3e-9, switch)), 2e-9)

    def test_planted_nominal_off_cannot_replace_gate_off(self):
        with self.assertRaisesRegex(ValueError, "semantics"):
            duration_s(D.GATE_ON, self.event(K.GATE_ON, 0), self.event(K.NOMINAL_OFF, 1))

    def test_cross_context_mixing_is_rejected(self):
        for field, value in [("branch", "P25"), ("run_id", "other"),
                             ("clock_id", "local"), ("phase", 2), ("cycle", 1)]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "cannot mix"):
                duration_s(D.GATE_ON, self.event(K.GATE_ON, 0),
                           self.event(K.GATE_OFF, 1, context=replace(self.context, **{field: value})))

    def test_unknown_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            duration_s(D.GATE_ON, self.event(K.GATE_ON, None), self.event(K.GATE_OFF, 1))

    def test_unresolved_evidence_blocks_number(self):
        with self.assertRaisesRegex(ValueError, "unresolved"):
            duration_s(D.GATE_ON, replace(self.event(K.GATE_ON, 0), evidence=Evidence.UNKNOWN_BLOCKING),
                       self.event(K.GATE_OFF, 1))

    def test_reverse_conduction_is_not_gate_on(self):
        with self.assertRaisesRegex(ValueError, "semantics"):
            duration_s(D.GATE_ON, self.event(K.REVERSE_CONDUCTION, 0), self.event(K.GATE_OFF, 1))

    def test_negative_deadtime_rejected(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            duration_s(D.GATE_DEADTIME, self.event(K.GATE_OFF, 2), self.event(K.GATE_ON, 1, "L"))

    def test_wrong_switch_rejected(self):
        with self.assertRaisesRegex(ValueError, "switch pair"):
            duration_s(D.COMMUTATION, self.event(K.GATE_OFF, 0), self.event(K.VDS_ZERO, 1))

    def test_architecture_and_finite_times(self):
        self.assertEqual(replace(self.context, nP=1).nP, 1)
        for kwargs in ({"nP": 0}, {"nM": True}, {"phase": 5}):
            with self.assertRaises(ValueError):
                replace(self.context, **kwargs)
        for t in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.event(K.GATE_ON, t)
