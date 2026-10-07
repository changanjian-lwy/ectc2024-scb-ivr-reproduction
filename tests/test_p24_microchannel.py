"""D77 microchannel cooler: Shah-London limits, fin efficiency against a 2D solve, and the coolant march's energy
balance and infinite-flow limit."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from scb_ivr import p24_microchannel as M  # noqa: E402
from scb_ivr import p24_thermal as T  # noqa: E402


class Cooler(unittest.TestCase):
    def test_shah_london_limits(self):
        self.assertAlmostEqual(M.nu_h1(1e-12), 8.235, places=3)
        self.assertAlmostEqual(M.nu_h1(1.0), 3.61, places=2)
        self.assertAlmostEqual(M.f_re(1e-12), 24.0, places=3)
        self.assertAlmostEqual(M.f_re(1.0), 14.23, places=2)
        self.assertAlmostEqual(M.nu_h1(0.25), M.nu_h1(4.0))

    def test_fin_against_2d(self):
        w, hgt, k, h = 100e-6, 400e-6, T.K_CU, 21000.0
        g = T.Grid(np.linspace(0, w / 2, 11), [0, 1e-3], np.linspace(0, hgt, 81))
        s = T.Solver(g, k, k, k, {"z0": ("T", 1.0), "x1": ("h", h, 0.0)})
        q = -s.face_heat(s.solve(np.zeros(g.shape)))["z0"]
        self.assertLess(abs(q / (M.fin_efficiency(h, k, w, hgt) * h * hgt * 1e-3) - 1), 0.003)

    def test_cooler_scaling(self):
        a = M.cooler(100e-6, 400e-6, 100e-6, T.K_CU, 1e-3, 12.5e-3, 20e-3)
        b = M.cooler(100e-6, 400e-6, 100e-6, T.K_CU, 2e-3, 12.5e-3, 20e-3)
        self.assertAlmostEqual(a["h_eff"], b["h_eff"])               # fully developed laminar: h independent of flow
        self.assertAlmostEqual(b["dp_pa"] / a["dp_pa"], 2.0)
        self.assertLess(a["re"], 2300)


class CoolantMarch(unittest.TestCase):
    def test_energy_and_limit(self):
        import p24_thermal_stack as S
        src, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH", 1.0, 1.0)
        base = {"f_g1": 0.02, "h_bot": 9e4, "t_cool": 25.0, "dx": 0.5e-3, "dy": 0.5e-3, "y_full": True}
        m = T.build(base)
        st = T.coupled(m, src, a_sw, a_cu, method="cg", max_iter=200, coolant={"m_dot": 1e-3, "t_in": 25.0, "cp": 4179.0})[1]
        self.assertLess(abs(st["coolant_heat_w"] / st["p_total_w"] - 1), 1e-5)
        self.assertAlmostEqual(st["coolant_t_out_mean"] - 25.0, st["coolant_heat_w"] / (1e-3 * 4179.0), places=6)
        uni = T.coupled(T.build(base), src, a_sw, a_cu, method="cg")[1]
        inf = T.coupled(T.build(base), src, a_sw, a_cu, method="cg", coolant={"m_dot": 1e3, "t_in": 25.0, "cp": 4179.0})[1]
        self.assertAlmostEqual(uni["t_max"], inf["t_max"], places=3)
        self.assertGreater(st["t_max"], uni["t_max"] + 5)


if __name__ == "__main__":
    unittest.main()
