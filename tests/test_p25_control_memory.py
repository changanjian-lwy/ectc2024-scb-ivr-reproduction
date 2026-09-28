"""Synthetic event traces; NOT solutions of the electrical trajectory."""
from dataclasses import replace
import unittest

from scb_ivr.p25_control_memory import (
    Policy, KnownPeak, Stage, Trigger, gate_pattern, start_at_high_on,
    transition, update_peak,
)
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary, PeakReference


class ControlMemoryTests(unittest.TestCase):
    def setUp(self):
        self.policy = Policy((2.,2.,2.), 1e-10, 1e-10, 1e-10, True, "synthetic zero-delay controller")
        self.peaks = tuple(KnownPeak(PeakReference(k,10.,"declared_design_peak","synthetic"),0.) for k in (1,2,3))
        self.start = Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
                              "synthetic", "absolute",0,0.,12.,(12.,4.,4.,0.,0.,1.),
                              (-.5,1.,1.),gate_pattern(1,Stage.RISE))
        self.memory = start_at_high_on(self.start, phase=1, peaks=self.peaks, policy=self.policy)

    def point(self, m, time, *, currents=None, voltage=None):
        return replace(m.last_event, time_s=time,
                       current_a=tuple(currents) if currents is not None else m.last_event.current_a,
                       voltage_v=tuple(voltage) if voltage is not None else m.last_event.voltage_v)

    def next_event(self, m):
        t, k, q = m.entered_at_s, m.phase-1, m.phase % 3
        current = [1.,1.,1.]
        if m.stage == Stage.RISE:
            current[k] = 2.
            return transition(m, Trigger.HIGH_OFF_DUE, self.point(m,t+2,currents=current), policy=self.policy)
        if m.stage == Stage.DOWN_COMM:
            v = [8.,4.,0.,0.,0.,1.]
            left_v = v.copy(); left_v[2+k] = .5
            return transition(m, Trigger.LOW_ZERO, self.point(m,t+1,currents=current,voltage=v),
                              left=self.point(m,t+.5,currents=current,voltage=left_v), policy=self.policy)
        if m.stage == Stage.ALL_LOW:
            before=current.copy(); before[q]=.5; current[q]=0.
            return transition(m, Trigger.NEXT_CURRENT_ZERO, self.point(m,t+1,currents=current),
                              left=self.point(m,t+.5,currents=before),policy=self.policy)
        if m.stage == Stage.NEGATIVE:
            before=current.copy(); before[q]=-.2; current[q]=m.latched_target_a
            return transition(m, Trigger.NEGATIVE_TARGET, self.point(m,t+1,currents=current),
                              left=self.point(m,t+.5,currents=before),policy=self.policy)
        current[q]=-.5
        on = {0:[12.,4.,2.,0.,0.,1.],1:[8.,8.,0.,2.,0.,1.],2:[8.,4.,0.,0.,4.,1.]}[q]
        left_v=on.copy()
        left_v[{0:0,1:1,2:4}[q]]-=1.
        return transition(m, Trigger.NEXT_HIGH_ZERO, self.point(m,t+1,currents=current,voltage=on),
                          left=self.point(m,t+.5,currents=current,voltage=left_v),policy=self.policy)

    def at_stage(self, count):
        m=self.memory
        for _ in range(count): m=self.next_event(m)
        return m

    def test_full_three_phase_control_ring_and_cycle_index(self):
        m=self.memory
        high_on_phases=[]
        for _ in range(15):
            m=self.next_event(m)
            if m.stage == Stage.RISE: high_on_phases.append(m.phase)
        self.assertEqual(high_on_phases,[2,3,1])
        self.assertEqual(m.last_event.cycle,1)
        self.assertEqual(m.last_event.time_s,18.)

    def test_electrical_state_unchanged_at_gate_edge(self):
        m=self.at_stage(4)
        at=self.point(m,m.entered_at_s+1,currents=(1.,-.5,1.),voltage=(8.,8.,0.,2.,0.,1.))
        left=self.point(m,m.entered_at_s+.5,currents=(1.,-.5,1.),voltage=(8.,7.,0.,2.,0.,1.))
        result=transition(m,Trigger.NEXT_HIGH_ZERO,at,left=left,policy=self.policy)
        self.assertEqual(result.last_event.voltage_v,at.voltage_v)
        self.assertEqual(result.last_event.current_a,at.current_a)
        self.assertEqual(result.last_event.vin_v,at.vin_v)

    def test_low_gate_stays_latched_until_negative_target(self):
        m=self.at_stage(2)
        self.assertTrue(all(m.last_event.gates.low))
        m=self.next_event(m)
        self.assertTrue(all(m.last_event.gates.low))
        m=self.next_event(m)
        self.assertEqual(m.last_event.gates.low,(True,False,True))

    def test_causal_peak_target_latched_at_current_zero(self):
        m=self.at_stage(3)
        self.assertEqual(m.latched_target_a,-.5)
        observed=self.point(m,m.entered_at_s+.1,currents=(1.,-.1,1.))
        peak=KnownPeak(PeakReference(2,20.,"previous_measured_peak","synthetic external history"),observed.time_s)
        changed=update_peak(m,peak,observed=observed,policy=self.policy)
        self.assertEqual(changed.latched_target_a,-.5)
        self.assertEqual(changed.peaks[1].reference.amperes,20.)

    def test_unknown_peak_blocks_target_creation(self):
        self.memory=start_at_high_on(self.start,phase=1,peaks=(self.peaks[0],None,self.peaks[2]),policy=self.policy)
        with self.assertRaisesRegex(ValueError,"unavailable"):
            self.at_stage(3)

    def test_future_peak_rejected(self):
        with self.assertRaisesRegex(ValueError,"future"):
            start_at_high_on(self.start,phase=1,peaks=(replace(self.peaks[0],available_at_s=1.),*self.peaks[1:]),policy=self.policy)

    def test_high_off_time_is_relative_to_actual_high_on(self):
        shifted=replace(self.start,time_s=10.)
        m=start_at_high_on(shifted,phase=1,peaks=self.peaks,policy=self.policy)
        after=self.next_event(m)
        self.assertEqual(after.last_event.time_s,12.)
        with self.assertRaisesRegex(ValueError,"endpoint"):
            transition(m,Trigger.HIGH_OFF_DUE,self.point(m,11.,currents=(2.,1.,1.)),policy=self.policy)

    def test_duplicate_event_rejected(self):
        m=self.at_stage(1)
        with self.assertRaisesRegex(ValueError,"out of order"):
            transition(m,Trigger.HIGH_OFF_DUE,m.last_event,policy=self.policy)

    def test_timer_cannot_replace_zero_event(self):
        m=self.at_stage(1)
        with self.assertRaisesRegex(ValueError,"witness"):
            transition(m,Trigger.LOW_ZERO,self.point(m,3.,voltage=(8.,4.,0.,0.,0.,1.)),policy=self.policy)

    def test_negative_target_overshoot_rejected(self):
        m=self.at_stage(3)
        with self.assertRaisesRegex(ValueError,"root not located"):
            transition(m,Trigger.NEGATIVE_TARGET,self.point(m,5.,currents=(1.,-2.,1.)),
                       left=self.point(m,4.5,currents=(1.,-.2,1.)),policy=self.policy)

    def test_other_phase_violation_blocks_transition(self):
        m=self.at_stage(3)
        with self.assertRaisesRegex(ValueError,"iL3"):
            transition(m,Trigger.NEGATIVE_TARGET,self.point(m,5.,currents=(1.,-.5,-1.)),
                       left=self.point(m,4.5,currents=(1.,-.2,1.)),policy=self.policy)

    def test_gate_on_cannot_reset_incompatible_capacitor_voltage(self):
        bad=replace(self.start,voltage_v=(11.,4.,4.,0.,0.,1.))
        with self.assertRaisesRegex(ValueError,"incompatible voltage"):
            start_at_high_on(bad,phase=1,peaks=self.peaks,policy=self.policy)

    def test_no_silent_real_driver_or_missing_on_time(self):
        with self.assertRaises(ValueError): replace(self.policy,ideal_zero_delay=False)
        with self.assertRaises(ValueError): replace(self.policy,on_time_s=(2.,2.))
        with self.assertRaisesRegex(ValueError,"separate extension"):
            replace(self.policy,on_time_s=(2.,2.,3.))
