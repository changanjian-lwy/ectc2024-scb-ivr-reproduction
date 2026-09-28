"""D05 artificial fixtures only; no prototype parameters or new transient run."""
from dataclasses import replace
import unittest

import numpy as np

from scb_ivr.p25_native_events import MODES, NativeBoundary
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_nodal_contract import Components, instantaneous_rates
from scb_ivr.p25_reverse_contract import (
    ReverseModel, Tolerances, paper_mode_violations, resolve_local_reverse,
)


class ReverseContractTests(unittest.TestCase):
    def setUp(self):
        self.gates = {x.name: x.gates for x in MODES}
        self.state = Snapshot(NativeBoundary(3, 2, 1, "dynamic_Co_current_ports", .05),
                              "synthetic", "absolute", 0, 0., 12.,
                              (8.,4.,0.,0.,0.,1.), (2.,1.,1.), self.gates["M2"])
        self.parts = Components((2.,3.,5.,7.,11.,13.), (0.,)*6, (17.,19.), 23.,
                                (2.,3.,4.), (0.,)*3, "synthetic F/H fixtures")
        self.model = ReverseModel("ideal_zero_drop", (0.,)*6, "PROJECT_DECISION ideal test, not GaN")
        self.tol = Tolerances(1e-12, 1e-12, 1e-12)

    def solve(self, state=None, model=None, **kw):
        args = dict(dvin_v_s=0., load_current_a=2., other_modules_current_a=0., tolerances=self.tol)
        args.update(kw)
        return resolve_local_reverse(state or self.state, self.parts, model or self.model, **args)

    def candidate(self, result):
        self.assertEqual(result.status, "LOCAL_COMPLEMENTARITY_ONLY")
        self.assertTrue(result.candidates)
        return result.candidates[0]

    def test_sl1_reverse_conduction_holds_zero_without_gate_on(self):
        c = self.candidate(self.solve())
        self.assertEqual(c.reverse_active, ("SL1",))
        self.assertAlmostEqual(c.reverse_current_a[3], 2.)
        self.assertEqual(c.gate_current_a[3], 0.)
        self.assertAlmostEqual(c.gap_rate_v_s[3], 0.)

    def test_reverse_path_releases_when_forward_current_would_be_needed(self):
        result = self.solve(replace(self.state, current_a=(-2.,1.,1.)))
        c = self.candidate(result)
        self.assertEqual(c.reverse_active, ())
        self.assertGreater(c.gap_rate_v_s[3], 0.)
        self.assertIn(("SL1",), result.rejected_active_sets)

    def test_h2_reverse_conduction_in_mode5_prime(self):
        state = replace(self.state, voltage_v=(8.,8.,0.,1.,0.,1.),
                        current_a=(2.,-.5,1.), gates=self.gates["M5"])
        c = self.candidate(self.solve(state))
        self.assertIn("SH2", c.reverse_active)
        self.assertGreater(c.reverse_current_a[1], 0.)
        self.assertAlmostEqual(c.gap_rate_v_s[1], 0.)

    def test_kcl_and_power_identity_at_clamp(self):
        for dvin in (0., .1):
            for c in self.solve(dvin_v_s=dvin).candidates:
                np.testing.assert_allclose(c.kcl_residual_a, 0, atol=1e-12)
                self.assertAlmostEqual(c.energy_rate_w, c.net_power_w, places=10)

    def test_declared_constant_drop_has_positive_dissipation(self):
        state = replace(self.state, voltage_v=(8.,4.,-.25,0.,0.,1.))
        model = ReverseModel("constant_drop_surrogate", (0.,0.,0.,.25,0.,0.), "synthetic declared drop")
        c = self.candidate(self.solve(state, model))
        self.assertAlmostEqual(c.reverse_loss_w, .25*c.reverse_current_a[3])
        self.assertGreater(c.reverse_loss_w, 0.)
        self.assertAlmostEqual(c.energy_rate_w, c.net_power_w, places=10)

    def test_nonzero_drop_does_not_qualify_ideal_gate_closure(self):
        state = replace(self.state, voltage_v=(8.,4.,-.25,0.,0.,1.), gates=self.gates["M3"])
        with self.assertRaisesRegex(ValueError, "SL1 ON voltage inconsistent"):
            self.solve(state)

    def test_voltage_violation_is_not_projected_to_clamp(self):
        with self.assertRaisesRegex(ValueError, "SL1 OFF reverse gap"):
            self.solve(replace(self.state, voltage_v=(8.,4.,-.1,0.,0.,1.)))

    def test_gate_on_channel_is_bidirectional_not_reverse_diode(self):
        state = replace(self.state, gates=self.gates["M4"], current_a=(2.,-.5,1.))
        c = self.candidate(self.solve(state))
        self.assertGreater(c.gate_current_a[4], 0.)
        self.assertEqual(c.reverse_current_a[4], 0.)

    def test_ideal_zero_clamp_to_gate_on_preserves_rates(self):
        clamp = self.candidate(self.solve())
        gate = self.candidate(self.solve(replace(self.state, gates=self.gates["M3"])))
        np.testing.assert_allclose(clamp.dv_v_s, gate.dv_v_s, atol=1e-12)
        np.testing.assert_allclose(clamp.di_a_s, gate.di_a_s, atol=1e-12)
        self.assertAlmostEqual(gate.gate_current_a[3], -clamp.reverse_current_a[3])

    def test_unclamped_interior_matches_d03(self):
        state = replace(self.state, voltage_v=(8.,4.,2.,0.,0.,1.))
        c = self.candidate(self.solve(state))
        d03 = instantaneous_rates(state.boundary, self.parts, "M2", voltage_v=state.voltage_v,
                                  current_a=state.current_a, vin_v=state.vin_v, dvin_v_s=0.,
                                  load_current_a=2., other_modules_current_a=0., constraint_tolerance_v=1e-12,
                                  reverse_path_regime="off_reverse_channels_excluded_until_admission")
        np.testing.assert_allclose(c.dv_v_s, d03.voltage_rate_v_s, atol=1e-12)
        np.testing.assert_allclose(c.di_a_s, d03.current_rate_a_s, atol=1e-12)

    def test_degenerate_ideal_loops_are_not_claimed_unique(self):
        state = replace(self.state, vin_v=0., voltage_v=(0.,)*6, current_a=(0.,)*3)
        r = self.solve(state, load_current_a=0.)
        self.assertEqual(r.status, "DEGENERATE_ACTIVE_SETS_UNRESOLVED")
        self.assertTrue(r.singular_active_sets)

    def test_zero_current_active_label_ambiguity_not_forced_current(self):
        state = replace(self.state, current_a=(0.,1.,1.))
        result = self.solve(state)
        self.candidate(result)
        self.assertGreaterEqual(len(result.candidates), 2)
        for c in result.candidates:
            self.assertAlmostEqual(c.reverse_current_a[3], 0.)

    def test_other_phase_sign_violation_is_visible(self):
        state = replace(self.state, gates=self.gates["M4"], current_a=(2.,-.5,-1.))
        self.assertEqual(paper_mode_violations(state, "M4", tolerance_a=1e-12), ("iL3_SIGN",))

    def test_mode3_and_mode4_are_not_same_current_domain(self):
        state = replace(self.state, gates=self.gates["M4"], current_a=(2.,-.5,1.))
        self.assertEqual(paper_mode_violations(state, "M4", tolerance_a=1e-12), ())
        self.assertEqual(paper_mode_violations(state, "M3", tolerance_a=1e-12), ("iL2_SIGN",))

    def test_mode6_does_not_require_resetting_negative_entry_current(self):
        state = replace(self.state, gates=self.gates["M6"], current_a=(2.,-.5,1.))
        self.assertEqual(paper_mode_violations(state, "M6", tolerance_a=1e-12), ())

    def test_missing_model_and_invalid_numeric_boundary_rejected(self):
        with self.assertRaises(ValueError):
            ReverseModel("real_GaN", (0.,)*6, "not supported")
        with self.assertRaises(ValueError):
            ReverseModel("ideal_zero_drop", (.1,)*6, "wrong")
        with self.assertRaises(ValueError):
            Tolerances(1e-12, float("nan"), 1e-12)
        with self.assertRaises(ValueError):
            resolve_local_reverse(self.state, self.parts, None, dvin_v_s=0., load_current_a=0.,
                                  other_modules_current_a=0., tolerances=self.tol)
