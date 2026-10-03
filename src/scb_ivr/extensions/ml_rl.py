"""Reinforcement learning in D63's environment (extension ml_design_assist, A122): an agent chooses phase 1's turn-off
rule each period - the timed edge, the comparator at the target, or the floor - after a disturbance.

Environment (Env): D63's ValleyMap at one design, from its steady state; one step is one phase-1 period, with the
agent's rule (ValleyMap.period(rule=...)). Episodes: a disturbance at the first period (a load step or an input
step over a slew), then `horizon` periods.
Observation: only what the RTL measures - Vo's error (the ADC, in units of 10 mV), Ton's deviation from its steady
value and its change over the last period (units of 5 ns), phase 1's last turn-off current against the target (the
crossing report, units of 5 A) - and a constant.
Reward per period: -( e_vo^2 / 10 + max(0, peak - 200 A) / 5 + phase 1's crossing depth / 5 + the slots' crossing
depth / 20 ), and -50 and the end of the episode if the map diverges.
Policy: a linear softmax over the 3 rules (Policy); training by REINFORCE (policy gradient) with a per-time baseline
and an entropy bonus (train). Fixed rules for comparison: always "timed", "cmp" or "floor".
"""
from __future__ import annotations

import copy
import math
from dataclasses import replace

import numpy as np

from scb_ivr.p24_valley_map import DIVERGED_A, Design, ValleyMap, steady_ton

RULES = ("timed", "cmp", "floor")


class Env:
    def __init__(self, d: Design, horizon=150):
        self.d, self.horizon = replace(d, mode="floor"), horizon
        self.m = ValleyMap(self.d)
        mw = ValleyMap(replace(d, mode="cmp"))
        s = mw.init_state(steady_ton(d))
        for _ in range(600):
            mw.period(s, d.vin, 0.0)
        for _ in range(200):                              # learn dlo in the timed design, as the RTL does
            self.m.period(s, d.vin, 0.0, rule="timed")
        self.s0 = s
        self.ton_ss = s["ton_ph1"]

    def reset(self, dist):
        """dist: ("load", di_a) or ("line", dv_v, slew_us)."""
        self.s = copy.deepcopy(self.s0)
        self.s["t"] = 0.0
        self.dist, self.k, self.last = dist, 0, None
        self.ton_prev = self.ton_ss
        return self.obs()

    def obs(self):
        s = self.s
        ton = s["ton_ph1"]
        o = np.array([(s["vo"] - self.d.vref) / 0.01, (ton - self.ton_ss) / 5e-9, (ton - self.ton_prev) / 5e-9,
                      (s["valley"][0] - self.d.i_tgt) / 5.0, 1.0])
        return np.clip(o, -10, 10)

    def step(self, a):
        d, s = self.d, self.s
        if self.dist[0] == "load":
            vin, i_step = d.vin, self.dist[1]
        else:
            vin, i_step = d.vin + self.dist[1] * min(s["t"] / (self.dist[2] * 1e-6), 1.0), 0.0
        self.ton_prev = s["ton_ph1"]
        rec = self.m.period(s, vin, i_step, rule=RULES[a])
        self.k += 1
        bad = not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in rec["valley"] + rec["peak"])
        if bad:
            return self.obs(), -50.0, True, rec
        e = (rec["vo"] - d.vref) / 0.01
        r = -(e * e / 10.0 + max(0.0, max(rec["peak"]) - 200.0) / 5.0 + rec["depth"][0] / 5.0 + sum(rec["depth"][1:]) / 20.0)
        return self.obs(), r, self.k >= self.horizon, rec


class Policy:
    def __init__(self, n_obs=5, n_act=3, seed=0):
        self.W = np.random.default_rng(seed).normal(0, 0.01, (n_act, n_obs))

    def probs(self, o):
        z = self.W @ o
        z -= z.max()
        p = np.exp(z)
        return p / p.sum()

    def act(self, o, rng=None):
        p = self.probs(o)
        return int(rng.choice(len(p), p=p)) if rng is not None else int(np.argmax(p))


def rollout(env, dist, chooser):
    """chooser(obs) -> action. Returns (total reward, actions, observations, rewards, records)."""
    o = env.reset(dist)
    obs, acts, rews, recs = [], [], [], []
    done = False
    while not done:
        a = chooser(o)
        obs.append(o); acts.append(a)
        o, r, done, rec = env.step(a)
        rews.append(r); recs.append(rec)
    return float(sum(rews)), acts, obs, rews, recs


def sample_dist(rng):
    if rng.random() < 0.3:
        return ("load", float(rng.choice([-62.5, 62.5])))
    return ("line", float(rng.choice([-4.8, 4.8])), float(np.exp(rng.uniform(0, np.log(20)))))


def train(env, iters=150, batch=16, lr=0.05, gamma=0.98, ent=0.01, seed=0, log=None):
    """REINFORCE: per batch, returns-to-go G_t (discount gamma), a per-time baseline (the batch mean of G_t), and the
    gradient of sum_t (G_t - b_t) log pi(a_t | o_t) + ent * entropy, normalised by the batch's advantage sd."""
    rng = np.random.default_rng(seed)
    pol = Policy(seed=seed)
    hist = []
    for it in range(iters):
        eps = [rollout(env, sample_dist(rng), lambda o: pol.act(o, rng)) for _ in range(batch)]
        T = max(len(e[1]) for e in eps)
        G = np.zeros((batch, T)); mask = np.zeros((batch, T))
        for b, (_, acts, obs, rews, _) in enumerate(eps):
            g = 0.0
            for t in range(len(rews) - 1, -1, -1):
                g = rews[t] + gamma * g
                G[b, t] = g; mask[b, t] = 1.0
        base = (G * mask).sum(axis=0) / np.maximum(mask.sum(axis=0), 1)
        adv = (G - base) * mask
        sd = adv[mask > 0].std() + 1e-8
        grad = np.zeros_like(pol.W)
        for b, (_, acts, obs, rews, _) in enumerate(eps):
            for t, (o, a) in enumerate(zip(obs, acts)):
                p = pol.probs(o)
                g_log = -np.outer(p, o); g_log[a] += o          # d log softmax / dW
                h = -np.sum(p * np.log(p + 1e-12))
                g_ent = -np.outer(p * (np.log(p + 1e-12) + h), o)   # d entropy / dW
                grad += (adv[b, t] / sd) * g_log + ent * g_ent
        pol.W += lr * grad / batch
        mean_r = float(np.mean([e[0] for e in eps]))
        hist.append(mean_r)
        if log and it % 10 == 0:
            log(f"iteration {it}: mean return {mean_r:.1f}")
    return pol, hist
