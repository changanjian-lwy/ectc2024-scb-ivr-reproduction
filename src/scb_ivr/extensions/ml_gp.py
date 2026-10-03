"""Gaussian-process regression in numpy/scipy (extension ml_design_assist), for small data with uncertainty.

Kernel: k(x, x') = s^2 exp(-1/2 sum_d ((x_d - x'_d) / l_d)^2) (squared exponential with one length scale per input,
"ARD"), plus noise n^2 on the diagonal. With K = k(X, X) + n^2 I and its Cholesky factor L:
- the posterior mean at x*: k*^T K^-1 y; its variance: k(x*, x*) - k*^T K^-1 k* (+ n^2 for a new observation);
- the log marginal likelihood: -1/2 y^T K^-1 y - sum log diag L - n/2 log 2 pi, maximised over (log s, log l, log n)
  with L-BFGS from several starts (fixed length scales stay at their value);
- leave-one-out without refitting (Rasmussen & Williams 2006, Eq. 5.12): mu_-i = y_i - [K^-1 y]_i / [K^-1]_ii,
  var_-i = 1 / [K^-1]_ii.
Targets are centred on their training mean (the prior mean).
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize


class GP:
    def __init__(self, fixed_l=None):
        """fixed_l: {input index: length scale} held fixed (inputs without variation in the training data)."""
        self.fixed_l = dict(fixed_l or {})

    def _kernel(self, a, b, s, l):
        d = (a[:, None, :] - b[None, :, :]) / l
        return s * s * np.exp(-0.5 * np.sum(d * d, axis=2))

    def _unpack(self, th, dim):
        s, n = np.exp(th[0]), np.exp(th[1])
        l = np.exp(th[2:2 + dim]).copy()
        for i, v in self.fixed_l.items():
            l[i] = v
        return s, n, l

    def _nlml(self, th, x, y):
        s, n, l = self._unpack(th, x.shape[1])
        K = self._kernel(x, x, s, l) + (n * n + 1e-10) * np.eye(len(x))
        try:
            c = cho_factor(K, lower=True)
        except np.linalg.LinAlgError:
            return 1e12
        a = cho_solve(c, y)
        return float(0.5 * y @ a + np.sum(np.log(np.diag(c[0]))) + 0.5 * len(x) * np.log(2 * np.pi))

    def fit(self, x, y, restarts=8, seed=0):
        self.x, self.mu = np.asarray(x, float), float(np.mean(y))
        self.y = np.asarray(y, float) - self.mu
        dim = self.x.shape[1]
        rng = np.random.default_rng(seed)
        sy = max(float(np.std(self.y)), 1e-6)
        best = None
        for r in range(restarts):
            th0 = np.concatenate([[np.log(sy), np.log(0.3 * sy)], rng.normal(0.0, 0.5, dim)])
            res = minimize(self._nlml, th0, args=(self.x, self.y), method="L-BFGS-B",
                           bounds=[(np.log(1e-3 * sy), np.log(1e2 * sy)), (np.log(1e-3 * sy), np.log(10 * sy))] + [(-3.0, 4.0)] * dim)
            if best is None or res.fun < best.fun:
                best = res
        self.theta = best.x
        self.s, self.n, self.l = self._unpack(best.x, dim)
        K = self._kernel(self.x, self.x, self.s, self.l) + (self.n ** 2 + 1e-10) * np.eye(len(self.x))
        self.c = cho_factor(K, lower=True)
        self.alpha = cho_solve(self.c, self.y)
        self.Kinv = cho_solve(self.c, np.eye(len(self.x)))
        self.nlml = float(best.fun)
        return self

    def predict(self, xs, noise=True):
        """(mean, sd) at xs; sd of a new observation when noise, of the latent function otherwise."""
        ks = self._kernel(np.asarray(xs, float), self.x, self.s, self.l)
        mean = ks @ self.alpha + self.mu
        v = cho_solve(self.c, ks.T)
        var = self.s ** 2 - np.sum(ks * v.T, axis=1) + (self.n ** 2 if noise else 0.0)
        return mean, np.sqrt(np.maximum(var, 1e-12))

    def loo(self):
        """Leave-one-out (mean, sd) at each training point, without refitting the hyperparameters."""
        d = np.diag(self.Kinv)
        return self.y + self.mu - self.alpha / d, np.sqrt(1.0 / d)
