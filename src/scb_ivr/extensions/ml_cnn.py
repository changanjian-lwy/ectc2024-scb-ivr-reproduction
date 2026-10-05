"""A small one-dimensional convolutional network in numpy (extension ml_design_assist): Conv1D, ReLU, Tanh, AvgPool1D,
Upsample1D, Flatten, Unflatten and Dense layers in a Sequential stack, trained with Adam (ml_nn.Adam) on a
mean-square loss, minibatches and early stopping on a validation set. Used for waveforms (A146: a V_DS ring ->
the loop's parameters) and sequences of per-period features (A147: an autoencoder of co-simulation runs).

Written out like ml_nn so every step can be read: each layer's forward keeps what its backward needs; backward takes
dL/d(output), stores the parameter gradients and returns dL/d(input). Tensors are (samples, channels, time). A
convolution sums over the input channels and the k taps of a window, with the input zero-padded by k // 2 on both
sides so the length is kept (odd k):  y[n, o, t] = b[o] + sum_c sum_j W[o, c, j] x[n, c, t + j].
Why convolution for these inputs: the features (a ring's period and decay, a limit cycle, a spike) are local patterns
that may sit anywhere in time; one filter slid along the time axis finds them wherever they are, with far fewer
weights than a dense layer over every sample.
"""
from __future__ import annotations

import json

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from .ml_nn import Adam


class Conv1D:
    def __init__(self, c_in, c_out, k, rng):
        if k % 2 != 1:
            raise ValueError("Conv1D: odd kernel length")
        self.k, self.spec = k, ["conv", c_in, c_out, k]
        self.W = rng.normal(0.0, np.sqrt(2.0 / (c_in * k)), (c_out, c_in, k))      # He init (a ReLU follows)
        self.b = np.zeros(c_out)

    def forward(self, x):
        p = self.k // 2
        win = sliding_window_view(np.pad(x, ((0, 0), (0, 0), (p, p))), self.k, axis=2)    # (n, c_in, T, k), a view
        self._win, self._T = win, x.shape[2]
        return np.einsum("nctj,ocj->not", win, self.W, optimize=True) + self.b[None, :, None]

    def backward(self, g):
        self.gW = np.einsum("not,nctj->ocj", g, self._win, optimize=True)
        self.gb = g.sum(axis=(0, 2))
        p, T = self.k // 2, self._T
        dxp = np.zeros((g.shape[0], self.W.shape[1], T + 2 * p))
        for j in range(self.k):                                    # tap j saw input sample t + j
            dxp[:, :, j:j + T] += np.einsum("oc,not->nct", self.W[:, :, j], g, optimize=True)
        return dxp[:, :, p:p + T]

    def params(self):
        return [self.W, self.b]

    def grads(self):
        return [self.gW, self.gb]


class Dense:
    def __init__(self, n_in, n_out, rng):
        self.spec = ["dense", n_in, n_out]
        self.W = rng.normal(0.0, np.sqrt(1.0 / n_in), (n_in, n_out))
        self.b = np.zeros(n_out)

    def forward(self, x):
        self._x = x
        return x @ self.W + self.b

    def backward(self, g):
        self.gW, self.gb = self._x.T @ g, g.sum(axis=0)
        return g @ self.W.T

    def params(self):
        return [self.W, self.b]

    def grads(self):
        return [self.gW, self.gb]


class _NoParams:
    def params(self):
        return []

    def grads(self):
        return []


class ReLU(_NoParams):
    spec = ["relu"]

    def forward(self, x):
        self._m = x > 0
        return x * self._m

    def backward(self, g):
        return g * self._m


class Tanh(_NoParams):
    spec = ["tanh"]

    def forward(self, x):
        self._y = np.tanh(x)
        return self._y

    def backward(self, g):
        return g * (1.0 - self._y ** 2)


class AvgPool1D(_NoParams):
    """Mean of non-overlapping pairs (an odd last sample is dropped; its gradient is 0)."""
    spec = ["pool"]

    def forward(self, x):
        self._shape = x.shape
        m = x.shape[2] // 2
        return x[:, :, :2 * m].reshape(x.shape[0], x.shape[1], m, 2).mean(axis=3)

    def backward(self, g):
        dx = np.zeros(self._shape)
        dx[:, :, :2 * g.shape[2]] = np.repeat(g, 2, axis=2) * 0.5
        return dx


class Upsample1D(_NoParams):
    """Each sample repeated twice (the decoder's inverse of AvgPool1D)."""
    spec = ["up"]

    def forward(self, x):
        return np.repeat(x, 2, axis=2)

    def backward(self, g):
        return g.reshape(g.shape[0], g.shape[1], -1, 2).sum(axis=3)


class Flatten(_NoParams):
    spec = ["flatten"]

    def forward(self, x):
        self._shape = x.shape
        return x.reshape(x.shape[0], -1)

    def backward(self, g):
        return g.reshape(self._shape)


class Unflatten(_NoParams):
    def __init__(self, c, t):
        self.c, self.t, self.spec = c, t, ["unflatten", c, t]

    def forward(self, x):
        return x.reshape(x.shape[0], self.c, self.t)

    def backward(self, g):
        return g.reshape(g.shape[0], -1)


def _build(spec, rng):
    kind, *a = spec
    if kind == "conv":
        return Conv1D(*a, rng=rng)
    if kind == "dense":
        return Dense(*a, rng=rng)
    if kind == "unflatten":
        return Unflatten(*a)
    return {"relu": ReLU, "tanh": Tanh, "pool": AvgPool1D, "up": Upsample1D, "flatten": Flatten}[kind]()


class Sequential:
    """layers: a list of specs, e.g. [["conv", 1, 8, 7], ["relu"], ["pool"], ["flatten"], ["dense", 400, 3]]."""

    def __init__(self, specs, seed=0):
        rng = np.random.default_rng(seed)
        self.specs = [list(s) for s in specs]
        self.layers = [_build(s, rng) for s in self.specs]

    def params(self):
        return [p for lay in self.layers for p in lay.params()]

    def forward(self, x):
        for lay in self.layers:
            x = lay.forward(x)
        return x

    def backward(self, g):
        for lay in reversed(self.layers):
            g = lay.backward(g)
        return g

    def grads(self):
        return [g for lay in self.layers for g in lay.grads()]

    def predict(self, x, batch=512):
        return np.concatenate([self.forward(x[k:k + batch]) for k in range(0, len(x), batch)])

    def loss_grads(self, x, y):
        """Mean over samples of the summed square error, and every parameter's gradient (dL/dp = 2 (p - y) / n at
        the output, then back through the stack)."""
        p = self.forward(x)
        n = len(x)
        loss = float(np.sum((p - y) ** 2) / n)
        self.backward(2.0 * (p - y) / n)
        return loss, self.grads()

    def loss(self, x, y, batch=512):
        return float(sum(np.sum((self.forward(x[k:k + batch]) - y[k:k + batch]) ** 2) for k in range(0, len(x), batch)) / len(x))

    def fit(self, x, y, xv, yv, epochs=200, batch=64, lr=1e-3, l2=0.0, patience=20, seed=0, log=None, max_norm=5.0):
        """Adam on shuffled minibatches (global gradient norm clipped at max_norm); keeps the parameters of the best
        validation loss and stops after `patience` epochs without improvement. Returns [(epoch, train, val)]."""
        rng = np.random.default_rng(seed)
        par = self.params()
        opt = Adam(par, lr=lr)
        best, best_par, wait, hist = np.inf, None, 0, []
        for ep in range(epochs):
            idx = rng.permutation(len(x))
            tl = 0.0
            for k in range(0, len(x), batch):
                j = idx[k:k + batch]
                loss, g = self.loss_grads(x[j], y[j])
                tl += loss * len(j)
                if l2:
                    g = [gi + l2 * p if p.ndim > 1 else gi for gi, p in zip(g, par)]
                opt.step(g, max_norm)
            vl = self.loss(xv, yv)
            hist.append((ep, tl / len(x), vl))
            if log:
                log(f"epoch {ep}: train {tl / len(x):.5f}, val {vl:.5f}")
            if vl < best - 1e-9:
                best, wait, best_par = vl, 0, [p.copy() for p in par]
            else:
                wait += 1
                if wait >= patience:
                    break
        if best_par is None:
            raise FloatingPointError("Sequential.fit: no finite validation loss (non-finite inputs or divergence)")
        for p, b in zip(par, best_par):
            p[...] = b
        return hist

    def save(self, path, **extra):
        np.savez(path, specs=json.dumps(self.specs), **{f"p{i}": p for i, p in enumerate(self.params())}, **extra)

    @classmethod
    def load(cls, path):
        z = np.load(path, allow_pickle=False)
        net = cls(json.loads(str(z["specs"])))
        for i, p in enumerate(net.params()):
            p[...] = z[f"p{i}"]
        return net, z
