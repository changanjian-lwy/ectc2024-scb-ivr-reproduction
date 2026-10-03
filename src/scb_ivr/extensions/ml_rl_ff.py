"""A126: D63's environment for a per-phase Ton feed-forward after line and load steps, at A124's 2.5 MHz design.

Plant: D63's ValleyMap at A124's design (L 2.933 nH, Cs 6 uF, 12.5%, the floor, D59's 100 kHz loop); one step is one
phase-1 period, and the action scales each phase's Ton after the loop (ValleyMap.period(ton_scale=...)).
Episodes: a steady state for Cs x one of CS_FACTORS (domain randomisation, warmed as A124's prediction is), then a
disturbance from period ONSET: a rising or falling line step (a ramp), a load step, or none; `horizon` periods.
Observations (the sensor set):
- "rtl": the controller's own signals - Vo's error (ADC, per 10 mV), Ton's deviation from its steady value and its
  change over the last period (per 5 ns), phase 1's last turn-off current against the target (per 5 A), a constant;
- "vin": + the input voltage sampled once per period: Vin - 48 V (per 4.8 V), its change over the period (per 0.5 V),
  and Vin minus its low-passes with 2, 8 and 32 us (per 2 V) - a hardware addition (P24 has no Vin sensing);
- "rails": + each rail's deviation from Vin / 4 (per 2 V) - sensing the series capacitors too.
Action: a in R^4, scale_k = clip(1 + 0.25 a_k, 0.5, 1.25).
Reward per period: -( e^2 / 10 (e = Vo error per 10 mV) + x / 2 + x^2 / 50 (x = max(0, largest peak - I_LIM)) +
0.02 sum_k |rail_k - Vin / 4| (V) + sum_k (scale_k - 1)^2 ); -200 and the end if the map diverges.
I_LIM = 178 A = 200 A / 1.125: A125's 80% band for D63's peak on rising line steps, so a D63 peak at I_LIM is a
co-simulated peak <= 200 A at that level.
Fixed laws for comparison (step_law): no feed-forward; phase 1's Ton capped at the Ton that reaches I_CAP from 0 A at
its rail, the rail from the rails themselves (oracle) or from Vin alone (V_1 ~ 3/4 of Vin's low-pass, tau 20 us).
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.p24_valley_map import DIVERGED_A, Design, ValleyMap, steady_ton

CS_FACTORS = (0.8, 0.9, 1.0, 1.1, 1.2)
ONSET = 4
I_LIM = 200.0 / 1.125
I_CAP = 180.0
TAUS = (2e-6, 8e-6, 32e-6)
SENSORS = {"rtl": 5, "vin": 10, "rails": 14}


def design(cfg_path, cs=6e-6):
    """A124's design (D63), with its thresholds and transition times from the cached file (setup_a126.py)."""
    c = json.loads(Path(cfg_path).read_text())
    return Design(lf=c["lf"], cs=cs, i_tgt=c["i_tgt"], mode="floor", floor_a=2.0, kp_ns=c["kp_ns"], ki_ns=c["ki_ns"],
                  ton_cfg_ns=35.5, smax=64, rs_low_ns=800.0, t_tr=tuple(c["t_tr"]), ith=tuple(tuple(x) for x in c["ith"]))


def warm(d: Design):
    mw = ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(steady_ton(d))
    for _ in range(600):
        mw.period(s, d.vin, 0.0)
    m = ValleyMap(d)
    for _ in range(200):
        m.period(s, d.vin, 0.0)
    s["t"] = 0.0
    return m, s


def rails_of(s, vin):
    vc = s["vc"]
    return [vin - vc[0]] + [vc[j - 1] - vc[j] for j in range(1, len(vc))] + [vc[-1]]


def sample_dist(rng):
    u = rng.random()
    if u < 0.35:
        return ("line", float(rng.uniform(2.0, 6.0)), float(np.exp(rng.uniform(np.log(0.5), np.log(20.0)))))
    if u < 0.7:
        return ("line", -float(rng.uniform(2.0, 9.0)), float(np.exp(rng.uniform(np.log(0.5), np.log(20.0)))))
    if u < 0.9:
        return ("load", float(rng.choice([-1, 1]) * rng.uniform(20.0, 62.5)))
    return ("none",)


class Env:
    def __init__(self, cfg_path, sensors="vin", horizon=120):
        self.sensors, self.horizon = sensors, horizon
        self.n_obs = SENSORS[sensors]
        self.warm = {}
        for f in CS_FACTORS:
            d = design(cfg_path, 6e-6 * f)
            m, s = warm(d)
            self.warm[f] = (d, m, s)
        self.fixed = None

    def reset(self, rng=None, dist=None, cs_factor=None):
        if cs_factor is None:
            cs_factor = float(rng.choice(CS_FACTORS)) if rng is not None else 1.0
        self.dist = dist if dist is not None else sample_dist(rng)
        self.d, self.m, s0 = self.warm[cs_factor]
        self.s = copy.deepcopy(s0)
        self.s["t"] = 0.0
        self.k = 0
        self.ton_ss = s0["ton_ph1"]
        self.ton_prev = self.ton_ss
        self.vin = self.vin_prev = self.d.vin
        self.lp = [self.d.vin] * len(TAUS)
        self.t_on = None
        self.recs = []
        return self.obs()

    def vin_at(self, t):
        if self.dist[0] != "line" or self.t_on is None:
            return self.d.vin
        return self.d.vin + self.dist[1] * min(max((t - self.t_on) / (self.dist[2] * 1e-6), 0.0), 1.0)

    def obs(self):
        s, d = self.s, self.d
        o = [(s["vo"] - d.vref) / 0.01, (s["ton_ph1"] - self.ton_ss) / 5e-9, (s["ton_ph1"] - self.ton_prev) / 5e-9,
             (s["valley"][0] - d.i_tgt) / 5.0, 1.0]
        if self.sensors in ("vin", "rails"):
            o += [(self.vin - 48.0) / 4.8, (self.vin - self.vin_prev) / 0.5] + [(self.vin - x) / 2.0 for x in self.lp]
        if self.sensors == "rails":
            o += [(r - self.vin / 4) / 2.0 for r in rails_of(s, self.vin)]
        return np.clip(np.array(o), -10.0, 10.0)

    def _advance(self, scale=None, cap=None):
        s, d = self.s, self.d
        if self.k == ONSET:
            self.t_on = s["t"]
        vin = self.vin_at(s["t"])
        i_step = self.dist[1] if self.dist[0] == "load" and self.k >= ONSET else 0.0
        self.ton_prev = s["ton_ph1"]
        rec = self.m.period(s, vin, i_step, ton_scale=scale, ton_cap=cap)
        rec["vin"] = vin
        self.recs.append(rec)
        self.k += 1
        self.vin_prev, self.vin = self.vin, self.vin_at(s["t"])
        for j, tau in enumerate(TAUS):
            self.lp[j] += (self.vin - self.lp[j]) * (1.0 - math.exp(-rec["period"] / tau))
        bad = not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in rec["valley"] + rec["peak"])
        if bad:
            return self.obs(), -200.0, True, {"terminal": True, "rec": rec}
        e = (rec["vo"] - d.vref) / 0.01
        x = max(0.0, max(rec["peak"]) - I_LIM)
        lad = sum(abs(r - vin / 4) for r in rec["rails"])
        act = sum((f - 1.0) ** 2 for f in scale) if scale is not None else 0.0
        r = -(e * e / 10.0 + x / 2.0 + x * x / 50.0 + 0.02 * lad + act)
        return self.obs(), r, self.k >= self.horizon, {"terminal": False, "rec": rec}

    def step(self, a):
        scale = [float(min(max(1.0 + 0.25 * v, 0.5), 1.25)) for v in a]
        return self._advance(scale=scale)

    def step_law(self, law):
        """law(env) -> (scale or None, cap or None)."""
        scale, cap = law(self)
        return self._advance(scale=scale, cap=cap)


def law_none(env):
    return None, None


def law_cap_rails(env):
    """Phase 1's Ton capped at L I_CAP / (V_rail,1 - Vo), the rail known (oracle)."""
    r1 = rails_of(env.s, env.vin)[0]
    return None, [env.d.lf * I_CAP / max(r1 - env.s["vo"], 1e-3), math.inf, math.inf, math.inf]


def law_cap_vin(env, tau_index=None):
    """The same with the rail estimated from Vin alone: V_rail,1 ~ Vin - 3/4 (Vin's low-pass, tau ~20 us)."""
    if not hasattr(env, "_lp20") or env.k == 0:
        env._lp20 = env.d.vin
    T = env.recs[-1]["period"] if env.recs else 0.5e-6
    env._lp20 += (env.vin - env._lp20) * (1.0 - math.exp(-T / 20e-6))
    r1 = env.vin - 0.75 * env._lp20
    return None, [env.d.lf * I_CAP / max(r1 - env.s["vo"], 1e-3), math.inf, math.inf, math.inf]


LAWS = {"none": law_none, "cap_vin": law_cap_vin, "cap_rails": law_cap_rails}


def episode(env, chooser, dist, cs_factor=1.0):
    """chooser: ("law", law) or ("policy", fn(obs) -> action). Returns (return, records, diverged)."""
    o = env.reset(dist=dist, cs_factor=cs_factor)
    total, done, info = 0.0, False, {}
    while not done:
        if chooser[0] == "law":
            o, r, done, info = env.step_law(chooser[1])
        else:
            o, r, done, info = env.step(chooser[1](o))
        total += r
    return total, env.recs, bool(info.get("terminal"))


def summarise(recs):
    a = recs[ONSET:]
    vo = np.array([r["vo"] for r in a])
    i = int(np.argmax(np.abs(vo - 1.0)))
    return {"peaks_a": [max(r["peak"][k] for r in a) for k in range(4)], "peak_a": max(max(r["peak"]) for r in a),
            "extreme_mv": float((vo[i] - 1.0) * 1e3),
            "ladder_max_v": max(max(abs(x - r["vin"] / 4) for x in r["rails"]) for r in a)}


A124_ROWS = {"p125_l_p48_1us": ("line", 4.8, 1.0), "p125_l_p48_5us": ("line", 4.8, 5.0), "p125_l_m48_1us": ("line", -4.8, 1.0),
             "p125_l_m48_5us": ("line", -4.8, 5.0), "p125_l_m80_10us": ("line", -8.0, 10.0), "p125_s_p62": ("load", 62.5),
             "p125_s_m62": ("load", -62.5)}
