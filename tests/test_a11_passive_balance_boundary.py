import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
A11 = PROJECT / (
    "experiments/track_A_periodic_steady_state/A11_passive_balance_isolated/"
    "A11_passive_balance_control_vs_C1_plus_0p5V.cir"
)
BOUNDARY = A11.with_name("BOUNDARY.md")
RESULTS = A11.with_name("RESULTS.md")


class A11PassiveBalanceBoundaryTests(unittest.TestCase):
    def test_symmetric_perturbations_share_one_netlist(self):
        text = A11.read_text()
        self.assertIn(".step param DV1 list -.5 0 .5", text)
        self.assertIn("ic={36+DV1}", text)

    def test_isolation_fixture_and_p24_threshold_are_explicit(self):
        text = A11.read_text()
        self.assertIn("GS61008T_commutation_capacitance.lib", text)
        self.assertRegex(text, r"(?i)NEG_FRAC\s*=\s*\.02")
        self.assertNotRegex(text, r"(?i)NEG_FRAC\s*=\s*\.0?[5-9]")
        self.assertRegex(text, r"(?m)^VOUT_BOUNDARY\s+out\s+0\s+\{VO\}\s*$")

    def test_documentation_does_not_overclaim(self):
        boundary = BOUNDARY.read_text()
        results = RESULTS.read_text()
        self.assertIn("not retained in the main reproduction", boundary)
        self.assertIn("does **not** establish convergence", results)
        self.assertIn("does not claim natural startup from zero", results)


if __name__ == "__main__":
    unittest.main()
