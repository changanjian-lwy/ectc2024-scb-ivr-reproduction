"""D23 synthetic endpoint accounting, retaining the full capacitance network."""
import unittest
import test_p25_seed_evaluation as fixtures
import test_p25_commutation_cycle as cycle_fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_commutation_charge import commutation_charge


class CommutationChargeTests(unittest.TestCase):
    def test_old_failed_trajectory_charge_gap_and_voltage_balance(self):
        f=fixtures.SeedEvaluationTests(); f.setUp(); r=f.evaluate()
        flow=LocalFlow(r.attempt.last_accepted.last_event,f.f.parts,"M5",f.f.ports,voltage_tolerance_v=1e-8)
        t=r.attempt.steps[-1].outcome.scan.windows[0].latest_s
        b=commutation_charge(flow,t)
        self.assertAlmostEqual(b.voltage_balance_residual_v,0.,places=12)
        self.assertAlmostEqual(b.required_normalized_charge_c-b.negative_phase_charge_c-
                               b.other_normalized_charge_c,b.remaining_normalized_charge_c,places=12)
        self.assertAlmostEqual(b.normalized_capacitance_f,3.219298245614,places=10)
        self.assertAlmostEqual(b.end_vds_v,5.98351164,places=7)
        self.assertLess(b.negative_phase_charge_c/b.required_normalized_charge_c,.06)

    def test_all_three_up_commutations_keep_zero_length_and_full_terms(self):
        f=cycle_fixtures.CommutationCycleTests(); f.setUp()
        for mode in ("M5","M10","M15"):
            flow=f.flow(mode)
            zero=commutation_charge(flow,flow.start.time_s)
            self.assertEqual(zero.negative_phase_charge_c,0.)
            self.assertEqual(zero.remaining_normalized_charge_c,zero.required_normalized_charge_c)
            b=commutation_charge(flow,.01)
            self.assertAlmostEqual(b.voltage_balance_residual_v,0.,places=12)
            self.assertEqual(len(b.rate_coefficients),10)

    def test_down_commutation_not_mislabeled_as_negative_charge(self):
        f=cycle_fixtures.CommutationCycleTests(); f.setUp()
        with self.assertRaises(ValueError):
            commutation_charge(f.flow("M2"),.01)


if __name__=="__main__":unittest.main()
