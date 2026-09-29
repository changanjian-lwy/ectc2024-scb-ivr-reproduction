"""D16: synthetic guard coverage, not connected-cycle or paper reproduction."""
from dataclasses import replace
import unittest

from scb_ivr.p25_cycle_modes import cycle_mode, current_signs, commutation_target
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_native_events import NativeBoundary
from scb_ivr.p25_nodal_contract import Components, SWITCHES
from scb_ivr.p25_local_flow import LocalFlow, ConstantPorts, scan_commutation
from scb_ivr.p25_entry_direction import classify_entry, DirectionTolerance
from scb_ivr.p25_reverse_contract import ReverseModel, paper_mode_violations
from scb_ivr.p25_root_location import RootSettings


class CommutationCycleTests(unittest.TestCase):
    def setUp(self):
        self.parts = Components((1.,)*6, (0.,)*6, (17.,19.),23.,
                                (2.,3.,4.),(0.,)*3,"synthetic F/H/s fixture")
        self.ports = ConstantPorts(1.,0.,"synthetic constant ports")
        self.reverse = ReverseModel("ideal_zero_drop",(0.,)*6,"ideal mathematical boundary")
        self.settings = RootSettings(1e-9,1e-8,100,"conditional sampled screening")
        self.direction = DirectionTolerance(1e-8,1e-8,1e-8,1e-8)
        self.expected = {"M2":"SL1","M7":"SL2","M12":"SL3",
                         "M5":"SH2","M10":"SH3","M15":"SH1"}

    def state(self, name):
        mode = cycle_mode(name)
        v = [8.,4.,0.,0.,0.,1.]
        currents = [20.,20.,20.]
        if mode.slot == "down_comm":
            v[1+mode.phase] = 2.
        else:
            v[1+mode.next_phase] = 1.
            currents[mode.next_phase-1] = -10.
        return Snapshot(NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05),
                        "synthetic","absolute",0,0.,12.,tuple(v),tuple(currents),mode.gates)

    def flow(self, name, state=None):
        return LocalFlow(state or self.state(name),self.parts,name,self.ports,
                         voltage_tolerance_v=1e-8)

    def scan(self, flow):
        return scan_commutation(flow,self.reverse,end_s=.1,intervals=50,
                                voltage_settings=self.settings,current_settings=self.settings,
                                entry_direction=self.direction)

    def test_six_targets_are_explicit_physical_switches(self):
        for name, target in self.expected.items():
            self.assertEqual(commutation_target(name),target)
        for name in ("M1","M3","M4","M6","M11","M16"):
            with self.assertRaises(ValueError):
                commutation_target(name)

    def test_classification_watches_all_off_switches_and_all_currents(self):
        for name,target in self.expected.items():
            with self.subTest(mode=name):
                flow = self.flow(name)
                report = classify_entry(flow,self.reverse,self.direction)
                expected = {"target."+target, "domain.iL1","domain.iL2","domain.iL3"}
                expected.update("reverse."+s for s,on in zip(SWITCHES,
                                (*flow.start.gates.high,*flow.start.gates.low)) if not on)
                self.assertEqual({item.name for item in report.items},expected)
                self.assertEqual(report.blockers,())
                self.assertEqual(paper_mode_violations(flow.start,name,tolerance_a=1e-8),())

    def test_other_phase_zero_stops_each_commutation(self):
        for name in self.expected:
            mode = cycle_mode(name)
            # Choose a positive-current phase with its low switch ON.
            k = (mode.phase if mode.slot=="down_comm" else mode.next_phase) % 3
            s = self.state(name)
            currents = list(s.current_a); currents[k] = .001
            result = self.scan(self.flow(name,replace(s,current_a=tuple(currents))))
            with self.subTest(mode=name):
                self.assertEqual(result.candidates,(f"domain.iL{k+1}",))
                self.assertIn("CONDITIONAL",result.scope)

    def test_wrong_negative_phase_is_rejected_not_rotated(self):
        for name in ("M5","M10","M15"):
            s=self.state(name); q=cycle_mode(name).next_phase-1
            wrong=(q+1)%3
            currents=[20.,20.,20.]; currents[wrong]=-10.
            bad=replace(s,current_a=tuple(currents))
            with self.subTest(mode=name):
                self.assertEqual(set(paper_mode_violations(bad,name,tolerance_a=1e-8)),
                                 {f"iL{q+1}_SIGN",f"iL{wrong+1}_SIGN"})
                result=self.scan(self.flow(name,bad))
                self.assertEqual(result.status,"ENTRY_DIRECTION_BLOCKED")

    def test_zero_target_requires_event_action_no_epsilon(self):
        for name,target in self.expected.items():
            s=self.state(name); v=list(s.voltage_v)
            if target.startswith("SL"):
                v[1+int(target[-1])]=0.
            elif target=="SH1":
                v[0]=s.vin_v
            elif target=="SH2":
                v[0]=v[1]
            else:
                v[4]=v[1]
            start=replace(s,voltage_v=tuple(v))
            flow=self.flow(name,start)
            result=self.scan(flow)
            with self.subTest(mode=name):
                self.assertIn("target."+target,result.candidates)
                self.assertEqual(result.sampled_until_s,start.time_s)
                self.assertEqual(flow.at(start.time_s),start)

    def test_sign_contract_full_cycle_and_legacy_prime_aliases(self):
        expected=((0,1,1),(1,1,1),(1,1,1),(1,-1,1),(1,-1,1),
                  (1,0,1),(1,1,1),(1,1,1),(1,1,-1),(1,1,-1),
                  (1,1,0),(1,1,1),(1,1,1),(-1,1,1),(-1,1,1))
        for k, signs in enumerate(expected,1):
            self.assertEqual(current_signs(f"M{k}"),signs)
        for name in ("M2","M5"):
            s=self.state(name)
            self.assertEqual(paper_mode_violations(s,name,tolerance_a=0.),
                             paper_mode_violations(s,name+"_PRIME_OPTIONAL",tolerance_a=0.))


if __name__ == "__main__":
    unittest.main()
