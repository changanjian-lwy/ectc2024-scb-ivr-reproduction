"""ml_gp: the closed-form leave-one-out against refitting without each point (same hyperparameters), and that the
posterior learns a smooth function with calibrated uncertainty."""
import unittest

import numpy as np

from scb_ivr.extensions.ml_gp import GP


class LeaveOneOut(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = np.random.default_rng(0)
        x = rng.uniform(-2, 2, (25, 2)); y = np.sin(x[:, 0]) + 0.3 * x[:, 1] + 0.05 * rng.normal(size=25)
        g = GP().fit(x, y, restarts=3)
        mu, sd = g.loo()
        for i in (0, 7, 19):
            keep = np.arange(25) != i
            h = GP(); h.s, h.n, h.l = g.s, g.n, g.l
            h.x, h.mu = x[keep], g.mu
            h.y = y[keep] - g.mu
            K = h._kernel(h.x, h.x, h.s, h.l) + (h.n ** 2 + 1e-10) * np.eye(24)
            from scipy.linalg import cho_factor, cho_solve
            h.c = cho_factor(K, lower=True); h.alpha = cho_solve(h.c, h.y)
            m, s = h.predict(x[i:i + 1])
            self.assertAlmostEqual(mu[i], m[0], places=6)
            self.assertAlmostEqual(sd[i], s[0], places=6)


class Learns(unittest.TestCase):
    def test_smooth_function_and_coverage(self):
        rng = np.random.default_rng(1)
        x = rng.uniform(-3, 3, (60, 1)); y = np.sin(x[:, 0]) + 0.1 * rng.normal(size=60)
        g = GP().fit(x, y, restarts=4)
        xt = np.linspace(-2.5, 2.5, 50)[:, None]
        m, s = g.predict(xt, noise=False)
        self.assertLess(float(np.max(np.abs(m - np.sin(xt[:, 0])))), 0.15)
        mu, sd = g.loo()
        self.assertGreater(float(np.mean(np.abs(y - mu) <= 1.645 * sd)), 0.8)

    def test_far_from_data_returns_the_prior(self):
        x = np.linspace(0, 1, 10)[:, None]; y = 2.0 * x[:, 0]
        g = GP().fit(x, y, restarts=2)
        m, s = g.predict(np.array([[1e4]]), noise=False)        # far beyond the largest length scale allowed (e^4)
        self.assertAlmostEqual(m[0], float(np.mean(y)), places=3)
        self.assertAlmostEqual(s[0], g.s, places=3)


if __name__ == "__main__":
    unittest.main()
