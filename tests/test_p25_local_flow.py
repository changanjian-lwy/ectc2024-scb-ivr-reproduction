"""Synthetic F/H/s fixtures; not P25 operating points or ZVS proof."""
from dataclasses import replace
import unittest
import numpy as np
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import MODES, NativeBoundary
from scb_ivr.p25_nodal_contract import Components, instantaneous_rates
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts, scan_commutation
from scb_ivr.p25_reverse_contract import ReverseModel
from scb_ivr.p25_root_location import RootSettings


class LocalFlowTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.ports=ConstantPorts(1.,0.,"constant synthetic ports")
        self.start=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
            "synthetic","absolute",0,0.,12.,(8.,4.,2.,0.,0.,1.),(20.,2.,3.),
            {m.name:m.gates for m in MODES}["M2"])
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"mathematical ideal")
        self.settings=RootSettings(1e-9,1e-8,100,"affine pre-event continuation only")

    def flow(self,start=None,mode="M2"):
        return LocalFlow(start or self.start,self.parts,mode,self.ports,voltage_tolerance_v=1e-10)

    def scan(self,flow,end=1.):
        return scan_commutation(flow,self.reverse,end_s=end,intervals=100,
            voltage_settings=self.settings,current_settings=self.settings)

    def test_generator_matches_independent_d03_rhs(self):
        flow=self.flow()
        for t in (0.,.01,.05):
            s=flow.at(t)
            r=instantaneous_rates(s.boundary,self.parts,"M2",voltage_v=s.voltage_v,
                current_a=s.current_a,vin_v=12.,dvin_v_s=0.,load_current_a=1.,
                other_modules_current_a=0.,constraint_tolerance_v=1e-10,
                reverse_path_regime="off_reverse_channels_excluded_until_admission")
            rhs=flow.generator@np.r_[s.voltage_v,s.current_a,1.]
            np.testing.assert_allclose(rhs[:9],np.r_[r.voltage_rate_v_s,r.current_rate_a_s],atol=1e-12)

    def test_semigroup_preserves_gates_and_dynamic_output(self):
        flow=self.flow(); split=self.flow(flow.at(.02)).at(.05); full=flow.at(.05)
        np.testing.assert_allclose(split.voltage_v,full.voltage_v,atol=1e-12)
        np.testing.assert_allclose(split.current_a,full.current_a,atol=1e-12)
        self.assertEqual(full.gates,self.start.gates)
        self.assertNotEqual(full.voltage_v[-1],self.start.voltage_v[-1])
        self.assertEqual(flow.at(0.),self.start)

    def test_zero_voltage_target_and_reverse_are_not_arbitrarily_prioritized(self):
        result=self.scan(self.flow())
        self.assertIn("target.SL1",result.candidates)
        self.assertIn("reverse.SL1",result.candidates)
        self.assertIn("OVERLAP",result.status)

    def test_other_phase_can_fail_before_target(self):
        flow=self.flow(replace(self.start,current_a=(20.,.001,3.)))
        result=self.scan(flow)
        self.assertEqual(result.candidates,("domain.iL2",))

    def test_start_on_reverse_boundary_is_not_advanced_by_epsilon(self):
        flow=self.flow(replace(self.start,voltage_v=(12.,4.,2.,0.,0.,1.)))
        result=self.scan(flow)
        self.assertEqual(result.status,"ENTRY_BOUNDARY_UNRESOLVED")
        self.assertEqual(result.sampled_until_s,0.)

    def test_illegal_closure_and_other_module_injection_rejected(self):
        with self.assertRaises(ValueError):
            self.flow(replace(self.start,voltage_v=(8.,4.,2.,1.,0.,1.)))
        with self.assertRaises(ValueError):
            LocalFlow(self.start,self.parts,"M2",ConstantPorts(1.,1.,"invalid nM1"),voltage_tolerance_v=1e-10)

    def test_m5_flow_keeps_negative_entry_and_all_capacitor_dynamics(self):
        start=replace(self.start,voltage_v=(8.,4.,0.,1.,0.,1.),current_a=(20.,-10.,20.),
            gates={m.name:m.gates for m in MODES}["M5"])
        flow=self.flow(start,"M5"); end=flow.at(.01)
        self.assertLess(end.switch_voltage("SH2"),start.switch_voltage("SH2"))
        self.assertNotEqual(end.voltage_v[0],start.voltage_v[0])
        self.assertEqual(flow.at(0.).current_a[1],-10.)

    def test_on_low_derivative_exact_zero_but_state_never_projected(self):
        flow=self.flow()
        self.assertTrue(np.all(flow.generator[3:5]==0.))
        self.assertEqual(flow.at(.1).voltage_v[3:5],(0.,0.))
        s=replace(self.start,voltage_v=(8.,4.,2.,1e-12,0.,1.))
        # Within explicitly allowed algebraic tolerance, do not erase residual.
        f=LocalFlow(s,self.parts,"M2",self.ports,voltage_tolerance_v=1e-10)
        self.assertEqual(f.at(.1).voltage_v[3],1e-12)


if __name__=="__main__":
    unittest.main()
