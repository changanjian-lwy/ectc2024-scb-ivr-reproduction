"""D64 stripline inductor: skin depth, R/L from the geometry, and that the copper loss is consistent with D62's form."""
import math
import unittest

from scb_ivr.p24_inductor_model import MU0, RHO_CU, Stripline, effective_r_per_l, skin_depth


class Stripline_(unittest.TestCase):
    def test_skin_depth_copper_1mhz(self):
        self.assertAlmostEqual(skin_depth(1e6) * 1e6, 66.0, delta=0.5)      # 66 um at 1 MHz (textbook)

    def test_r_per_l_from_geometry(self):
        # L = mu0 l h / w and R = 2 rho l / (w t): R / L = 2 rho / (mu0 h t), whatever l and w
        h, t, l, w = 1e-3, 70e-6, 20e-3, 8e-3
        L = MU0 * l * h / w
        R = 2 * RHO_CU * l / (w * t)
        self.assertAlmostEqual(Stripline(h, t).r_per_l_dc(), R / L, places=6)

    def test_ac_uses_the_skin_depth_when_thicker(self):
        s = Stripline(1e-3, 300e-6)
        self.assertAlmostEqual(s.r_per_l_ac(1e6) / s.r_per_l_dc(), 300e-6 / skin_depth(1e6), places=6)
        self.assertEqual(Stripline(1e-3, 20e-6).r_per_l_ac(1e6), Stripline(1e-3, 20e-6).r_per_l_dc())

    def test_loss_matches_the_effective_r_per_l(self):
        s, lf, f, pp = Stripline(2e-3, 105e-6), 7.3333e-9, 0.84e6, 152.7
        ms = 62.5 ** 2 + (pp / math.sqrt(12)) ** 2
        self.assertAlmostEqual(s.loss(lf, f, pp), 4 * lf * effective_r_per_l(s, f, pp) * ms, places=9)


if __name__ == "__main__":
    unittest.main()
