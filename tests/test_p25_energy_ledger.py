"""D32 residual work and broken endpoint are not hidden in energy bookkeeping."""
from dataclasses import replace
import unittest
import test_p25_seed_evaluation as fixtures
import test_p25_commutation_cycle as cycle_fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_energy_ledger import accepted_energy_ledger, segment_energy


class EnergyLedgerTests(unittest.TestCase):
    options = dict(voltage_tolerance_v=1e-8, quadrature_abs_j=1e-10, quadrature_rel=1e-10)

    def test_accepted_prefix_only_closes_with_residual_work_separate(self):
        f = fixtures.SeedEvaluationTests(); f.setUp()
        coverage, rows = accepted_energy_ledger(f.evaluate().attempt, f.f.parts, f.f.ports, **self.options)
        self.assertEqual(coverage, "ACCEPTED_PREFIX_ONLY")
        self.assertEqual([r.mode for r in rows], ["M1", "M2", "M3", "M4"])
        for row in rows:
            self.assertLess(abs(row.balance_residual_j), 1e-9)
            self.assertEqual(row.winding_j, 0.)
        self.assertGreater(abs(sum(r.on_residual_work_j for r in rows)), 1e-10)

    def test_nonzero_winding_loss_closes(self):
        f = cycle_fixtures.CommutationCycleTests(); f.setUp()
        parts = replace(f.parts, winding_ohm=(.1,.2,.3))
        flow = LocalFlow(f.state("M5"), parts, "M5", f.ports, voltage_tolerance_v=1e-8)
        r = segment_energy(flow, flow.at(.01), **self.options)
        self.assertGreater(r.winding_j, 0.)
        self.assertLess(abs(r.balance_residual_j), 1e-9)

    def test_wrong_endpoint_energy_is_detected(self):
        f = cycle_fixtures.CommutationCycleTests(); f.setUp(); flow = f.flow("M5")
        end = flow.at(.01); v = list(end.voltage_v); v[5] += .1
        r = segment_energy(flow, replace(end, voltage_v=tuple(v)), **self.options)
        self.assertGreater(abs(r.balance_residual_j), 1.)

    def test_explicit_nonzero_on_offset_is_not_silently_zero_loss(self):
        f = cycle_fixtures.CommutationCycleTests(); f.setUp(); s = f.state("M5")
        v = list(s.voltage_v); v[2] = .001
        flow = LocalFlow(replace(s, voltage_v=tuple(v)), f.parts, "M5", f.ports, voltage_tolerance_v=.002)
        r = segment_energy(flow, flow.at(.01), **{**self.options, "voltage_tolerance_v":.002})
        self.assertGreater(abs(r.on_residual_work_j), 1e-5)
        self.assertLess(abs(r.balance_residual_j), 1e-9)


if __name__ == "__main__":
    unittest.main()
