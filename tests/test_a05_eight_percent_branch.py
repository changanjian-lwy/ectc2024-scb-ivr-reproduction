import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NETLIST = ROOT / (
    "experiments/track_A_periodic_steady_state/A05_four_phase_8pct_branch/"
    "A05_four_phase_readiness_supervisor_8pct.cir"
)


class A05EightPercentBranchTests(unittest.TestCase):
    def test_only_threshold_differs_from_a04_contract(self):
        text = NETLIST.read_text()
        self.assertIn("NEG_FRAC=.08", text)
        self.assertIn("GS61008T_commutation_capacitance.lib", text)
        self.assertIn("V(xmod:a1,xmod:a2)>=VSEG_LO", text)

    def test_result_record_rejects_false_eight_percent_claim(self):
        result = (NETLIST.parent / "RESULTS.md").read_text()
        self.assertIn("did **not exercise the 8% turn-off event**", result)
        self.assertIn("IL1,min = -3.3367 A", result)


if __name__ == "__main__":
    unittest.main()
