import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PeriodicShootingRecordTests(unittest.TestCase):
    def test_a10_has_all_eight_state_seeds(self):
        netlist = (ROOT / (
            "experiments/track_A_periodic_steady_state/"
            "A10_eight_state_shooting_iteration_1/"
            "A10_eight_state_shooting_iteration_1.cir"
        )).read_text()
        for token in ("VC1_INIT", "VC2_INIT", "VC3_INIT", "VO_INIT",
                      "IL1_INIT", "IL2_INIT", "IL3_INIT", "IL4_INIT"):
            self.assertIn(token, netlist)

    def test_record_does_not_claim_false_balance_or_zvs(self):
        record = (ROOT / (
            "experiments/track_A_periodic_steady_state/"
            "PERIODIC_SHOOTING_RESULTS_A06_A10.md"
        )).read_text()
        record_lower = " ".join(record.lower().split())
        self.assertIn("output state is not closed", record_lower)
        self.assertIn("8% release event is not reached", record_lower)


if __name__ == "__main__":
    unittest.main()
