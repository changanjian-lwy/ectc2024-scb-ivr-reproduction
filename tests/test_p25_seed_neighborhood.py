"""D29 fixed synthetic local diagnostic, not global feasibility search."""
import unittest
from scripts.audit_p25_synthetic_seeds import run_audit


class SeedNeighborhoodTests(unittest.TestCase):
    def test_exactly_one_coordinate_changes_in_each_variant(self):
        cases=run_audit()["cases"]
        self.assertEqual(len(cases),13)
        baseline=cases[0]["seed"]
        for case in cases[1:]:
            changes=[(a,b) for a,b in zip(baseline,case["seed"]) if a!=b]
            self.assertEqual(len(changes),1)
            a,b=changes[0]
            self.assertAlmostEqual(abs(b/a-1),.1)

    def test_failure_classification_survives_grid_refinement(self):
        coarse=run_audit(200)["cases"];fine=run_audit(400)["cases"]
        for a,b in zip(coarse,fine):
            self.assertEqual(a["failed_mode"],"M5")
            self.assertEqual(a["events"],("domain.iL3",))
            self.assertEqual((a["case"],a["events"],a["failed_mode"]),(b["case"],b["events"],b["failed_mode"]))
            self.assertIsNone(a["state_return"])
            self.assertLess(abs(a["windows"][0]["latest_s"]-b["windows"][0]["latest_s"]),2e-9)


if __name__=="__main__":unittest.main()
