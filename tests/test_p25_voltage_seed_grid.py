"""D36: bounded initial-voltage diagnostic, not component optimization."""
import unittest
from scripts.audit_p25_voltage_seed_grid import run_voltage_grid


class VoltageSeedGridTests(unittest.TestCase):
    def test_only_two_initial_coordinates_vary(self):
        r = run_voltage_grid()
        self.assertEqual(len(r["cases"]),6)
        self.assertEqual({c["seed"]["x1_v"] for c in r["cases"]},{2.,3.,4.})
        self.assertEqual({c["seed"]["out_v"] for c in r["cases"]},{.5,1.})
        for c in r["cases"]:
            self.assertEqual(c["seed"]["a2_v"],4.)
            self.assertEqual(c["seed"]["current_a"],(-.0025,2.,3.))

    def test_later_failure_is_not_periodicity(self):
        rows = run_voltage_grid()["cases"]
        self.assertEqual([c["failed_mode"] for c in rows],["M2","M2","M2","M2","M4","M5"])
        self.assertEqual(rows[-1]["accepted_modes"],["M1","M2","M3","M4"])
        for c in rows:
            self.assertIsNone(c["state_return"])
            self.assertEqual(len(c["last_accepted"]["inductor_current_a"]),3)
            self.assertAlmostEqual(c["m2_charge"]["voltage_balance_residual_v"],0.,places=11)

    def test_frozen_model_and_event_windows_survive_grid_refinement(self):
        a,b = run_voltage_grid(200),run_voltage_grid(400)
        self.assertEqual(a["frozen_model"],b["frozen_model"])
        self.assertEqual(a["frozen_ports"],b["frozen_ports"])
        for x,y in zip(a["cases"],b["cases"]):
            self.assertEqual((x["failed_mode"],x["events"]),(y["failed_mode"],y["events"]))
            self.assertLess(abs(x["event_windows"][0]["latest_s"]-y["event_windows"][0]["latest_s"]),2e-9)


if __name__ == "__main__":
    unittest.main()
