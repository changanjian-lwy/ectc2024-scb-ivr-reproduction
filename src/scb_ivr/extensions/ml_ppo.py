"""Proximal policy optimisation (PPO; Schulman et al. 2017) in numpy (extension ml_design_assist, A126): an
actor-critic for continuous actions.

Actor: an MLP (ml_nn.MLP: tanh hidden layers, linear output) gives the mean mu(o) of a Gaussian over the action
vector; the log standard deviation is one learned number per action, independent of the state. Critic: a second MLP
gives the value V(o).
Environment interface: reset(rng) -> o; step(a) -> (o, r, done, info), info["terminal"] True when the episode ended
in a failure (no value after it) rather than at the horizon (bootstrapped with V).
Advantages: generalised advantage estimation (GAE; Schulman et al. 2016), delta_t = r_t + gamma V(o_t+1) - V(o_t),
A_t = sum_l (gamma lambda)^l delta_t+l; the critic's targets are R_t = A_t + V(o_t).
Update: `epochs` passes over shuffled minibatches of the clipped surrogate
    L = -mean(min(rho A, clip(rho, 1 - eps, 1 + eps) A)) - ent H,   rho = pi_new(a | o) / pi_old(a | o),
with the gradients written out: d log pi / d mu = (a - mu) / sigma^2, d log pi / d log sigma = ((a - mu) / sigma)^2
- 1, dL / d log pi = -rho A / n where the unclipped term is the minimum (else 0), dH / d log sigma = 1. The critic
minimises the mean of (V - R)^2. A pass stops early when the approximate KL divergence exceeds kl_stop.
Anchored residual policy (A127): with anchor(O) (the observations with their transient features zeroed), the mean is
mu(o) = net(o) - net(anchor(o)), so the action is exactly zero wherever the transient features are; the gradient
backpropagates through both evaluations (+delta and -delta).
"""
from __future__ import annotations

import math

import numpy as np

from scb_ivr.extensions.ml_nn import MLP, Adam


class GaussianPolicy:
    def __init__(self, n_obs, n_act, hidden=(64, 64), log_std=-1.0, seed=0, anchor=None):
        self.net = MLP([n_obs, *hidden, n_act], seed=seed)
        self.net.W[-1] *= 0.01                      # start near the zero action
        self.log_std = np.full(n_act, float(log_std))
        self.anchor = anchor

    def forward(self, O):
        """(mean, cache) for a batch of observations."""
        acts = self.net.forward(O)
        if self.anchor is None:
            return acts[-1], (acts, None)
        acts0 = self.net.forward(self.anchor(O))
        return acts[-1] - acts0[-1], (acts, acts0)

    def backward(self, cache, d_mu):
        acts, acts0 = cache
        gW, gb = self.net.backward(acts, d_mu)
        if acts0 is not None:
            gW0, gb0 = self.net.backward(acts0, -d_mu)
            gW = [a + b for a, b in zip(gW, gW0)]
            gb = [a + b for a, b in zip(gb, gb0)]
        return gW, gb

    def mean(self, o):
        return self.forward(np.atleast_2d(o))[0]

    def logp(self, a, mu):
        z = (a - mu) / np.exp(self.log_std)
        return -0.5 * np.sum(z * z, axis=-1) - np.sum(self.log_std) - 0.5 * len(self.log_std) * math.log(2 * math.pi)

    def sample(self, o, rng):
        mu = self.mean(o)[0]
        a = mu + np.exp(self.log_std) * rng.normal(size=mu.shape)
        return a, float(self.logp(a, mu))

    def params(self):
        return self.net.W + self.net.b + [self.log_std]


def collect(env, pol, critic, n_episodes, rng, gamma=0.99, lam=0.95):
    """n_episodes rollouts with the stochastic policy. Returns arrays O, A, logp, advantages, returns and the
    episodes' total rewards."""
    O, A, LP, ADV, RET, totals = [], [], [], [], [], []
    for _ in range(n_episodes):
        o = env.reset(rng)
        obs, acts, lps, rews = [], [], [], []
        done, info = False, {}
        while not done:
            a, lp = pol.sample(o, rng)
            obs.append(o); acts.append(a); lps.append(lp)
            o, r, done, info = env.step(a)
            rews.append(r)
        v = critic.predict(np.array(obs))[:, 0]
        v_last = 0.0 if info.get("terminal") else float(critic.predict(np.atleast_2d(o))[0, 0])
        adv = np.zeros(len(rews))
        g = 0.0
        for t in range(len(rews) - 1, -1, -1):
            v_next = v[t + 1] if t + 1 < len(rews) else v_last
            g = rews[t] + gamma * v_next - v[t] + gamma * lam * g
            adv[t] = g
        O += obs; A += acts; LP += lps; ADV += adv.tolist(); RET += (adv + v).tolist(); totals.append(float(sum(rews)))
    return np.array(O), np.array(A), np.array(LP), np.array(ADV), np.array(RET), totals


def update(pol, critic, opt_pi, opt_v, batch, rng, epochs=10, mb=256, clip=0.2, ent=0.0, kl_stop=0.03, max_norm=0.5):
    O, A, LP0, ADV, RET = batch
    ADV = (ADV - ADV.mean()) / (ADV.std() + 1e-8)
    n = len(O)
    sd = None
    for _ in range(epochs):
        idx = rng.permutation(n)
        for k in range(0, n, mb):
            j = idx[k:k + mb]
            mu, cache = pol.forward(O[j])
            sd = np.exp(pol.log_std)
            lp = pol.logp(A[j], mu)
            rho = np.exp(lp - LP0[j])
            use = rho * ADV[j] <= np.clip(rho, 1 - clip, 1 + clip) * ADV[j]
            d_lp = -np.where(use, rho * ADV[j], 0.0) / len(j)
            gW, gb = pol.backward(cache, d_lp[:, None] * (A[j] - mu) / sd ** 2)
            g_ls = np.sum(d_lp[:, None] * (((A[j] - mu) / sd) ** 2 - 1.0), axis=0) - ent
            opt_pi.step(gW + gb + [g_ls], max_norm=max_norm)
            ca = critic.forward(O[j])
            gW, gb = critic.backward(ca, 2.0 * (ca[-1] - RET[j][:, None]) / len(j))
            opt_v.step(gW + gb, max_norm=max_norm)
        kl = float(np.mean(LP0 - pol.logp(A, pol.mean(O))))
        if kl > kl_stop:
            break
    return {"kl": kl, "std": np.exp(pol.log_std).tolist()}


def train(env, n_obs, n_act, iters=200, episodes=32, lr=3e-4, gamma=0.99, lam=0.95, log_std=-1.0, hidden=(64, 64), seed=0,
          log=None, anchor=None, **kw):
    """PPO from scratch. Returns (policy, critic, history of mean episode returns)."""
    rng = np.random.default_rng(seed)
    pol = GaussianPolicy(n_obs, n_act, hidden, log_std, seed, anchor)
    critic = MLP([n_obs, *hidden, 1], seed=seed + 1)
    opt_pi, opt_v = Adam(pol.params(), lr), Adam(critic.W + critic.b, lr)
    hist = []
    for it in range(iters):
        *batch, totals = collect(env, pol, critic, episodes, rng, gamma, lam)
        info = update(pol, critic, opt_pi, opt_v, batch, rng, **kw)
        hist.append(float(np.mean(totals)))
        if log and (it % 10 == 0 or it == iters - 1):
            log(f"iteration {it}: mean return {hist[-1]:.2f}, kl {info['kl']:.4f}, std " + " ".join(f"{s:.3f}" for s in info["std"]))
    return pol, critic, hist
