"""ml_nn: the backward pass against finite differences, and that the network learns a smooth function and a class."""
import unittest

import numpy as np

from scb_ivr.extensions.ml_nn import MLP, Scaler


class Gradients(unittest.TestCase):
    def _check(self, out):
        rng = np.random.default_rng(1)
        net = MLP([3, 5, 4, 2], out=out, seed=2)
        x = rng.normal(size=(7, 3))
        y = rng.random((7, 2)) if out == "sigmoid" else rng.normal(size=(7, 2))
        _, gW, gb = net.loss_grads(x, y)
        h = 1e-6
        for par, g in list(zip(net.W, gW)) + list(zip(net.b, gb)):
            for idx in np.ndindex(par.shape):
                old = par[idx]
                par[idx] = old + h; lp = net.loss_grads(x, y)[0]
                par[idx] = old - h; lm = net.loss_grads(x, y)[0]
                par[idx] = old
                self.assertAlmostEqual(g[idx], (lp - lm) / (2 * h), delta=1e-6 * max(1.0, abs(g[idx])))

    def test_linear(self):
        self._check("linear")

    def test_sigmoid(self):
        self._check("sigmoid")


class Learns(unittest.TestCase):
    def test_regression(self):
        rng = np.random.default_rng(0)
        x = rng.uniform(-2, 2, (800, 2)); y = np.sin(x[:, :1]) * np.cos(x[:, 1:])
        sx = Scaler.fit(x)
        net = MLP([2, 32, 32, 1], seed=0)
        net.fit(sx.fwd(x[:600]), y[:600], sx.fwd(x[600:]), y[600:], epochs=300, lr=5e-3)
        err = net.predict(sx.fwd(x[600:])) - y[600:]
        self.assertLess(float(np.sqrt(np.mean(err ** 2))), 0.05)

    def test_classification(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=(600, 2)); y = (x[:, :1] ** 2 + x[:, 1:] ** 2 < 1.0).astype(float)
        net = MLP([2, 16, 1], out="sigmoid", seed=0)
        net.fit(x[:500], y[:500], x[500:], y[500:], epochs=300, lr=1e-2)
        acc = float(np.mean((net.predict(x[500:]) > 0.5) == (y[500:] > 0.5)))
        self.assertGreater(acc, 0.93)


if __name__ == "__main__":
    unittest.main()
