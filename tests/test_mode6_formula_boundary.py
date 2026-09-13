import unittest

from pathlib import Path


class Mode6FormulaBoundaryTests(unittest.TestCase):
    def test_netlist_keeps_physical_and_printed_equation_branches(self):
        path = Path(__file__).resolve().parents[1] / "paper_locked/03_apec2025_auxiliary/spice/R04D6A_P25_native_mode6_physical_circuit.cir"
        text = path.read_text()
        self.assertIn("Vrail2-Vo = 4 V-1 V = 3 V", text)
        self.assertIn("EQ15_DELTA_I", text)
        self.assertIn("P24_EQ2_REFERENCE_PEAK", text)


if __name__ == "__main__":
    unittest.main()
