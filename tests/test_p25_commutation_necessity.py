"""D30 exact-premise diagnostics; no projection of earlier trajectory."""
from dataclasses import replace
import unittest
import test_p25_commutation_cycle as fixtures
import test_p25_seed_evaluation as seed_fixtures
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_commutation_necessity import commutation_necessity


class ChargeNecessityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CommutationCycleTests(); self.f.setUp()

    def check(self, state, mode="M5", **changes):
        return commutation_necessity(state, changes.get("parts", self.f.parts), mode,
                                     self.f.ports, charge_margin_c=1e-10)

    def test_three_phases_have_small_flux_obstruction(self):
        for mode in ("M5", "M10", "M15"):
            q = cycle_mode(mode).next_phase-1
            i = [20.,20.,20.]; i[q] = -.1; i[(q+1)%3] = .01
            s = replace(self.f.state(mode), current_a=tuple(i))
            r = self.check(s, mode)
            self.assertEqual(r.status, "TARGET_BEFORE_OTHER_ZERO_IMPOSSIBLE")
            self.assertGreater(r.required_charge_c, r.maximum_charge_c)

    def test_old_continuous_seed_not_projected_to_zero_nodes(self):
        f = seed_fixtures.SeedEvaluationTests(); f.setUp()
        state = f.evaluate().attempt.last_accepted.last_event
        r = commutation_necessity(state, f.f.parts, "M5", f.f.ports, charge_margin_c=1e-10)
        self.assertEqual(r.status, "NOT_APPLICABLE")
        self.assertIn("residual", r.reason)

    def test_nonzero_resistance_and_failed_output_premise_are_not_impossibility(self):
        s = self.f.state("M5")
        r = self.check(s, parts=replace(self.f.parts, winding_ohm=(1.,0.,0.)))
        self.assertEqual(r.status, "NOT_APPLICABLE")
        self.assertEqual(self.check(s).status, "NOT_APPLICABLE")

    def test_large_charge_capacity_is_not_success(self):
        s = replace(self.f.state("M5"), current_a=(100.,-1.,1.))
        v = list(s.voltage_v); v[5] = .001
        r = self.check(replace(s, voltage_v=tuple(v)))
        self.assertEqual(r.status, "NOT_EXCLUDED_NOT_SUFFICIENT")


if __name__ == "__main__":
    unittest.main()
