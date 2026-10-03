"""A small multilayer perceptron in numpy (extension ml_design_assist): tanh hidden layers, a linear (regression) or
sigmoid (classification) output, trained with Adam on minibatches with early stopping on a validation set.

Written out in full so every step can be read: the forward pass keeps each layer's activation, the backward pass
applies the chain rule layer by layer (for tanh, d tanh(z)/dz = 1 - tanh(z)^2), Adam keeps running first and second
moments of each gradient. Inputs and targets are standardised with the training set's mean and sd (Scaler).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Scaler:
    mean: np.ndarray
    sd: np.ndarray

    @classmethod
    def fit(cls, x):
        sd = x.std(axis=0)
        return cls(x.mean(axis=0), np.where(sd > 0, sd, 1.0))

    def fwd(self, x):
        return (x - self.mean) / self.sd

    def inv(self, z):
        return z * self.sd + self.mean


class MLP:
    def __init__(self, sizes, out="linear", seed=0):
        """sizes: [n_in, hidden..., n_out]; out: "linear" (mean-square loss) or "sigmoid" (cross-entropy loss)."""
        rng = np.random.default_rng(seed)
        self.out = out
        self.W = [rng.normal(0.0, np.sqrt(1.0 / a), (a, b)) for a, b in zip(sizes[:-1], sizes[1:])]   # LeCun init
        self.b = [np.zeros(b) for b in sizes[1:]]

    # ---- forward / backward ----
    def forward(self, x):
        acts = [x]
        for i, (w, b) in enumerate(zip(self.W, self.b)):
            z = acts[-1] @ w + b
            if i < len(self.W) - 1:
                acts.append(np.tanh(z))
            else:
                acts.append(1.0 / (1.0 + np.exp(-z)) if self.out == "sigmoid" else z)
        return acts

    def predict(self, x):
        return self.forward(x)[-1]

    def loss_grads(self, x, y, weight=None):
        """Mean loss and the gradients of every W, b. For the sigmoid output with cross-entropy, and for the linear
        output with the mean square, dL/dz at the output is (prediction - target) / n."""
        acts = self.forward(x)
        p = acts[-1]
        n = len(x)
        w = np.ones((n, 1)) if weight is None else weight.reshape(-1, 1)
        if self.out == "sigmoid":                                        # summed over outputs, averaged over samples
            eps = 1e-12
            loss = float(-np.sum(w * (y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))) / n)
        else:
            loss = float(np.sum(w * (p - y) ** 2) / n)
        delta = w * (p - y) / n * (1.0 if self.out == "sigmoid" else 2.0)
        gW, gb = [None] * len(self.W), [None] * len(self.W)
        for i in range(len(self.W) - 1, -1, -1):
            gW[i] = acts[i].T @ delta
            gb[i] = delta.sum(axis=0)
            if i > 0:
                delta = (delta @ self.W[i].T) * (1.0 - acts[i] ** 2)     # back through tanh
        return loss, gW, gb

    # ---- training ----
    def fit(self, x, y, xv, yv, epochs=400, batch=128, lr=2e-3, l2=1e-5, patience=40, seed=0, weight=None, log=None):
        """Adam (beta 0.9 / 0.999) on shuffled minibatches; keeps the weights of the best validation loss and stops
        after `patience` epochs without improvement. Returns the history [(epoch, train loss, val loss)]."""
        rng = np.random.default_rng(seed)
        m = [np.zeros_like(a) for a in self.W + self.b]
        v = [np.zeros_like(a) for a in self.W + self.b]
        b1, b2, step = 0.9, 0.999, 0
        best, best_par, wait, hist = np.inf, None, 0, []
        for ep in range(epochs):
            idx = rng.permutation(len(x))
            tl = 0.0
            for k in range(0, len(x), batch):
                j = idx[k:k + batch]
                loss, gW, gb = self.loss_grads(x[j], y[j], None if weight is None else weight[j])
                tl += loss * len(j)
                grads = [g + l2 * w for g, w in zip(gW, self.W)] + gb
                step += 1
                for t, (par, g) in enumerate(zip(self.W + self.b, grads)):
                    m[t] = b1 * m[t] + (1 - b1) * g
                    v[t] = b2 * v[t] + (1 - b2) * g * g
                    par -= lr * (m[t] / (1 - b1 ** step)) / (np.sqrt(v[t] / (1 - b2 ** step)) + 1e-8)
            vl = self.loss_grads(xv, yv)[0]
            hist.append((ep, tl / len(x), vl))
            if log and ep % 50 == 0:
                log(f"epoch {ep}: train {tl / len(x):.5f}, val {vl:.5f}")
            if vl < best - 1e-7:
                best, wait = vl, 0
                best_par = [a.copy() for a in self.W + self.b]
            else:
                wait += 1
                if wait >= patience:
                    break
        k = len(self.W)
        self.W, self.b = best_par[:k], best_par[k:]
        return hist

    def save(self, path, **extra):
        np.savez(path, n=len(self.W), out=self.out, **{f"W{i}": w for i, w in enumerate(self.W)},
                 **{f"b{i}": b for i, b in enumerate(self.b)}, **extra)

    @classmethod
    def load(cls, path):
        z = np.load(path, allow_pickle=False)
        n = int(z["n"])
        m = cls.__new__(cls)
        m.out = str(z["out"])
        m.W = [z[f"W{i}"] for i in range(n)]
        m.b = [z[f"b{i}"] for i in range(n)]
        return m, z
