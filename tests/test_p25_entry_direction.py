"""P25 three-phase single-module synthetic entry tests, not paper cases."""
from dataclasses import replace
import unittest
from scb_ivr.p25_entry_direction import DirectionTolerance, classify_entry
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts, scan_commutation
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary, MODES
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_reverse_contract import ReverseModel
from scb_ivr.p25_root_location import RootSettings


class EntryDirectionTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","clock",0,0.,
            12.,(12.,4.,2.,0.,0.,1.),(20.,2.,3.),{m.name:m.gates for m in MODES}["M2"])
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"ideal mathematical branch")
        self.tol=DirectionTolerance(1e-8,1e-8,1e-10,1e-10)
        self.root=RootSettings(1e-9,1e-8,100,"pre-event continuation")

    def flow(self,s=None,mode="M2"):
        return LocalFlow(s or self.s,self.parts,mode,ConstantPorts(1.,0.,"constant synthetic"),voltage_tolerance_v=1e-10)

    def test_high_just_off_leaves_zero_without_reopening(self):
        flow=self.flow(); report=classify_entry(flow,self.reverse,self.tol)
        self.assertEqual(report.blockers,())
        self.assertEqual(report.release_names,("reverse.SH1",))
        self.assertGreater(next(i.rate for i in report.items if i.name=="reverse.SH1"),0.)
        self.assertEqual(flow.at(0.),self.s)

    def test_integrated_scan_reaches_target_without_epsilon_reset(self):
        report=scan_commutation(self.flow(),self.reverse,end_s=1.,intervals=100,
            voltage_settings=self.root,current_settings=self.root,entry_direction=self.tol)
        self.assertIn("target.SL1",report.candidates)
        self.assertIn("reverse.SL1",report.candidates)

    def test_m1_endpoint_reused_as_m2_entry_without_electrical_reset(self):
        initial=replace(self.s,gates={m.name:m.gates for m in MODES}["M1"])
        end=self.flow(initial,"M1").at(.02)  # synthetic declared on interval
        entry=replace(end,gates=self.s.gates)
        flow=self.flow(entry)
        self.assertEqual(entry.voltage_v,end.voltage_v)
        self.assertEqual(entry.current_a,end.current_a)
        self.assertEqual(entry.time_s,end.time_s)
        self.assertEqual(classify_entry(flow,self.reverse,self.tol).blockers,())
        report=scan_commutation(flow,self.reverse,end_s=1.,intervals=100,
            voltage_settings=self.root,current_settings=self.root,entry_direction=self.tol)
        self.assertIn("target.SL1",report.candidates)

    def test_low_just_off_in_m5_leaves_zero(self):
        s=replace(self.s,voltage_v=(8.,4.,0.,0.,0.,1.),current_a=(20.,-10.,20.),
            gates={m.name:m.gates for m in MODES}["M5"])
        report=classify_entry(self.flow(s,"M5"),self.reverse,self.tol)
        self.assertEqual(report.release_names,("reverse.SL2",))
        self.assertEqual(report.blockers,())

    def test_outward_current_requires_reverse_solver_not_free_flow(self):
        report=classify_entry(self.flow(replace(self.s,current_a=(-20.,2.,3.))),self.reverse,self.tol)
        self.assertEqual(next(i.status for i in report.items if i.name=="reverse.SH1"),"REVERSE_RESOLUTION_REQUIRED")
        self.assertIn("domain.iL1",report.blockers)

    def test_tangent_zero_does_not_pass(self):
        report=classify_entry(self.flow(replace(self.s,current_a=(0.,2.,3.))),self.reverse,self.tol)
        self.assertEqual(next(i.status for i in report.items if i.name=="reverse.SH1"),"TANGENT_OR_RATE_UNRESOLVED")

    def test_near_zero_not_projected(self):
        s=replace(self.s,voltage_v=(12.-1e-9,4.,2.,0.,0.,1.))
        report=classify_entry(self.flow(s),self.reverse,self.tol)
        self.assertEqual(next(i.status for i in report.items if i.name=="reverse.SH1"),"NEAR_BOUNDARY_UNRESOLVED")

    def test_target_at_entry_is_not_treated_as_release(self):
        s=replace(self.s,voltage_v=(8.,4.,0.,0.,0.,1.))
        report=classify_entry(self.flow(s),self.reverse,self.tol)
        self.assertIn("target.SL1",report.blockers)

    def test_multimodule_rejected_and_np4_rejected_upstream(self):
        with self.assertRaises(ValueError):
            classify_entry(self.flow(replace(self.s,boundary=replace(self.s.boundary,nM=2))),self.reverse,self.tol)
        with self.assertRaises(ValueError):
            replace(self.s.boundary,nP=4)


if __name__=="__main__":
    unittest.main()
