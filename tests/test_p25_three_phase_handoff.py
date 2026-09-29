"""D17 synthetic per-handoff tests; no stitched full-cycle claim."""
from dataclasses import replace
import unittest
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_control_memory import Policy, Memory, Stage, KnownPeak
from scb_ivr.p25_entry_direction import DirectionTolerance
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary, PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances
from scb_ivr.p25_root_location import RootSettings
from scb_ivr.p25_handoff import enter_all_low, reach_next_current_zero, reach_second_current_zero
from scb_ivr.p25_negative_handoff import reach_negative_target, enter_next_high, enter_second_high


class ThreePhaseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic F/H/s")
        self.ports=ConstantPorts(1.,0.,"synthetic constant ports")
        self.policy=Policy((.02,)*3,1e-8,1e-8,1e-9,True,"ideal synthetic")
        self.reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"ideal")
        self.root=RootSettings(1e-9,1e-8,100,"local affine continuation")
        self.direction=DirectionTolerance(1e-8,1e-8,1e-10,1e-10)
        self.common=dict(intervals=200,voltage_root=self.root,current_root=self.root,
                         electrical=Tolerances(1e-8,1e-8,1e-8))

    def fixture(self, phase, offset=3):
        mode=cycle_mode(f"M{5*(phase-1)+offset}")
        v=[8.,4.,0.,0.,0.,1.]; currents=[20.,20.,20.]
        if offset==2:
            v[1+phase]=2.
            stage=Stage.DOWN_COMM
        else:
            currents[mode.next_phase-1]=.5
            stage=Stage.ALL_LOW
        s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
            "synthetic handoff","clock",7,0.,12.,tuple(v),tuple(currents),mode.gates)
        peaks=tuple(KnownPeak(PeakReference(k,20.,"declared_design_peak","synthetic not measured"),0.)
                    for k in (1,2,3))
        return Memory(phase,stage,0.,s,peaks,None)

    def invoke(self, fn, memory, **kwargs):
        return fn(memory,self.parts,self.ports,self.policy,self.reverse,
                  end_s=memory.last_event.time_s+10.,**self.common,**kwargs)

    def assert_continuous(self, before, after, mode):
        expected=LocalFlow(before.last_event,self.parts,mode,self.ports,
                           voltage_tolerance_v=1e-8).at(after.last_event.time_s)
        self.assertEqual(expected.voltage_v,after.last_event.voltage_v)
        self.assertEqual(expected.current_a,after.last_event.current_a)
        self.assertEqual(expected.vin_v,after.last_event.vin_v)
        self.assertEqual(expected.boundary,after.last_event.boundary)
        self.assertEqual(expected.run_id,after.last_event.run_id)
        self.assertEqual(expected.clock_id,after.last_event.clock_id)

    def test_each_low_admission_preserves_full_state_and_phase(self):
        for phase in (1,2,3):
            with self.subTest(phase=phase):
                m=self.fixture(phase,2)
                r=self.invoke(enter_all_low,m,direction=self.direction)
                self.assertEqual(r.status,f"CONDITIONAL_M{5*(phase-1)+3}_ENTRY",r.reason)
                self.assertEqual(r.memory.phase,phase)
                self.assertEqual(r.memory.last_event.cycle,7)
                self.assert_continuous(m,r.memory,f"M{5*(phase-1)+2}")

    def test_each_all_low_to_next_high_preserves_states_and_wrap(self):
        for phase in (1,2,3):
            with self.subTest(phase=phase):
                m=self.fixture(phase); q=phase%3+1
                r=self.invoke(reach_next_current_zero,m)
                self.assertEqual(r.status,f"CONDITIONAL_M{5*(phase-1)+4}_ENTRY",r.reason)
                self.assert_continuous(m,r.memory,f"M{5*(phase-1)+3}")
                self.assertEqual(r.memory.latched_target_a,-1.)
                m=r.memory
                r=self.invoke(reach_negative_target,m,current_rate_tolerance_a_s=1e-10)
                self.assertEqual(r.status,f"CONDITIONAL_M{5*phase}_ENTRY",r.reason)
                self.assert_continuous(m,r.memory,f"M{5*(phase-1)+4}")
                self.assertFalse(r.memory.last_event.gates.low[q-1])
                m=r.memory
                r=self.invoke(enter_next_high,m,direction=self.direction)
                self.assertEqual(r.status,f"CONDITIONAL_M{5*(q-1)+1}_ENTRY",r.reason)
                self.assert_continuous(m,r.memory,f"M{5*phase}")
                self.assertEqual(r.memory.phase,q)
                self.assertEqual(r.memory.last_event.cycle,7+int(phase==3))
                self.assertLess(r.memory.last_event.current_a[q-1],0.)
                self.assertIsNone(r.memory.latched_target_a)

    def test_missing_next_phase_peak_is_not_borrowed(self):
        for phase in (1,2,3):
            m=self.fixture(phase); q=phase%3
            peaks=list(m.peaks); peaks[q]=None
            r=self.invoke(reach_next_current_zero,replace(m,peaks=tuple(peaks)))
            with self.subTest(phase=phase):
                self.assertEqual(r.status,f"M{5*(phase-1)+3}_CONTROL_REJECTED")
                self.assertIn(f"phase {q+1} causal peak",r.reason)
                self.assertIsNone(r.memory)

    def test_other_phase_zero_stops_each_all_low_interval(self):
        for phase in (1,2,3):
            m=self.fixture(phase)
            currents=list(m.last_event.current_a); currents[phase-1]=.001
            m=replace(m,last_event=replace(m.last_event,current_a=tuple(currents)))
            r=self.invoke(reach_next_current_zero,m)
            with self.subTest(phase=phase):
                self.assertEqual(r.status,f"OTHER_M{5*(phase-1)+3}_BOUNDARY_FIRST_OR_OVERLAP")
                self.assertEqual(r.scan.candidates,(f"domain.iL{phase}",))
                self.assertIsNone(r.memory)

    def test_legacy_names_cannot_silently_mean_another_phase(self):
        for phase in (2,3):
            for fn in (reach_second_current_zero,enter_second_high):
                with self.assertRaises(ValueError):
                    fn(self.fixture(phase))


if __name__=="__main__": unittest.main()
