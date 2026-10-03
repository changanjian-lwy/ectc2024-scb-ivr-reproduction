"""ml_conformal: the finite-sample rank, the coverage guarantee on exchangeable data (1 - alpha <= coverage <
1 - alpha + 1 / (n + 1)), the signed and Mondrian variants, and adaptive conformal inference under drift."""
import math
import unittest

import numpy as np

from scb_ivr.extensions.ml_conformal import ACI, band, mondrian_band, quantile


class Rank(unittest.TestCase):
    def test_rank_and_infinity(self):
        s = np.arange(1.0, 10.0)                       # n = 9
        self.assertEqual(quantile(s, 0.2), 8.0)         # ceil(10 x 0.8) = 8th smallest
        self.assertEqual(quantile(s, 0.1), 9.0)         # ceil(10 x 0.9) = 9
        self.assertEqual(quantile(s, 0.05), math.inf)   # ceil(9.5) = 10 > 9
        self.assertEqual(quantile([1.0, 2.0, 3.0], 0.2), math.inf)
        self.assertEqual(quantile(s, 1.0), -math.inf)


def trials(n_cal, alpha, signed, kind, n_trials=20000, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(100, 200, (n_trials, n_cal + 1))
    e = rng.standard_t(4, (n_trials, n_cal + 1)) * 0.05 + 0.02     # biased, heavy-tailed relative errors
    y = p * (1 + e) if kind == "rel" else p * np.exp(e)
    hit = np.empty(n_trials, bool)
    for t in range(n_trials):
        lo, hi = band(p[t, :-1], y[t, :-1], p[t, -1:], alpha, kind, signed)
        hit[t] = lo[0] <= y[t, -1] <= hi[0]
    return hit.mean()


class Coverage(unittest.TestCase):
    def test_symmetric(self):
        for n, alpha in ((19, 0.2), (9, 0.2), (39, 0.1)):
            c = trials(n, alpha, False, "rel")
            self.assertGreaterEqual(c, 1 - alpha - 0.01)
            self.assertLess(c, 1 - alpha + 1 / (n + 1) + 0.01)

    def test_signed_and_log(self):
        self.assertGreaterEqual(trials(39, 0.2, True, "rel"), 0.79)
        self.assertGreaterEqual(trials(19, 0.2, False, "log"), 0.79)

    def test_signed_is_narrower_under_bias(self):
        rng = np.random.default_rng(3)
        p = np.full(200, 150.0); y = p * (1 + 0.08 + 0.02 * rng.normal(size=200))   # all under-predicted by ~8%
        lo_s, hi_s = band(p, y, [150.0], 0.2)
        lo_g, hi_g = band(p, y, [150.0], 0.2, signed=True)
        self.assertLess(hi_g[0] - lo_g[0], 0.5 * (hi_s[0] - lo_s[0]))
        self.assertGreater(lo_g[0], 150.0)


class Mondrian(unittest.TestCase):
    def test_per_group_width(self):
        rng = np.random.default_rng(4)
        g = np.array(["a"] * 100 + ["b"] * 100)
        p = np.full(200, 100.0)
        y = p * (1 + np.where(g == "a", 0.02, 0.15) * rng.normal(size=200))
        lo, hi = mondrian_band(p, y, g, [100.0, 100.0], ["a", "b"], 0.2)
        self.assertLess(hi[0] - lo[0], 0.3 * (hi[1] - lo[1]))


class Adaptive(unittest.TestCase):
    def test_drift(self):
        """Errors growing over time: split conformal on a fixed calibration set under-covers, ACI recovers alpha."""
        rng = np.random.default_rng(5)
        cal_p = np.full(50, 100.0); cal_y = cal_p * (1 + 0.03 * rng.normal(size=50))
        aci = ACI(0.2, 0.01)
        hit_s, hit_a = [], []
        for t in range(3000):
            sd = 0.03 * (1 + t / 500)
            y = 100.0 * (1 + sd * rng.normal())
            lo, hi = band(cal_p, cal_y, [100.0], 0.2)
            hit_s.append(lo[0] <= y <= hi[0])
            lo, hi = aci.band(cal_p, cal_y, [100.0])
            h = lo[0] <= y <= hi[0]
            hit_a.append(h); aci.update([h])
        self.assertLess(np.mean(hit_s), 0.5)
        self.assertGreater(np.mean(hit_a), 0.7)


if __name__ == "__main__":
    unittest.main()
