import unittest
from pathlib import Path


NETLIST = (
    Path(__file__).resolve().parents[1]
    / "experiments/track_A_periodic_steady_state/A04_four_phase_readiness_supervisor/"
    "A04_four_phase_readiness_supervisor_2pct.cir"
)


class A04ReadinessSupervisorTests(unittest.TestCase):
    def test_release_uses_adjacent_differences_not_absolute_nodes(self):
        text = NETLIST.read_text()
        self.assertIn("V(xmod:a1,xmod:a2)>=VSEG_LO", text)
        self.assertIn("V(xmod:a2,xmod:a3)>=VSEG_LO", text)
        self.assertIn("V(xmod:a3,xmod:x4)>=VSEG_LO", text)
        self.assertNotIn("V(xmod:a2)>=", text)

    def test_controller_is_latched_and_has_explicit_gate_ports(self):
        text = NETLIST.read_text()
        self.assertIn(".state WAIT_P2", text)
        self.assertIn(".state P2_ON", text)
        self.assertIn("gh2_cmd gh3_cmd gh4_cmd SCB4P_PERIODIC_SEED", text)
        self.assertIn("BGH2 gh2 g V=V(gh2_in,g)", text)

    def test_p24_threshold_remains_separate(self):
        text = NETLIST.read_text()
        self.assertIn("NEG_FRAC=.02", text)
        self.assertIn("GS61008T_commutation_capacitance.lib", text)


if __name__ == "__main__":
    unittest.main()
