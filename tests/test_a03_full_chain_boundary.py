import unittest
from pathlib import Path


NETLIST = (
    Path(__file__).resolve().parents[1]
    / "experiments/track_A_periodic_steady_state/A03_phase1_full_zvs_chain/"
    "A03_phase1_full_zvs_chain_8pct.cir"
)


class A03FullChainBoundaryTests(unittest.TestCase):
    def test_event_order_is_encoded(self):
        text = NETLIST.read_text()
        expected = (
            "HS1_ENERGY COMMUTATE_TO_LS1 time>TON",
            "COMMUTATE_TO_LS1 LS1_FREEWHEEL V(x1)<0",
            "LS1_FREEWHEEL COMMUTATE_TO_HS1 I(L1)<-INEG",
            "COMMUTATE_TO_HS1 HS1_ZVS_RETURN V(vin,a1)<0",
        )
        for rule in expected:
            self.assertIn(rule, text)

    def test_only_p25_bounded_thresholds_are_swept(self):
        text = NETLIST.read_text()
        self.assertIn(".step param NEG_FRAC list .08 .09 .10", text)

    def test_device_coss_and_zero_snubber_are_shared_inputs(self):
        text = NETLIST.read_text()
        self.assertIn("GS61008T_commutation_capacitance.lib", text)
        self.assertNotIn(".param CH=", text)
        self.assertNotIn(".param CL=", text)


if __name__ == "__main__":
    unittest.main()
