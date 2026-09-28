from dataclasses import replace
import unittest

from scb_ivr.p25_control_memory import Memory, Policy, Stage, gate_pattern
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary
from scb_ivr.p25_watch_contract import required_watches, missing_watches


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.policy=Policy((2.,)*3,1e-9,1e-9,1e-9,True,"synthetic")
        s=Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),"synthetic","absolute",0,0.,12.,
                   (8.,8.,0.,2.,0.,1.),(1.,-.5,1.),gate_pattern(1,Stage.UP_COMM))
        self.memory=Memory(1,Stage.UP_COMM,0.,s,(None,)*3,-.5)

    def plan(self,**kw):
        args=dict(reverse_active=(),external_event_names=(),port_event_declaration="synthetic time-invariant external law")
        args.update(kw)
        return required_watches(self.memory,self.policy,**args)

    def test_all_off_devices_and_other_phases_are_watched(self):
        names={w.name for w in self.plan().watches}
        self.assertTrue({"reverse.SH1.entry","reverse.SH2.entry","reverse.SH3.entry","reverse.SL2.entry",
                         "mode.iL1.boundary","mode.iL2.boundary","mode.iL3.boundary"} <= names)
        self.assertNotIn("reverse.SL1.entry",names)

    def test_active_reverse_path_watches_release_not_permanent_zero(self):
        names={w.name for w in self.plan(reverse_active=("SH2",)).watches}
        self.assertIn("reverse.SH2.release",names)
        self.assertNotIn("reverse.SH2.entry",names)

    def test_omitted_other_phase_event_detected(self):
        plan=self.plan()
        installed=tuple(w.name for w in plan.watches if w.name!="mode.iL3.boundary")
        self.assertEqual(missing_watches(plan,installed),("mode.iL3.boundary",))

    def test_phase3_next_event_is_phase1_without_rewiring_topology(self):
        self.memory=replace(self.memory,phase=3,last_event=replace(self.memory.last_event,gates=gate_pattern(3,Stage.UP_COMM)))
        self.assertEqual(self.plan().watches[0].expression,"Vds(SH1)")

    def test_input_breakpoint_not_omitted(self):
        plan=self.plan(external_event_names=("vin_ramp_end",))
        self.assertIn("external.vin_ramp_end",{w.name for w in plan.watches})

    def test_on_reverse_overlap_and_missing_port_declaration_rejected(self):
        with self.assertRaises(ValueError):self.plan(reverse_active=("SL1",))
        with self.assertRaises(ValueError):self.plan(port_event_declaration="")

    def test_gate_algebra_is_not_a_zero_root_watch(self):
        self.assertIn("gate_voltage_constraints",self.plan().algebraic_checks)
        self.assertFalse(any("reverse.SL1" in w.name for w in self.plan().watches))

    def test_negative_target_cannot_be_guessed(self):
        self.memory=replace(self.memory,stage=Stage.NEGATIVE,latched_target_a=None,
                            last_event=replace(self.memory.last_event,gates=gate_pattern(1,Stage.NEGATIVE)))
        with self.assertRaisesRegex(ValueError,"missing latched"):
            self.plan()
