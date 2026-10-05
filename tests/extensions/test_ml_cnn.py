"""ml_cnn: every layer's backward pass against finite differences, save / load, and that a small network learns the
frequency of a noisy sine wave (a stand-in for reading a ring's period off a waveform)."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scb_ivr.extensions.ml_cnn import Sequential

SPECS = [["conv", 2, 3, 3], ["relu"], ["pool"], ["conv", 3, 2, 5], ["tanh"], ["up"], ["conv", 2, 2, 3], ["pool"],
         ["flatten"], ["dense", 2 * 4, 3], ["tanh"], ["dense", 3, 2 * 4], ["unflatten", 2, 4]]


class Gradients(unittest.TestCase):
    def test_every_parameter(self):
        rng = np.random.default_rng(1)
        net = Sequential(SPECS, seed=2)
        x = rng.normal(size=(4, 2, 9))                       # odd length: the pool drops a sample
        y = rng.normal(size=(4, 2, 4))
        _, g = net.loss_grads(x, y)
        h = 1e-6
        for par, gp in zip(net.params(), g):
            for idx in np.ndindex(par.shape):
                old = par[idx]
                par[idx] = old + h; lp = net.loss_grads(x, y)[0]
                par[idx] = old - h; lm = net.loss_grads(x, y)[0]
                par[idx] = old
                self.assertAlmostEqual(gp[idx], (lp - lm) / (2 * h), delta=1e-6 * max(1.0, abs(gp[idx])))

    def test_input_gradient(self):
        rng = np.random.default_rng(3)
        net = Sequential(SPECS, seed=4)
        x = rng.normal(size=(2, 2, 9)); y = rng.normal(size=(2, 2, 4))
        p = net.forward(x)
        dx = net.backward(2.0 * (p - y) / len(x))
        h = 1e-6
        for idx in np.ndindex(x.shape):
            xp, xm = x.copy(), x.copy(); xp[idx] += h; xm[idx] -= h
            num = (np.sum((net.forward(xp) - y) ** 2) - np.sum((net.forward(xm) - y) ** 2)) / len(x) / (2 * h)
            self.assertAlmostEqual(dx[idx], num, delta=1e-6 * max(1.0, abs(num)))


class Learning(unittest.TestCase):
    def test_sine_frequency_and_save_load(self):
        rng = np.random.default_rng(5)
        t = np.arange(64)
        f = rng.uniform(0.03, 0.12, 600)
        x = (np.sin(2 * np.pi * f[:, None] * t + rng.uniform(0, 6.3, (600, 1))) + 0.1 * rng.normal(size=(600, 64)))[:, None, :]
        y = ((f - 0.075) / 0.026)[:, None]
        net = Sequential([["conv", 1, 6, 5], ["relu"], ["pool"], ["conv", 6, 8, 5], ["relu"], ["pool"], ["flatten"],
                          ["dense", 8 * 16, 16], ["relu"], ["dense", 16, 1]], seed=0)
        net.fit(x[:500], y[:500], x[500:], y[500:], epochs=60, batch=32, lr=3e-3, patience=15)
        rmse = float(np.sqrt(np.mean((net.predict(x[500:]) - y[500:]) ** 2)))
        self.assertLess(rmse, 0.35)                          # vs 1.0 for predicting the mean
        with tempfile.TemporaryDirectory() as d:
            net.save(Path(d) / "n.npz")
            net2, _ = Sequential.load(Path(d) / "n.npz")
        self.assertTrue(np.array_equal(net.predict(x[500:]), net2.predict(x[500:])))


if __name__ == "__main__":
    unittest.main()
