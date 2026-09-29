"""D35 exact network pairing; no topology rotation or trajectory reset."""
from dataclasses import replace
import unittest
import test_p25_commutation_cycle as fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_down_commutation_charge import down_commutation_charge
from scripts.audit_p25_down_charge import run_down_charge_audit


class DownChargeTests(unittest.TestCase):
    def test_three_phases_match_closed_form_and_integral(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        for mode in ("M2","M7","M12"):
            flow = f.flow(mode); r = down_commutation_charge(flow,.01)
            self.assertAlmostEqual(r.closed_form_capacitance_f,r.network_rate_capacitance_f,places=12)
            self.assertAlmostEqual(r.voltage_balance_residual_v,0.,places=12)
            self.assertAlmostEqual(r.required_charge_c-r.phase_charge_c-r.other_charge_c,
                                   r.remaining_charge_c,places=12)

    def test_nonzero_winding_R_does_not_change_network_charge_identity(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        flow = LocalFlow(f.state("M2"),replace(f.parts,winding_ohm=(.1,.2,.3)),"M2",f.ports,
                         voltage_tolerance_v=1e-8)
        self.assertAlmostEqual(down_commutation_charge(flow,.01).voltage_balance_residual_v,0.,places=12)

    def test_d34_stops_before_low_side_zero(self):
        for row in run_down_charge_audit()["cases"]:
            b = row["budget"]
            self.assertGreater(b["end_vds_v"],0.)
            self.assertLess(b["phase_charge_c"],b["required_charge_c"])
            self.assertLess(abs(b["voltage_balance_residual_v"]),1e-11)

    def test_wrong_target_mode_rejected(self):
        f = fixtures.CommutationCycleTests(); f.setUp()
        with self.assertRaises(ValueError):
            down_commutation_charge(f.flow("M5"),.01)


if __name__ == "__main__":
    unittest.main()
