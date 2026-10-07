"""D76 core loss: the digitised HBS1 R_acx table, its interpolation and the phase loss."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scb_ivr import p24_core_loss as C  # noqa: E402


class CoreLoss(unittest.TestCase):
    def test_table_points_and_power_law(self):
        for f, vals in C.RACX_HBS1.items():
            for d, v in zip(C.RACX_D, vals):
                self.assertAlmostEqual(C.racx(f, d), v * 1e6, delta=1e-6 * v * 1e6)
        self.assertTrue(1.45 < C.exponent(0.077) < 1.6)
        mid = C.racx(2.5e6, 0.077)
        self.assertTrue(C.racx(2e6, 0.077) < mid < C.racx(4e6, 0.077))

    def test_smaller_duty_is_lossier(self):
        self.assertGreater(C.racx(2.5e6, 0.05), C.racx(2.5e6, 0.1))

    def test_phase_loss(self):
        # 2.5 MHz design numbers: triangle -15.6 -> 144 A, 38.6 ns in 505 ns, 2.933 nH
        p1 = C.phase_core_loss(-15.6, 144.0, 38.6e-9, 505e-9, 2.933e-9, 1.0)
        exact = C.racx(1 / 505e-9, 38.6 / 505) * 2.933e-9 * (159.6 ** 2 / 12)
        self.assertAlmostEqual(p1, exact, places=12)
        self.assertAlmostEqual(C.phase_core_loss(-15.6, 144.0, 38.6e-9, 505e-9, 2.933e-9, 4.0), 4 * p1, places=12)
        self.assertTrue(1.5 < p1 < 2.5)


if __name__ == "__main__":
    unittest.main()
