"""Synthetic linear trajectories only; no paper operating-point tuning."""
from dataclasses import replace
import unittest
from scb_ivr.p25_control_memory import Policy, Stage, Memory, KnownPeak, Trigger, start_at_high_on, transition
from scb_ivr.p25_handoff import enter_all_low, reach_second_current_zero
from scb_ivr.p25_entry_direction import DirectionTolerance
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import ConstantPorts, LocalFlow
from scb_ivr.p25_native_events import NativeBoundary, MODES, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings
from scb_ivr.p25_negative_handoff import reach_negative_target, enter_second_high


class NegativeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic F/H fixture")
        self.ports=ConstantPorts(1.,0.,"constant synthetic")
        self.policy=Policy((.02,)*3,1e-8,1e-8,1e-9,True,"synthetic")
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"ideal")
        self.root=RootSettings(1e-9,1e-8,100,"affine continuation")
        self.electrical=Tolerances(1e-8,1e-8,1e-8)
        self.direction=DirectionTolerance(1e-8,1e-8,1e-10,1e-10)
        s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","clock",0,0.,12.,
            (8.,4.,0.,0.,0.,1.),(20.,0.,20.),{m.name:m.gates for m in MODES}["M4"])
        peak=KnownPeak(PeakReference(2,20.,"declared_design_peak","synthetic not measured"),0.)
        self.m=Memory(1,Stage.NEGATIVE,0.,s,(None,peak,None),-1.)

    def negative(self,m=None):
        return reach_negative_target(m or self.m,self.parts,self.ports,self.policy,self.reverse,
            end_s=10.,intervals=200,voltage_root=self.root,current_root=self.root,
            electrical=self.electrical,current_rate_tolerance_a_s=1e-10)

    def high(self,m):
        return enter_second_high(m,self.parts,self.ports,self.policy,self.reverse,end_s=m.entered_at_s+10.,
            intervals=200,voltage_root=self.root,current_root=self.root,electrical=self.electrical,direction=self.direction)

    def test_m4_target_reached_and_low_off_without_reset(self):
        r=self.negative()
        self.assertEqual(r.status,"CONDITIONAL_M5_ENTRY",r.reason)
        s=r.memory.last_event
        expected=LocalFlow(self.m.last_event,self.parts,"M4",self.ports,voltage_tolerance_v=1e-8).at(s.time_s)
        self.assertEqual(s.current_a,expected.current_a)
        self.assertEqual(s.voltage_v,expected.voltage_v)
        self.assertAlmostEqual(s.current_a[1],-1.,places=7)
        self.assertFalse(s.gates.low[1])
        # R=0/all-low identity remains exact for DYNAMIC output voltage:
        # Lk*(ik_end-ik_entry)=L2*(i2_end-i2_entry).
        for k in (0,2):
            self.assertAlmostEqual(self.parts.inductance_h[k]*(s.current_a[k]-self.m.last_event.current_a[k]),
                self.parts.inductance_h[1]*(s.current_a[1]-self.m.last_event.current_a[1]),places=10)

    def test_other_phase_zero_blocks_negative_target(self):
        m=replace(self.m,last_event=replace(self.m.last_event,current_a=(.01,0.,20.)))
        r=self.negative(m)
        self.assertEqual(r.status,"OTHER_M4_BOUNDARY_FIRST_OR_OVERLAP")
        self.assertIn("domain.iL1",r.scan.candidates)

    def test_missing_target_not_guessed(self):
        with self.assertRaises(ValueError): self.negative(replace(self.m,latched_target_a=None))

    def test_isolated_m4_fixture_continues_to_m6_after_derivative_identity_fix(self):
        r=self.high(self.negative().memory)
        self.assertEqual(r.status,"CONDITIONAL_M6_ENTRY")
        self.assertEqual(r.memory.phase,2)

    def test_stronger_synthetic_m5_entry_can_reach_high_event(self):
        # Independent fixture, NOT changed alpha or claimed continuation of above case.
        s=replace(self.m.last_event,voltage_v=(8.,4.,0.,0.,0.,1.),current_a=(20.,-10.,20.),
            gates={m.name:m.gates for m in MODES}["M5"])
        m=Memory(1,Stage.UP_COMM,0.,s,(None,)*3,-10.)
        r=self.high(m)
        self.assertEqual(r.status,"CONDITIONAL_M6_ENTRY",r.reason)
        self.assertEqual(r.memory.phase,2)
        self.assertTrue(r.memory.last_event.gates.high[1])
        self.assertLess(r.memory.last_event.current_a[1],0.)

    def test_connected_d12_fixture_first_fails_at_phase3_in_m5(self):
        s=replace(self.m.last_event,voltage_v=(12.,4.,2.,0.,0.,1.),current_a=(20.,2.,3.),
            gates={m.name:m.gates for m in MODES}["M1"])
        m=start_at_high_on(s,phase=1,peaks=self.m.peaks,policy=self.policy)
        end=LocalFlow(s,self.parts,"M1",self.ports,voltage_tolerance_v=1e-8).at(.02)
        m=transition(m,Trigger.HIGH_OFF_DUE,end,policy=self.policy)
        common=dict(voltage_root=self.root,current_root=self.root,electrical=self.electrical)
        m=enter_all_low(m,self.parts,self.ports,self.policy,self.reverse,end_s=1.,intervals=100,
            direction=self.direction,**common).memory
        m=reach_second_current_zero(m,self.parts,self.ports,self.policy,self.reverse,
            end_s=m.entered_at_s+10.,intervals=200,**common).memory
        m=reach_negative_target(m,self.parts,self.ports,self.policy,self.reverse,end_s=m.entered_at_s+10.,
            intervals=200,current_rate_tolerance_a_s=1e-10,**common).memory
        self.assertEqual(m.last_event.voltage_v[3],0.)
        times=[]
        for count in (200,400,800):
            r=enter_second_high(m,self.parts,self.ports,self.policy,self.reverse,
                end_s=m.entered_at_s+10.,intervals=count,direction=self.direction,**common)
            self.assertEqual(r.status,"BLOCKED_BEFORE_JOINT_HIGH_EVENT")
            self.assertEqual(r.scan.candidates,("domain.iL3",))
            self.assertIsNone(r.memory)
            times.append(r.scan.windows[0].latest_s)
        self.assertLess(max(times)-min(times),2e-9)


if __name__=="__main__": unittest.main()
