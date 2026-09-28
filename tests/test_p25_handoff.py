"""Actual affine synthetic trajectories, NOT paper operating points."""
from dataclasses import replace
import unittest
from scb_ivr.p25_control_memory import Policy, Stage, Trigger, KnownPeak, start_at_high_on, transition
from scb_ivr.p25_entry_direction import DirectionTolerance
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_handoff import enter_all_low, reach_second_current_zero
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts
from scb_ivr.p25_native_events import NativeBoundary, MODES, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.ports=ConstantPorts(1.,0.,"synthetic constant ports")
        self.policy=Policy((.02,)*3,1e-8,1e-8,1e-9,True,"synthetic ideal driver")
        self.s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","absolute",0,0.,
            12.,(12.,4.,2.,0.,0.,1.),(20.,2.,3.),{m.name:m.gates for m in MODES}["M1"])
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"ideal")
        self.root=RootSettings(1e-9,1e-8,100,"local affine continuation")
        self.direction=DirectionTolerance(1e-8,1e-8,1e-10,1e-10)
        self.electrical=Tolerances(1e-8,1e-8,1e-8)

    def initial_memory(self,s=None):
        s=s or self.s
        m=start_at_high_on(s,phase=1,peaks=(None,)*3,policy=self.policy)
        end=LocalFlow(s,self.parts,"M1",self.ports,voltage_tolerance_v=1e-8).at(.02)
        return transition(m,Trigger.HIGH_OFF_DUE,end,policy=self.policy)

    def run_handoff(self,m,**changes):
        args=dict(end_s=1.,intervals=100,voltage_root=self.root,current_root=self.root,
                  direction=self.direction,electrical=self.electrical)
        args.update(changes)
        return enter_all_low(m,self.parts,self.ports,self.policy,self.reverse,**args)

    def test_m1_m2_m3_connected_no_state_reset(self):
        m=self.initial_memory(); result=self.run_handoff(m)
        self.assertEqual(result.status,"CONDITIONAL_M3_ENTRY",result.reason)
        self.assertEqual(result.memory.stage,Stage.ALL_LOW)
        s=result.memory.last_event
        expected=LocalFlow(m.last_event,self.parts,"M2",self.ports,voltage_tolerance_v=1e-8).at(s.time_s)
        self.assertEqual(s.voltage_v,expected.voltage_v)
        self.assertEqual(s.current_a,expected.current_a)
        self.assertEqual(result.pre_reverse_status,"LOCAL_COMPLEMENTARITY_ONLY")
        self.assertEqual(result.post_reverse_status,"LOCAL_COMPLEMENTARITY_ONLY")

    def test_other_phase_first_blocks_instead_of_forcing_gate(self):
        result=self.run_handoff(self.initial_memory(replace(self.s,current_a=(20.,.05,3.))))
        self.assertEqual(result.status,"BLOCKED_BEFORE_JOINT_LOW_EVENT")
        self.assertIn("domain.iL2",result.scan.candidates)
        self.assertIsNone(result.memory)

    def test_short_horizon_is_not_declared_infeasible(self):
        m=self.initial_memory()
        result=self.run_handoff(m,end_s=.021)
        self.assertEqual(result.scan.status,"NO_DOWNWARD_BRACKET_OBSERVED")
        self.assertIsNone(result.memory)

    def test_layer_tolerance_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.run_handoff(self.initial_memory(),electrical=Tolerances(1e-6,1e-8,1e-8))

    def run_m3(self,m):
        return reach_second_current_zero(m,self.parts,self.ports,self.policy,self.reverse,
            end_s=m.entered_at_s+10.,intervals=200,voltage_root=self.root,current_root=self.root,
            electrical=self.electrical)

    def test_m3_missing_peak_blocks_at_real_zero_not_guessed(self):
        m=self.run_handoff(self.initial_memory()).memory
        result=self.run_m3(m)
        self.assertEqual(result.status,"M3_CONTROL_REJECTED",result.reason)
        self.assertIn("peak reference unavailable",result.reason)

    def test_connected_m1_to_m4_with_declared_design_reference(self):
        m=self.initial_memory()
        ref=KnownPeak(PeakReference(2,20.,"declared_design_peak","synthetic reference, not measured"),0.)
        m=replace(m,peaks=(None,ref,None))
        m=self.run_handoff(m).memory
        result=self.run_m3(m)
        self.assertEqual(result.status,"CONDITIONAL_M4_ENTRY",result.reason)
        after=result.memory
        self.assertEqual(after.stage,Stage.NEGATIVE)
        self.assertEqual(after.latched_target_a,-1.)
        self.assertEqual(after.last_event.gates,m.last_event.gates)
        exact=LocalFlow(m.last_event,self.parts,"M3",self.ports,voltage_tolerance_v=1e-8).at(after.entered_at_s)
        self.assertEqual(after.last_event.voltage_v,exact.voltage_v)
        self.assertEqual(after.last_event.current_a,exact.current_a)


if __name__=="__main__": unittest.main()
