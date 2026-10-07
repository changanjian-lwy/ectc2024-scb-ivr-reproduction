"""D74 conduction solver: closed-form checks (slab, layered 1D, flux channels), solver identities and the module
model's energy balance. Coarse grids; scripts/p24_thermal_verify.py runs the refinement studies."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from scb_ivr import p24_thermal as T  # noqa: E402


def channel(a, b, layers_bottom_up, h, c, d, q0, dxy, dz):
    zb = np.concatenate([[0.0], np.cumsum([t for t, _, _ in layers_bottom_up])])
    g = T.Grid(T.edges([0, a / 2 - c / 2, a / 2 + c / 2, a], dxy), T.edges([0, b / 2 - d / 2, b / 2 + d / 2, b], dxy),
               T.edges(list(zb), dz))
    kxy, kz = np.zeros(g.shape), np.zeros(g.shape)
    for (t, kx, kzz), z0, z1 in zip(layers_bottom_up, zb[:-1], zb[1:]):
        m = g.box(z=(z0, z1))
        kxy[m], kz[m] = kx, kzz
    src = g.box(x=(a / 2 - c / 2, a / 2 + c / 2), y=(b / 2 - d / 2, b / 2 + d / 2))[:, :, 0]
    q = np.zeros(g.shape)
    q[:, :, -1] = src * q0 * g.dx[:, None] * g.dy[None, :]
    t, fh = T.solve(g, kxy, kxy, kz, q, {"z0": ("h", h, 0.0)})
    ts = t[:, :, -1] + np.where(src, q0 * g.dz[-1] / (2 * kz[:, :, -1]), 0.0)
    return float(ts[src].mean()), fh["z0"] / (q0 * c * d)


class Closed(unittest.TestCase):
    def test_slab_second_order_and_energy(self):
        errs = []
        for nz in (8, 16):
            g = T.Grid([0, 1e-3], [0, 1e-3], np.linspace(0, 1e-3, nz + 1))
            t, fh = T.solve(g, 2.0, 2.0, 2.0, 1e8 * g.volume(), {"z1": ("h", 2e4, 25.0)})
            errs.append(np.abs(t[0, 0] - T.slab_generation(g.zc, 1e-3, 2.0, 1e8, 2e4, 25.0)).max())
            self.assertAlmostEqual(fh["z1"], 1e8 * 1e-9, delta=1e-12)
        self.assertAlmostEqual(errs[0] / errs[1], 4.0, delta=0.01)

    def test_layered_1d_exact(self):
        layers = [(200e-6, T.K_CU), (518e-6, 120.0), (30e-6, T.K_ABF), (300e-6, 1.1), (300e-6, 2.0)]
        zb = np.concatenate([[0.0], np.cumsum([t for t, _ in layers])])
        g = T.Grid([0, 1e-3], [0, 1e-3], T.edges(list(zb), 70e-6))
        k = np.zeros(g.shape)
        for (t, kk), z0, z1 in zip(layers, zb[:-1], zb[1:]):
            k[g.box(z=(z0, z1))] = kk
        q = np.zeros(g.shape)
        q[0, 0, -1] = 2e5 * 1e-6
        t, _ = T.solve(g, k, k, k, q, {"z0": ("h", 2e4, 0.0)})
        top = t[0, 0, -1] + 2e5 * g.dz[-1] / (2 * k[0, 0, -1])
        exact = 2e5 * (1 / 2e4 + sum(t / kk for t, kk in layers))
        self.assertLess(abs(top / exact - 1), 1e-12)

    def test_flux_channel_converges_to_series(self):
        a = b = 10e-3
        exact, field = T.flux_channel(a, b, [(1e-3, 20.0, 20.0)], 1e4, (a / 2, b / 2, 2e-3, 2e-3, 1e6), 400, 400)
        self.assertAlmostEqual(exact, 43.1703, delta=2e-3)                 # D74_verification.json
        self.assertGreater(field(a / 2, b / 2)[0], exact)                   # centre hotter than the source mean
        e = [channel(a, b, [(1e-3, 20.0, 20.0)], 1e4, 2e-3, 2e-3, 1e6, dxy, dxy / 2)[0] / exact - 1
             for dxy in (0.5e-3, 0.25e-3)]
        self.assertTrue(0 < e[1] < 0.025 and np.log2(e[0] / e[1]) > 1.5, e)

    def test_compound_channel(self):
        a = b = 10e-3
        c = d = 2.85e-3
        q0 = 1.33 / (c * d)
        top, bot = (200e-6, T.K_CU, T.K_CU), (300e-6, 1.1, 1.1)
        exact, _ = T.flux_channel(a, b, [top, bot], 2e4, (a / 2, b / 2, c, d, q0), 400, 400)
        num, eb = channel(a, b, [bot, top], 2e4, c, d, q0, 0.25e-3, 25e-6)
        self.assertLess(abs(num / exact - 1), 0.005)
        self.assertLess(abs(eb - 1), 1e-10)

    def test_orthotropic_equals_stretched_isotropic(self):
        a = b = 5e-3
        kxy, kz = T.via_k(0.05, T.K_CU, 1.1)
        src = (a / 2, b / 2, 1e-3, 1e-3, 1e6)
        ortho, _ = T.flux_channel(a, b, [(300e-6, kxy, kz)], 2e4, src)
        ke, te = np.sqrt(kxy * kz), 300e-6 * np.sqrt(kxy / kz)
        iso, _ = T.flux_channel(a, b, [(te, ke, ke)], 2e4, src)
        self.assertLess(abs(ortho / iso - 1), 1e-10)

    def test_via_k_limits(self):
        self.assertEqual(T.via_k(0.0, 390.0, 1.1), (1.1, 1.1))
        kxy, kz = T.via_k(1.0, 390.0, 1.1)
        self.assertAlmostEqual(kxy, 390.0)
        self.assertAlmostEqual(kz, 390.0)
        self.assertAlmostEqual(T.via_count(0.196, 3600e-12, 30e-6), 0.196 * 3600 / (np.pi * 225), places=9)


class Solver(unittest.TestCase):
    def test_direct_equals_cg(self):
        g = T.Grid(T.edges([0, 3e-3], 0.25e-3), T.edges([0, 2e-3], 0.25e-3), T.edges([0, 100e-6, 400e-6], 50e-6))
        rng = np.random.default_rng(1)
        k = np.where(g.box(z=(0, 100e-6)), T.K_CU, 1.0) * rng.uniform(0.5, 2.0, g.shape)
        q = rng.uniform(0, 1e-3, g.shape)
        bc = {"z0": ("h", 2e4, 25.0), "x1": ("T", 30.0)}
        t1 = T.Solver(g, k, 0.5 * k, 2 * k, bc, "direct").solve(q)
        s = T.Solver(g, k, 0.5 * k, 2 * k, bc, "cg")
        t2 = s.solve(q)
        self.assertLess(np.abs(t1 - t2).max(), 1e-8)
        heat = s.face_heat(t2)
        self.assertAlmostEqual(sum(heat.values()), q.sum(), delta=1e-9)


class Module(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import p24_thermal_stack as S
        cls.src, cls.a_sw, cls.a_cu = S.sources("2.5MHz_N29", "86um_150pH")
        cls.res = {}
        for f in (0.0, 0.02):
            m = T.build({"f_g1": f, "dx": 0.5e-3, "dy": 0.5e-3, "t_cool": 45.0})
            cls.res[f] = (m,) + T.coupled(m, cls.src, cls.a_sw, cls.a_cu, method="cg")

    def test_die_areas_and_energy(self):
        m, t, st, src, it, fh = self.res[0.0]
        self.assertTrue(all(abs(d["area_check"] - 1) < 1e-9 for d in m["dies"]))
        self.assertLess(abs(2 * fh["z0"] / st["p_total_w"] - 1), 1e-9)
        self.assertLess(it, 30)

    def test_losses_follow_local_temperatures(self):
        m, t, st, src, it, fh = self.res[0.0]
        ind = sum(self.src["inductor"] / 4 * (1 + self.a_cu * (ti - 25)) for ti in st["t_ind_cols"])
        self.assertAlmostEqual(st["p_inductor_w"], ind, delta=1e-3)      # losses lag one iterate (tol 1e-3 K)
        self.assertGreater(st["p_dies_w"], sum(2 * c[0] + 3 * c[1] for c in self.src["die_cond"].values()))

    def test_inductor_is_hottest_and_vias_cool_it(self):
        st0, st2 = self.res[0.0][2], self.res[0.02][2]
        self.assertEqual(st0["t_max"], st0["inductor_max"])
        self.assertGreater(st0["inductor_max"] - st0["junction_max"], 30.0)
        self.assertLess(st2["inductor_max"], st0["inductor_max"] - 20.0)


if __name__ == "__main__":
    unittest.main()
