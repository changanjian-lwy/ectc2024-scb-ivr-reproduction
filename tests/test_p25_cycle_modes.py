"""D15 synthetic per-mode checks, NOT an assembled full-period trajectory."""
import unittest
import numpy as np
from scb_ivr.p25_cycle_modes import cycle_mode,SLOTS
from scb_ivr.p25_native_events import MODES,NativeBoundary
from scb_ivr.p25_control_memory import Stage,gate_pattern
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import LocalFlow,ConstantPorts
from scb_ivr.p25_nodal_contract import Components,instantaneous_rates,ENDS


class CycleModeTests(unittest.TestCase):
    def test_first_six_match_original_table(self):
        for m in MODES:
            if "OPTIONAL" not in m.name: self.assertEqual(cycle_mode(m.name).gates,m.gates)

    def test_all_fifteen_match_existing_controller_indices(self):
        stages=(Stage.RISE,Stage.DOWN_COMM,Stage.ALL_LOW,Stage.NEGATIVE,Stage.UP_COMM)
        for j in range(15):
            m=cycle_mode(f"M{j+1}")
            self.assertEqual(m.gates,gate_pattern(j//5+1,stages[j%5]))
        self.assertEqual(cycle_mode("M15").exit_event,"SH1_zero_voltage_admission")
        self.assertEqual(cycle_mode("M13").exit_event,"iL1_downward_zero")

    def test_unknown_fourth_phase_modes_rejected(self):
        for name in ("M16","M20","M2_PRIME_OPTIONAL","M0","M01"):
            with self.assertRaises(ValueError): cycle_mode(name)

    def test_all_modes_same_node_network_kcl_energy_and_flow(self):
        parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"synthetic")
        boundary=NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05)
        original=ENDS
        for index in range(1,16):
            m=cycle_mode(f"M{index}");v=[8.,4.,0.,0.,0.,1.]
            if m.slot=="high_on":
                v={1:[12.,4.,4.,0.,0.,1.],2:[8.,8.,0.,4.,0.,1.],3:[8.,4.,0.,0.,4.,1.]}[m.phase]
            elif m.slot=="down_comm":v[1+m.phase]=2.
            elif m.slot=="up_comm":v[1+m.next_phase]=1.
            s=Snapshot(boundary,"synthetic","clock",0,0.,12.,tuple(v),(2.,3.,4.),m.gates)
            with self.subTest(mode=m.name):
                r=instantaneous_rates(boundary,parts,m.name,voltage_v=v,current_a=s.current_a,vin_v=12.,dvin_v_s=0.,
                    load_current_a=1.,other_modules_current_a=0.,constraint_tolerance_v=1e-9,
                    reverse_path_regime="off_reverse_channels_excluded_until_admission")
                np.testing.assert_allclose(r.kcl_residual_a,0.,atol=1e-12)
                self.assertAlmostEqual(r.energy_rate_w,r.supplied_minus_dissipated_w,places=11)
                f=LocalFlow(s,parts,m.name,ConstantPorts(1.,0.,"synthetic"),voltage_tolerance_v=1e-9)
                np.testing.assert_allclose((f.generator@np.r_[v,s.current_a,1.])[:9],
                    np.r_[r.voltage_rate_v_s,r.current_rate_a_s],atol=1e-12)
                self.assertEqual(f.at(.01).gates,m.gates)
                self.assertEqual(ENDS,original)
                if m.slot=="high_on":
                    # Distinct positions: source, capacitor difference, last capacitor.
                    k=m.phase-1
                    self.assertAlmostEqual(r.current_rate_a_s[k],(4.-1.)/parts.inductance_h[k])


if __name__=="__main__":unittest.main()
