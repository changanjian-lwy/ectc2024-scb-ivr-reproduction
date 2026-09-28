"""Synthetic affine fixtures; volt-second identities, not design data."""
from dataclasses import replace
import unittest
import numpy as np
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts
from scb_ivr.p25_native_events import NativeBoundary, MODES
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_freewheel_margin import freewheel_margin


class FreewheelTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","absolute",0,0.,12.,
            (8.,4.,0.,0.,0.,1.),(20.,-1.,.75),{m.name:m.gates for m in MODES}["M5"])
        self.ports=ConstantPorts(1.,0.,"synthetic constant-current ports")

    def flow(self,s=None,parts=None):
        return LocalFlow(s or self.s,parts or self.parts,"M5",self.ports,voltage_tolerance_v=1e-8)

    def test_integral_zero_and_additivity(self):
        f=self.flow()
        np.testing.assert_array_equal(f.integrated_coordinates(0.),np.zeros(9))
        split=f.integrated_coordinates(.1)+self.flow(f.at(.1)).integrated_coordinates(.3)
        np.testing.assert_allclose(split,f.integrated_coordinates(.3),atol=1e-12)

    def test_dynamic_vo_flux_balance(self):
        f=self.flow(); r=freewheel_margin(f,3,.3,current_tolerance_a=1e-8)
        self.assertAlmostEqual(r.balance_residual_vs,0.,places=12)
        self.assertAlmostEqual(r.consumed_flux_vs,r.output_volt_seconds,places=12)
        self.assertNotAlmostEqual(r.output_volt_seconds,.3*self.s.voltage_v[-1],places=5)

    def test_shared_output_charge_matches_voltage_change(self):
        f=self.flow(); end=.3; integ=f.integrated_coordinates(end)
        delivered=sum(integ[6:9])+(self.ports.other_modules_current_a-self.ports.load_current_a)*end
        stored=self.parts.output_f*(f.at(end).voltage_v[-1]-self.s.voltage_v[-1])
        self.assertAlmostEqual(delivered,stored,places=12)

    def test_winding_term_not_silently_omitted(self):
        f=self.flow(parts=replace(self.parts,winding_ohm=(.2,.3,.4)))
        r=freewheel_margin(f,3,.3,current_tolerance_a=1e-8)
        self.assertGreater(r.winding_volt_seconds,0.)
        self.assertAlmostEqual(r.balance_residual_vs,0.,places=12)
        self.assertGreater(abs(r.initial_flux_vs-r.output_volt_seconds-4*r.actual_current_a),.01)

    def test_nonzero_node_residual_is_accounted_not_projected(self):
        f=self.flow(replace(self.s,voltage_v=(8.,4.,0.,0.,1e-9,1.)))
        r=freewheel_margin(f,3,.3,current_tolerance_a=1e-8)
        self.assertAlmostEqual(r.switch_node_volt_seconds,3e-10,places=18)
        self.assertAlmostEqual(r.balance_residual_vs,0.,places=12)

    def test_switching_phase_not_claimed_freewheel(self):
        with self.assertRaises(ValueError): freewheel_margin(self.flow(),2,.3,current_tolerance_a=1e-8)

    def test_multimodule_not_silently_treated_single(self):
        s=replace(self.s,boundary=replace(self.s.boundary,nM=2))
        with self.assertRaises(ValueError): freewheel_margin(self.flow(s),3,.3,current_tolerance_a=1e-8)


if __name__=="__main__": unittest.main()
