"""D25 variable-output, asymmetric-network checks; no new device assumptions."""
from dataclasses import replace
import unittest
import test_p25_commutation_cycle as fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_commutation_dynamics import audit_commutation_dynamics


class CommutationDynamicsTests(unittest.TestCase):
    def test_all_phases_full_generator_matches_ode_with_dynamic_output_and_resistance(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        parts=replace(f.parts,coss_f=(1.,2.,3.,4.,5.,6.),winding_ohm=(.1,.2,.3))
        for mode in ("M5","M10","M15"):
            flow=LocalFlow(f.state(mode),parts,mode,f.ports,voltage_tolerance_v=1e-8)
            for t in (0.,.01,.03):
                r=audit_commutation_dynamics(flow,t)
                self.assertAlmostEqual(r.ode_residual_v,0.,places=11)
                self.assertAlmostEqual(r.node_relation_residual_v,0.,places=11)
            self.assertNotEqual(r.actual_output_v,flow.start.voltage_v[5])

    def test_node_capacitance_is_not_target_normalization(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        for mode in ("M5","M10","M15"):
            r=audit_commutation_dynamics(f.flow(mode),.01)
            self.assertGreater(r.gamma,1.)
            self.assertLess(r.node_capacitance_f,r.normalized_capacitance_f)

    def test_wrong_mode_is_rejected(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        with self.assertRaises(ValueError):
            audit_commutation_dynamics(f.flow("M2"),.01)


if __name__=="__main__":unittest.main()
