"""ml_ppo: the hand-written policy gradient against finite differences of the surrogate loss, and that PPO learns a
stabilising feedback on a noisy scalar system."""
import unittest

import numpy as np

from scb_ivr.extensions.ml_ppo import GaussianPolicy, train


def surrogate(pol, O, A, LP0, ADV, clip=0.2):
    rho = np.exp(pol.logp(A, pol.mean(O)) - LP0)
    return -float(np.mean(np.minimum(rho * ADV, np.clip(rho, 1 - clip, 1 + clip) * ADV)))


class Gradient(unittest.TestCase):
    def test_against_finite_differences(self):
        rng = np.random.default_rng(0)
        pol = GaussianPolicy(3, 2, (8,), log_std=-0.5, seed=1)
        pol.net.W[-1] *= 100.0                              # a non-trivial mean
        O = rng.normal(size=(40, 3)); A = pol.mean(O) + 0.3 * rng.normal(size=(40, 2))
        LP0 = pol.logp(A, pol.mean(O)) + 0.05 * rng.normal(size=40)     # an "old" policy near the current one
        ADV = rng.normal(size=40)
        acts = pol.net.forward(O); mu = acts[-1]; sd = np.exp(pol.log_std)
        lp = pol.logp(A, mu); rho = np.exp(lp - LP0)
        use = rho * ADV <= np.clip(rho, 0.8, 1.2) * ADV
        d_lp = -np.where(use, rho * ADV, 0.0) / 40
        gW, gb = pol.net.backward(acts, d_lp[:, None] * (A - mu) / sd ** 2)
        g_ls = np.sum(d_lp[:, None] * (((A - mu) / sd) ** 2 - 1.0), axis=0)
        eps = 1e-6
        for par, g in ((pol.net.W[0], gW[0]), (pol.net.b[1], gb[1]), (pol.log_std, g_ls)):
            for idx in [(0,) * par.ndim, tuple(s - 1 for s in par.shape)]:
                old = par[idx]
                par[idx] = old + eps; up = surrogate(pol, O, A, LP0, ADV)
                par[idx] = old - eps; dn = surrogate(pol, O, A, LP0, ADV)
                par[idx] = old
                self.assertAlmostEqual((up - dn) / (2 * eps), g[idx], places=5)


class Anchored(unittest.TestCase):
    def test_zero_at_anchor_and_gradient(self):
        rng = np.random.default_rng(2)
        anchor = lambda O: np.concatenate([np.zeros((len(O), 2)), O[:, 2:]], axis=1)
        pol = GaussianPolicy(3, 2, (8,), log_std=-0.5, seed=1, anchor=anchor)
        pol.net.W[-1] *= 100.0
        self.assertTrue(np.allclose(pol.mean(np.array([[0.0, 0.0, 1.0]])), 0.0))
        O = rng.normal(size=(30, 3)); A = pol.mean(O) + 0.3 * rng.normal(size=(30, 2))
        LP0 = pol.logp(A, pol.mean(O)) + 0.05 * rng.normal(size=30); ADV = rng.normal(size=30)
        mu, cache = pol.forward(O); sd = np.exp(pol.log_std)
        rho = np.exp(pol.logp(A, mu) - LP0)
        d_lp = -np.where(rho * ADV <= np.clip(rho, 0.8, 1.2) * ADV, rho * ADV, 0.0) / 30
        gW, _ = pol.backward(cache, d_lp[:, None] * (A - mu) / sd ** 2)
        par, eps = pol.net.W[0], 1e-6
        old = par[0, 0]
        par[0, 0] = old + eps; up = surrogate(pol, O, A, LP0, ADV)
        par[0, 0] = old - eps; dn = surrogate(pol, O, A, LP0, ADV)
        par[0, 0] = old
        self.assertAlmostEqual((up - dn) / (2 * eps), gW[0][0, 0], places=5)


class Scalar:
    """x' = 0.9 x + 0.5 a + noise, reward -x^2 - 0.01 a^2, 30 steps from x ~ U(-2, 2)."""

    def reset(self, rng):
        self.rng, self.k = rng, 0
        self.x = rng.uniform(-2, 2)
        return np.array([self.x, 1.0])

    def step(self, a):
        a = float(np.clip(a[0], -3, 3))
        r = -self.x ** 2 - 0.01 * a * a
        self.x = 0.9 * self.x + 0.5 * a + 0.05 * self.rng.normal()
        self.k += 1
        return np.array([self.x, 1.0]), r, self.k >= 30, {}


class Learns(unittest.TestCase):
    def test_scalar_feedback(self):
        env = Scalar()
        pol, _, hist = train(env, 2, 1, iters=40, episodes=16, lr=3e-3, log_std=-0.5, hidden=(16,), seed=0)
        self.assertGreater(np.mean(hist[-5:]), 0.5 * np.mean(hist[:3]))       # returns are negative: less negative
        gain = (pol.mean(np.array([[1.0, 1.0]]))[0, 0] - pol.mean(np.array([[-1.0, 1.0]]))[0, 0]) / 2
        self.assertLess(gain, -0.5)                                           # a = -k x with k > 0.5


if __name__ == "__main__":
    unittest.main()
