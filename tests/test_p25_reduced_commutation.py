"""D26 independent five-state/full-network propagation comparisons."""
from dataclasses import replace
import unittest
import numpy as np
import test_p25_commutation_cycle as fixtures
import test_p25_seed_evaluation as seed_fixtures
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_reduced_commutation import ReducedCommutation


class ReducedCommutationTests(unittest.TestCase):
    def test_three_asymmetric_phases_match_full_network_over_time(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        parts=replace(f.parts,coss_f=(1.,2.,3.,4.,5.,6.),winding_ohm=(.1,.2,.3))
        for m in ("M5","M10","M15"):
            full=LocalFlow(f.state(m),parts,m,f.ports,voltage_tolerance_v=1e-8)
            small=ReducedCommutation(full.start,parts,m,f.ports,gate_tolerance_v=1e-8)
            for t in (0.,.01,.1,.3):
                a=full.at(t); b=small.at(t)
                np.testing.assert_allclose([b.target_vds_v,*b.current_a,b.output_v],
                    [a.switch_voltage(small.target),*a.current_a,a.voltage_v[5]],rtol=1e-12,atol=1e-12)

    def test_old_failure_endpoint_and_dynamic_output_are_retained(self):
        f=seed_fixtures.SeedEvaluationTests();f.setUp();r=f.evaluate()
        s=r.attempt.last_accepted.last_event
        t=r.attempt.steps[-1].outcome.scan.windows[0].latest_s
        small=ReducedCommutation(s,f.f.parts,"M5",f.f.ports,gate_tolerance_v=1e-8)
        end=small.at(t)
        self.assertAlmostEqual(end.current_a[2],0.,places=8)
        self.assertAlmostEqual(end.target_vds_v,5.98351164,places=7)
        self.assertGreater(end.output_v,s.voltage_v[5])

    def test_nonzero_on_node_residual_kept_not_projected(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        s=f.state("M5"); v=list(s.voltage_v);v[2]=1e-10
        s=replace(s,voltage_v=tuple(v))
        full=LocalFlow(s,f.parts,"M5",f.ports,voltage_tolerance_v=1e-8)
        small=ReducedCommutation(s,f.parts,"M5",f.ports,gate_tolerance_v=1e-8)
        np.testing.assert_allclose(small.at(.1).current_a,full.at(.1).current_a,atol=1e-12,rtol=1e-12)
        self.assertEqual(small.generator[1,5],1e-10/f.parts.inductance_h[0])

    def test_no_wrong_gates_or_backward_time(self):
        f=fixtures.CommutationCycleTests();f.setUp()
        with self.assertRaises(ValueError):
            ReducedCommutation(f.state("M5"),f.parts,"M10",f.ports,gate_tolerance_v=1e-8)
        small=ReducedCommutation(f.state("M5"),f.parts,"M5",f.ports,gate_tolerance_v=1e-8)
        with self.assertRaises(ValueError):small.at(-1.)


if __name__=="__main__":unittest.main()
