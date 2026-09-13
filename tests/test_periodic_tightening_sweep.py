import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
TRACK = PROJECT / "experiments/track_A_periodic_steady_state"


class PeriodicTighteningSweepTests(unittest.TestCase):
    def test_each_update_has_a_separate_boundary_folder(self):
        folders = (
            "A13_tighten_01_inductor_currents",
            "A14_tighten_02_C1",
            "A15_tighten_03_C2",
            "A16_tighten_04_C3",
        )
        for folder in folders:
            path = TRACK / folder
            self.assertTrue((path / "BOUNDARY.md").is_file(), folder)
            self.assertTrue((path / "RESULTS.md").is_file(), folder)
            self.assertEqual(len(list(path.glob("*.cir"))), 1, folder)

    def test_locked_electrical_boundaries_survive_all_steps(self):
        for index in range(13, 17):
            netlist = next((TRACK.glob(f"A{index}_*/*cir")))
            text = netlist.read_text()
            self.assertRegex(text, r"(?i)NEG_FRAC\s*=\s*\.02")
            self.assertIn("FSW=5Meg", text)
            self.assertIn("VOUT_BOUNDARY out 0 {VO}", text)
            self.assertIn("GS61008T_commutation_capacitance.lib", text)
            self.assertIn(".tran 0 {T0+T+5n} 0 5p UIC", text)

    def test_summary_preserves_scope(self):
        summary = (TRACK / "PERIODIC_TIGHTENING_SWEEP_1_A13_A16.md").read_text()
        self.assertIn("one state group is updated per folder", summary.lower())
        self.assertIn("does not demonstrate output regulation", summary)


if __name__ == "__main__":
    unittest.main()
