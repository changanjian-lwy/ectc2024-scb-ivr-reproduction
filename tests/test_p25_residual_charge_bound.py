"""D31 tests preserve, rather than erase, entry residuals."""
from dataclasses import replace
import unittest
import test_p25_commutation_cycle as fixtures
import test_p25_seed_evaluation as seed_fixtures
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_commutation_necessity import commutation_necessity
from scb_ivr.p25_residual_charge_bound import residual_charge_bound
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_commutation_charge import commutation_charge


class ResidualChargeBoundTests(unittest.TestCase):
    def test_reduces_to_d30_for_zero_other_nodes(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        for mode in ("M5", "M10", "M15"):
            q = cycle_mode(mode).next_phase-1
            i = [20.,20.,20.]; i[q] = -.1; i[(q+1)%3] = .01
            s = replace(f.state(mode), current_a=tuple(i))
            a = commutation_necessity(s, f.parts, mode, f.ports, charge_margin_c=1e-10)
            b = residual_charge_bound(s, f.parts, mode, f.ports, charge_margin_c=1e-10)
            self.assertEqual(a.status, b.status)
            self.assertAlmostEqual(a.maximum_charge_c, b.maximum_charge_c)
            self.assertAlmostEqual(a.maximum_duration_s, b.maximum_duration_s)

    def test_old_seed_charge_and_time_are_below_derived_upper_bounds(self):
        f = seed_fixtures.SeedEvaluationTests(); f.setUp()
        r = f.evaluate(); s = r.attempt.last_accepted.last_event
        before = s.voltage_v
        b = residual_charge_bound(s, f.f.parts, "M5", f.f.ports, charge_margin_c=1e-10)
        self.assertEqual(b.status, "TARGET_BEFORE_OTHER_ZERO_IMPOSSIBLE")
        end = r.attempt.steps[-1].outcome.scan.windows[0].latest_s
        flow = LocalFlow(s, f.f.parts, "M5", f.f.ports, voltage_tolerance_v=1e-8)
        charge = commutation_charge(flow, end)
        self.assertLess(charge.negative_phase_charge_c, b.maximum_charge_c)
        self.assertLess(end-s.time_s, b.maximum_duration_s)
        self.assertGreater(b.required_charge_c, b.maximum_charge_c)
        self.assertEqual(before, s.voltage_v)
        self.assertNotEqual(s.voltage_v[2], 0.)

    def test_positive_and_negative_offsets_are_retained(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        s = replace(f.state("M5"), current_a=(100.,-1.,1.))
        results = []
        for offset in (-.01, 0., .01):
            v = list(s.voltage_v); v[4] = offset
            b = residual_charge_bound(replace(s, voltage_v=tuple(v)), f.parts, "M5", f.ports,
                                      charge_margin_c=1e-10)
            self.assertNotEqual(b.status, "NOT_APPLICABLE")
            results.append(b.maximum_duration_s)
        self.assertLess(results[0], results[1]); self.assertLess(results[1], results[2])

    def test_no_output_voltage_gap_cannot_produce_bound(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        s = f.state("M5"); v = list(s.voltage_v); v[4] = v[5]
        b = residual_charge_bound(replace(s, voltage_v=tuple(v)), f.parts, "M5", f.ports,
                                  charge_margin_c=1e-10)
        self.assertEqual(b.status, "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
