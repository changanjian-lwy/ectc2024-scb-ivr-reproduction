"""D28 same-trace integral accounting, excluding unresolved trial segments."""
from dataclasses import replace
import unittest
import numpy as np
import test_p25_seed_evaluation as fixtures
from scb_ivr.p25_trace_balance import trace_balance


class TraceBalanceTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.SeedEvaluationTests();self.f.setUp()
        self.attempt=self.f.evaluate().attempt

    def audit(self,attempt):
        return trace_balance(attempt,self.f.f.parts,self.f.f.ports,voltage_tolerance_v=1e-8)

    def test_failed_m5_is_excluded_and_accepted_prefix_balances(self):
        r=self.audit(self.attempt)
        self.assertEqual(r.coverage,"ACCEPTED_PREFIX_ONLY")
        self.assertEqual([s.mode for s in r.segments],["M1","M2","M3","M4"])
        self.assertAlmostEqual(r.output_charge_residual_c,0.,places=10)
        np.testing.assert_allclose(r.inductor_residual_vs,0.,atol=1e-11)
        np.testing.assert_allclose(r.capacitor_residual_c,0.,atol=1e-11)
        self.assertGreater(r.total_output_charge_c,0.) # Prefix charging is not nonperiodicity proof.

    def test_missing_segment_cannot_be_hidden_by_endpoint_comparison(self):
        with self.assertRaises(ValueError):
            self.audit(replace(self.attempt,steps=self.attempt.steps[1:]))

    def test_partial_trajectory_cannot_be_labeled_full(self):
        with self.assertRaises(ValueError):
            self.audit(replace(self.attempt,end=self.attempt.last_accepted))

    def test_wrong_output_capacitance_breaks_integral_identity(self):
        # Deliberate model mismatch: do not silently accept old states under new C.
        bad_parts=replace(self.f.f.parts,output_f=24.)
        r=trace_balance(self.attempt,bad_parts,self.f.f.ports,voltage_tolerance_v=1e-8)
        self.assertGreater(abs(r.output_charge_residual_c),1e-3)


if __name__=="__main__":unittest.main()
