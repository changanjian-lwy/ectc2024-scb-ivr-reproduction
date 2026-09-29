"""D18 synthetic high-on guards; not paper operating-point evidence."""
from dataclasses import replace
import unittest
from scb_ivr.p25_control_memory import Policy, Stage, start_at_high_on
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_high_on import advance_high_on
from scb_ivr.p25_native_events import NativeBoundary
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_local_flow import ConstantPorts, LocalFlow
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings


class HighOnTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        self.ports=ConstantPorts(1.,0.,"synthetic")
        self.policy=Policy((.02,)*3,1e-8,1e-8,1e-9,True,"ideal synthetic")
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"ideal")
        self.root=RootSettings(1e-9,1e-8,100,"affine flow")
        self.electrical=Tolerances(1e-8,1e-8,1e-8)

    def memory(self,phase):
        v={1:(12.,4.,4.,0.,0.,1.),2:(8.,8.,0.,4.,0.,1.),3:(8.,4.,0.,0.,4.,1.)}[phase]
        s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
                   "synthetic","absolute",4,0.,12.,v,(20.,20.,20.),
                   cycle_mode(f"M{5*(phase-1)+1}").gates)
        return start_at_high_on(s,phase=phase,peaks=(None,)*3,policy=self.policy)

    def run_on(self,m):
        return advance_high_on(m,self.parts,self.ports,self.policy,self.reverse,intervals=20,
                               voltage_root=self.root,current_root=self.root,electrical=self.electrical)

    def test_all_three_timers_preserve_state_and_do_not_invent_peaks(self):
        for phase in (1,2,3):
            m=self.memory(phase)
            r=self.run_on(m)
            with self.subTest(phase=phase):
                self.assertEqual(r.status,f"CONDITIONAL_M{5*(phase-1)+2}_ENTRY",r.reason)
                expected=LocalFlow(m.last_event,self.parts,f"M{5*(phase-1)+1}",self.ports,
                                   voltage_tolerance_v=1e-8).at(.02)
                self.assertEqual(r.memory.last_event.voltage_v,expected.voltage_v)
                self.assertEqual(r.memory.last_event.current_a,expected.current_a)
                self.assertEqual(r.memory.last_event.time_s,.02)
                self.assertEqual(r.memory.last_event.cycle,4)
                self.assertEqual(r.memory.peaks,(None,)*3)
                self.assertEqual(r.memory.stage,Stage.DOWN_COMM)

    def test_other_phase_zero_is_not_hidden_by_timer(self):
        for phase in (1,2,3):
            m=self.memory(phase); k=phase%3
            i=list(m.last_event.current_a); i[k]=.0001
            m=replace(m,last_event=replace(m.last_event,current_a=tuple(i)))
            r=self.run_on(m)
            with self.subTest(phase=phase):
                self.assertEqual(r.status,"HIGH_ON_BOUNDARY_BEFORE_OR_AT_OFF")
                self.assertEqual(r.scan.candidates,(f"domain.iL{k+1}",))
                self.assertIsNone(r.memory)
                self.assertLess(r.scan.sampled_until_s,.02)

    def test_active_negative_entry_can_cross_zero_without_a_fake_reset(self):
        for phase in (1,2,3):
            m=self.memory(phase); i=list(m.last_event.current_a); i[phase-1]=-.001
            m=replace(m,last_event=replace(m.last_event,current_a=tuple(i)))
            r=self.run_on(m)
            with self.subTest(phase=phase):
                self.assertEqual(r.status,f"CONDITIONAL_M{5*(phase-1)+2}_ENTRY",r.reason)
                self.assertGreater(r.memory.last_event.current_a[phase-1],0.)
                self.assertEqual(m.last_event.current_a[phase-1],-.001)

    def test_negative_current_at_off_is_not_forced_into_down_comm(self):
        m=self.memory(2)
        m=replace(m,last_event=replace(m.last_event,current_a=(20.,-10.,20.)))
        r=self.run_on(m)
        self.assertEqual(r.status,"HIGH_OFF_EVENT_REJECTED")
        self.assertIn("current-sign domain",r.reason)
        self.assertIsNone(r.memory)

    def test_exact_entry_boundary_is_not_skipped(self):
        m=self.memory(1)
        m=replace(m,last_event=replace(m.last_event,voltage_v=(12.,4.,0.,0.,0.,1.)))
        r=self.run_on(m)
        self.assertEqual(r.status,"HIGH_ON_ENTRY_UNRESOLVED")
        self.assertIn("reverse.SL1",r.scan.candidates)
        self.assertEqual(r.scan.sampled_until_s,0.)

    def test_cannot_restart_partway_and_omit_prior_event_history(self):
        m=self.memory(1)
        with self.assertRaises(ValueError):
            self.run_on(replace(m,last_event=replace(m.last_event,time_s=.001)))
        with self.assertRaises(ValueError):
            self.run_on(replace(m,stage=Stage.DOWN_COMM))


if __name__=="__main__":unittest.main()
