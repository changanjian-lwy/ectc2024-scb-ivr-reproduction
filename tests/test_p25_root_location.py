"""Analytic artificial callbacks; these are not SCB trajectories."""
from dataclasses import replace
import unittest

from scb_ivr.p25_native_events import NativeBoundary, GateState
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_root_location import (
    Quantity, RootSettings, EventWindow, locate_downward, order_windows, trace_key,
    ideal_gate_reverse_batch,
)
from scb_ivr.p25_control_memory import Memory, Policy, Stage, Trigger, gate_pattern
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances


class RootLocationTests(unittest.TestCase):
    def setUp(self):
        self.template = Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
                                 "synthetic","absolute",0,0.,12.,(8.,4.,0.,1.,0.,1.),
                                 (1.,-.5,1.),GateState((False,)*3,(True,False,True)))
        self.settings = RootSettings(1e-8,1e-8,100,"analytic continuous test function; not a circuit solution")
        self.quantity = Quantity("SH2_zero","V",lambda s:s.switch_voltage("SH2"))

    def path(self,t):
        return replace(self.template,time_s=t,voltage_v=(8.,4.+t,0.,1.,0.,1.))

    def root(self, **kwargs):
        args=dict(left_s=0.,right_s=8.,settings=self.settings)
        args.update(kwargs)
        return locate_downward(self.quantity,self.path,**args)

    def window(self,name,a,b):
        return EventWindow(name,a,b,trace_key(self.template),"synthetic time interval")

    def test_analytic_root_and_both_tolerances(self):
        r=self.root()
        self.assertEqual(r.status,"NUMERICAL_ROOT_ONLY")
        self.assertLessEqual(r.left.time_s,4.)
        self.assertGreaterEqual(r.right.time_s,4.)
        self.assertLessEqual(r.right.time_s-r.left.time_s,1e-8)
        self.assertLessEqual(abs(r.right_value),1e-8)
        self.assertGreater(r.left_value,0.)
        self.assertLessEqual(r.right_value,0.)

    def test_state_is_not_projected_to_zero(self):
        settings=RootSettings(.01,.01,100,"synthetic analytic continuation")
        r=self.root(right_s=7.,settings=settings)
        self.assertEqual(r.right,self.path(r.right.time_s))
        self.assertNotEqual(r.right_value,0.)

    def test_jump_is_not_accepted_merely_because_time_bracket_is_small(self):
        q=Quantity("jump","A",lambda s:1. if s.time_s<4 else -1.)
        with self.assertRaises(RuntimeError):
            locate_downward(q,self.path,left_s=0.,right_s=8.,settings=self.settings)

    def test_start_on_root_requires_separate_arming(self):
        with self.assertRaisesRegex(ValueError,"root-at-start"):
            self.root(left_s=4.)

    def test_missing_crossing_is_not_created_by_clock(self):
        with self.assertRaisesRegex(ValueError,"bracket"):
            self.root(right_s=3.)

    def test_changed_gate_during_trial_rejected(self):
        def wrong(t):
            s=self.path(t)
            return replace(s,gates=GateState((False,True,False),(True,False,True))) if t>2 else s
        with self.assertRaisesRegex(ValueError,"changed"):
            locate_downward(self.quantity,wrong,left_s=0.,right_s=8.,settings=self.settings)

    def test_wrong_callback_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,"requested time"):
            locate_downward(self.quantity,lambda t:self.path(t+1),left_s=0.,right_s=8.,settings=self.settings)

    def test_iteration_limit_is_not_false_success(self):
        with self.assertRaisesRegex(RuntimeError,"iteration limit"):
            self.root(settings=replace(self.settings,max_iterations=1))

    def test_numerical_root_window_preserves_trace_identity(self):
        w=EventWindow.from_root(self.root())
        self.assertEqual(w.trace,trace_key(self.template))

    def test_separate_windows_have_order_independent_of_input_listing(self):
        a,b=self.window("controller",1,2),self.window("domain_exit",3,4)
        self.assertEqual(order_windows((a,b)),order_windows((b,a)))
        self.assertEqual(order_windows((a,b)).possible_first,("controller",))

    def test_overlapping_roots_are_not_sorted_by_midpoint(self):
        r=order_windows((self.window("gate",1,3),self.window("reverse",2,4)))
        self.assertEqual(r.status,"OVERLAP_REFINE_OR_DECLARE_UNRESOLVED")
        self.assertEqual(r.possible_first,("gate","reverse"))

    def test_exact_coincidence_does_not_choose_gate_priority(self):
        r=order_windows((self.window("gate",2,2),self.window("reverse",2,2)))
        self.assertEqual(r.status,"EXACT_COINCIDENCE_REQUIRES_RESET_RULE")

    def test_physically_earlier_domain_exit_not_ignored(self):
        r=order_windows((self.window("desired_gate",4,5),self.window("other_phase_zero",1,2)))
        self.assertEqual(r.possible_first,("other_phase_zero",))

    def test_touching_intervals_are_not_claimed_strictly_ordered(self):
        r=order_windows((self.window("a",1,2),self.window("b",2,3)))
        self.assertEqual(len(r.possible_first),2)

    def test_empty_duplicate_and_mixed_run_windows_rejected(self):
        a=self.window("a",1,2)
        for values in ((),(a,a),(a,replace(self.window("b",3,4),trace=("other_run",)))):
            with self.assertRaises(ValueError): order_windows(values)

    def batch_fixture(self, high):
        stage=Stage.UP_COMM if high else Stage.DOWN_COMM
        lv=(8.,7.,0.,2.,0.,1.) if high else (8.,4.,1.,0.,0.,1.)
        rv=(8.,8.,0.,2.,0.,1.) if high else (8.,4.,0.,0.,0.,1.)
        current=(2.,-.5,1.) if high else (2.,1.,1.)
        left=replace(self.template,gates=gate_pattern(1,stage),voltage_v=lv,current_a=current)
        at=replace(left,time_s=1.,voltage_v=rv)
        memory=Memory(1,stage,0.,left,(None,)*3,-.5 if high else None)
        params=dict(left=left,policy=Policy((2.,)*3,1e-12,1e-12,1e-12,True,"synthetic ideal"),
                    parts=Components((2.,3.,5.,7.,11.,13.),(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic"),
                    reverse_model=ReverseModel("ideal_zero_drop",(0.,)*6,"synthetic explicit ideal branch"),
                    dvin_v_s=0.,load_current_a=2.,other_modules_current_a=0.,tolerances=Tolerances(1e-12,1e-12,1e-12))
        return memory,at,params

    def test_low_zero_reverse_and_gate_batch_preserves_state(self):
        m,at,params=self.batch_fixture(False)
        after,before,post=ideal_gate_reverse_batch(m,Trigger.LOW_ZERO,at,**params)
        self.assertEqual(after.stage,Stage.ALL_LOW)
        self.assertEqual(after.last_event.voltage_v,at.voltage_v)
        self.assertEqual(after.last_event.current_a,at.current_a)
        self.assertGreater(before.candidates[0].reverse_current_a[3],0.)
        self.assertEqual(post.candidates[0].reverse_current_a[3],0.)
        self.assertLess(post.candidates[0].gate_current_a[3],0.)

    def test_high_zero_batch_preserves_negative_entry_current(self):
        m,at,params=self.batch_fixture(True)
        after,_,_=ideal_gate_reverse_batch(m,Trigger.NEXT_HIGH_ZERO,at,**params)
        self.assertEqual(after.phase,2)
        self.assertEqual(after.stage,Stage.RISE)
        self.assertEqual(after.last_event.current_a[1],-.5)

    def test_unmodelled_simultaneous_actions_or_real_drop_not_assumed(self):
        m,at,params=self.batch_fixture(False)
        with self.assertRaises(ValueError):
            ideal_gate_reverse_batch(m,Trigger.NEXT_CURRENT_ZERO,at,**params)
        params["reverse_model"]=ReverseModel("constant_drop_surrogate",(.1,)*6,"synthetic")
        with self.assertRaisesRegex(ValueError,"zero-drop"):
            ideal_gate_reverse_batch(m,Trigger.LOW_ZERO,at,**params)
