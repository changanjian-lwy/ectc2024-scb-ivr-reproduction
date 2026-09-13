import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
A12_DIR = PROJECT / "experiments/track_A_periodic_steady_state/A12_passive_balance_long_horizon"
NETLIST = A12_DIR / "A12_passive_balance_symmetric_20cycles.cir"


class A12LongHorizonBoundaryTests(unittest.TestCase):
    def test_only_long_horizon_variant_is_encoded(self):
        text = NETLIST.read_text()
        self.assertIn(".step param DV1 list -.5 0 .5", text)
        self.assertIn(".tran 0 {T0+20*T+5n} 0 5p UIC", text)
        for cycle in (1, 5, 10, 15, 20):
            self.assertIn(f"VC1_C{cycle}", text)

    def test_p24_and_isolation_boundaries_remain_locked(self):
        text = NETLIST.read_text()
        self.assertRegex(text, r"(?i)NEG_FRAC\s*=\s*\.02")
        self.assertRegex(text, r"(?m)^VOUT_BOUNDARY\s+out\s+0\s+\{VO\}\s*$")
        self.assertIn("GS61008T_commutation_capacitance.lib", text)

    def test_result_retains_nonconvergence_qualification(self):
        results = (A12_DIR / "RESULTS.md").read_text()
        self.assertIn("does not prove asymptotic convergence", results)
        self.assertIn("not yet an exact periodic fixed point", results)
        self.assertIn("neither zero-start validation nor output regulation", results)


if __name__ == "__main__":
    unittest.main()
