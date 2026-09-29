"""D27 all-node reconstruction, not a replacement of full event scanning."""
from dataclasses import replace
import unittest
import numpy as np
import test_p25_commutation_cycle as fixtures
import test_p25_seed_evaluation as seed_fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_reduced_commutation import ReducedCommutation
from scb_ivr.p25_nodal_contract import SWITCHES
from scb_ivr.p25_root_location import Quantity,locate_downward


class ReconstructionTests(unittest.TestCase):
    def test_all_nodes_and_six_switch_voltages_match_on_all_phases(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        parts=replace(f.parts,coss_f=(1.,2.,3.,4.,5.,6.),winding_ohm=(.1,.2,.3))
        for mode in ("M5","M10","M15"):
            full=LocalFlow(f.state(mode),parts,mode,f.ports,voltage_tolerance_v=1e-8)
            reduced=ReducedCommutation(full.start,parts,mode,f.ports,gate_tolerance_v=1e-8)
            self.assertIs(reduced.snapshot_at(0.),full.start)
            for t in (.01,.1,.3):
                a=full.at(t); b=reduced.snapshot_at(t)
                np.testing.assert_allclose(a.voltage_v,b.voltage_v,rtol=1e-12,atol=1e-12)
                np.testing.assert_allclose([a.switch_voltage(n) for n in SWITCHES],
                                           [b.switch_voltage(n) for n in SWITCHES],rtol=1e-12,atol=1e-12)
                self.assertEqual((a.boundary,a.gates,a.run_id,a.clock_id,a.cycle),
                                 (b.boundary,b.gates,b.run_id,b.clock_id,b.cycle))

    def test_actual_failure_root_and_competing_high_voltage_match(self):
        f=seed_fixtures.SeedEvaluationTests();f.setUp();r=f.evaluate()
        s=r.attempt.last_accepted.last_event
        reduced=ReducedCommutation(s,f.f.parts,"M5",f.f.ports,gate_tolerance_v=1e-8)
        # Independent broad bracket around the known diagnostic boundary.
        root=locate_downward(Quantity("domain.iL3","A",lambda x:x.current_a[2]),
                            reduced.snapshot_at,left_s=4.,right_s=4.2,settings=f.f.root)
        self.assertAlmostEqual(root.right.time_s,r.attempt.steps[-1].outcome.scan.windows[0].latest_s,places=8)
        self.assertGreater(root.right.switch_voltage("SH2"),5.9)

    def test_nonzero_initial_node_residual_is_reconstructed_unchanged(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        s=f.state("M15"); v=list(s.voltage_v);v[3]=1e-11;v[4]=-1e-11
        s=replace(s,voltage_v=tuple(v))
        reduced=ReducedCommutation(s,f.parts,"M15",f.ports,gate_tolerance_v=1e-8)
        end=reduced.snapshot_at(.1)
        self.assertEqual(end.voltage_v[3:5],(1e-11,-1e-11))


if __name__=="__main__":unittest.main()
