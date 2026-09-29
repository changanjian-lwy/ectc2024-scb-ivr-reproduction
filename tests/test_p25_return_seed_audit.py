"""D34: distinguish finite search horizon from competing-event failure."""
import unittest
from scripts.audit_p25_return_seeds import run_return_audit


class ReturnSeedAuditTests(unittest.TestCase):
    def test_direction_and_on_time_rejection_are_distinct(self):
        rows = run_return_audit()["cases"]
        self.assertTrue(all(r["direction"] == "NECESSARY_DIRECTION_PASSED_NOT_SUFFICIENT" for r in rows))
        self.assertTrue(all(r["state_return"] is None for r in rows))
        for r in rows[2:]:
            self.assertEqual(r["last_action"], "HIGH_OFF_EVENT_REJECTED")
            self.assertLess(r["nominal_high_off_i1_continuation_a"], 0.)
            self.assertEqual(r["accepted_modes"], [])

    def test_horizon_exhaustion_is_not_called_physical_event(self):
        short = run_return_audit()["cases"]
        long = run_return_audit(down_horizon_s=10.)["cases"]
        for a,b in zip(short[:2],long[:2]):
            self.assertEqual(a["scan_status"], "NO_DOWNWARD_BRACKET_OBSERVED")
            self.assertEqual(a["events"], ())
            self.assertEqual(b["events"], ("domain.iL2",))
            self.assertEqual(b["accepted_modes"], ["M1"])

    def test_longer_search_classification_survives_grid_refinement(self):
        a = run_return_audit(200,10.)["cases"]
        b = run_return_audit(400,10.)["cases"]
        for x,y in zip(a,b):
            self.assertEqual((x["failed_mode"],x["events"]),(y["failed_mode"],y["events"]))
            self.assertLess(abs(x["windows"][0]["latest_s"]-y["windows"][0]["latest_s"]),2e-9)


if __name__ == "__main__":
    unittest.main()
