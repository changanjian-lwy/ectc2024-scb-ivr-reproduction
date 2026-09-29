"""A78 - A76's simulator plus a per-section record of each phase's integral of i^2 dt (diagnostic only;
conduction-loss accounting for the negative-current target sweep, BOUNDARY.md).

A76 docstring follows.
A76 - A75's simulator plus three control-rule options (BOUNDARY.md), all off by default:
- trim_gain: per-phase current-comparator thresholds, self-trimmed at each comparator-decided
  low-side turn-off edge (Schaef et al. ISSCC 2019);
- qualify_current: phases 2..N turn their low side off only when the timed slot has passed AND
  their own current is below the threshold (P25 Sec. II; UCC28063A);
- zvs_reactive False: in predictive mode ZVS is left to the timed prediction (Chiang 2009).

A75 docstring follows.
A75 - A74's simulator plus controller latency and a predictive valley turn-on (BOUNDARY.md).

Copied from A74 (a74_transient.py, unmodified there). New, off by default (mode P only):
- t_d: latency from a comparator decision to the gate edge (ZVS low-on, phase-1 current
  target, high-side ZVS and valley). Timer-generated edges are taken as pre-compensated;
- valley_mode "predictive": the high side turns on at t_lo + dt_pred[k], a timed edge
  (Chiang 2009's predictive turn-on / adaptive dead time); dt_pred starts at half the
  node resonance period and is corrected every cycle: +dt_step if the node was still
  falling at turn-on (early), else set to the observed valley time (late).

A74 docstring follows.
A74 - A73's simulator plus mode-P phase shifts that follow the measured period (BOUNDARY.md).

Copied from A73 (a73_transient.py, unmodified there). New, off by default:
- adaptive_shift: in mode P, phase k's low side turns off at t_ref + (k-1)*T_meas/N,
  T_meas = the last phase-1 period, clamped to [0.5, 3]*T0;
- a log of every high-side turn-on (mechanism, Vds at turn-on); it does not change the dynamics.

A73 docstring follows.
A73 - A72's simulator plus the published ladder-control start-up methods (BOUNDARY.md).

Copied from A72 (a72_transient.py, unmodified there). New options, all off by default:
- init_ladder: start from a precharged ladder (Wei et al. JSSC 2021 end state), Vin held;
- t_ss: mode-S Ton ramped from 0 over t_ss (Kim et al. TPEL 2018 soft start);
- k_b: mode-S high-state duration modulated by the sensed switching-node voltage
  (Xia & Stauth JSSC 2022 balancing sliding mode, transferred to the SCB).

A72 docstring follows.
A72 - A71's zero-start simulator generalised to N phases and a resistive load.

A71 (a71_transient.py, unmodified there) is the N = 3, constant-current special
case; the regression gate (BOUNDARY Section 4) checks that. Node, switch and
capacitor orderings follow A71 so that N = 3 reproduces it.

    vin-SH1-a1-SH2-a2-...-a(N-1)-SHN-xN,  SLk: xk-0,  Csk: ak-xk (k < N),  Lk: xk-out
    [Cm 0; 0 L] d/dt [v; i] = [[-G, -B], [B^T, -R]] [v; i] + f(t)
    v = (a1..a(N-1), x1..xN, out), i = (i1..iN) (xk -> out)
Modes as in A71: S (fixed timing, fixed dead time) from t = 0, P (D41 single-sensor
rule + Chiang valley fallback) from the first phase-1 high-side turn-on at or
after t_hand.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.linalg import lu_factor, lu_solve

HERE = Path(__file__).resolve().parent
# A71's P25-scale three-phase circuit (A69/A70 values, 4.9 mOhm, CC 67.5 A, T0 2 us, 20 ns dead time)
P25_PRESET = dict(n=3, vin=12.0, L=30e-9, R=4.9e-3, c_high=0.69e-9, c_low=1.38e-9, cs=100e-6, co=100e-6,
                  load_kind="cc", i_load=67.5, ton=500e-9, i_target=-2.5, t0=2e-6, t_dead=20e-9)


@dataclass
class Params:
    n: int = 4
    vin: float = 48.0
    L: float = 1.4666667e-9
    R: float = 0.54e-3
    c_high: float = 2 * 1860e-12
    c_low: float = 3 * 1860e-12
    cs: float = 3e-6
    co: float = 4.672e-3
    load_kind: str = "r"        # "r": resistive r_load; "cc": constant current i_load
    r_load: float = 4e-3
    i_load: float = 250.0
    ton: float = 16.667e-9
    i_target: float = -2.5
    t0: float = 200e-9
    t_dead: float = 2.15e-9
    g_on: float = 1e7
    h: float = 10e-12
    v_hys: float = 0.05
    t_ramp: float = 68.61e-6
    t_load: float = 88.61e-6
    t_hand: float = 88.61e-6
    t_end: float = 388.61e-6
    shifts: tuple = ()
    level_events: bool = False   # BOUNDARY 9: a condition already met fires at once (comparator), not only on a crossing
    t_restart_high: float = 0.0  # BOUNDARY 9: mode P restart timer on the UP/DOWN waits (0 = off)
    t_restart_low: float = 0.0   # BOUNDARY 9: mode P restart timer on phase 1's current-target wait (0 = off)
    init_ladder: tuple = ()       # A73: flying-capacitor voltages at t = 0 (V); () = all zero
    t_ss: float = 0.0             # A73: mode-S Ton ramp time (0 = off)
    k_b: float = 0.0              # A73: mode-S balancing gain (0 = off)
    k_b_vmin: float = 2.0         # A73: no balancing below this Vin
    diode_check: bool = False
    init_z: tuple = ()            # A73 BOUNDARY 10: N = 3 start from an A69 section (a2, x1, out, i1, i2, i3), SH1 on
    valley: bool = True           # A73 BOUNDARY 10: False = A69 controller (no valley path)     # A73 BOUNDARY 8: a diode may not carry drain->source current within a step
    stall_periods: float = 3.0   # STALLED if no phase-1 section for this many T0 (BOUNDARY 8: 20 for P24 runs)
    adaptive_shift: bool = False  # A74: mode-P shifts k*T_meas/N instead of k*T0/N
    t_meas_clamp: tuple = (0.5, 3.0)  # A74: T_meas limits in units of T0 (PROJECT_DECISION)
    t_d: float = 0.0                  # A75: comparator-to-gate latency (s), mode P
    valley_mode: str = "reactive"     # A75: "reactive" (A70 + latency) or "predictive" (timed valley)
    dt_step: float = 0.2e-9           # A75: predictive correction step when early (PROJECT_DECISION)
    trim_gain: float = 0.0            # A76: comparator self-trim gain per cycle (0 = off)
    trim_clamp: tuple = (-10.0, 30.0) # A76: theta_k limits relative to i_target (A)
    qualify_current: bool = False     # A76: phases 2..N low-off needs the slot AND i_k <= theta_k
    zvs_reactive: bool = True         # A76: False = no reactive ZVS decision in predictive mode

    def __post_init__(self):
        if not self.shifts:
            self.shifts = tuple((k * self.t0) / self.n for k in range(1, self.n))

    def vin_at(self, t):
        return self.vin * min(t / self.t_ramp, 1.0) if self.t_ramp > 0 else self.vin

    def ton_at(self, t):
        return self.ton * min(t / self.t_ss, 1.0) if self.t_ss > 0 else self.ton

    def load_at(self, t):
        return self.i_load if (self.load_kind == "cc" and t >= self.t_load) else 0.0


def topology(n):
    nodes = tuple(f"a{k}" for k in range(1, n)) + tuple(f"x{k}" for k in range(1, n + 1)) + ("out",)
    highs = [("SH1", "vin", "a1")] + [(f"SH{k}", f"a{k - 1}", f"a{k}") for k in range(2, n)] + [(f"SH{n}", f"a{n - 1}", f"x{n}")]
    lows = [(f"SL{k}", f"x{k}", None) for k in range(1, n + 1)]
    return nodes, tuple(highs + lows)


@dataclass
class Sim:
    p: Params
    cache: dict = field(default_factory=dict)

    def __post_init__(self):
        p = self.p
        self.nodes, self.switches = topology(p.n)
        self.idx = {nm: k for k, nm in enumerate(self.nodes)}
        nv = len(self.nodes); self.nv = nv
        caps = ([(p.c_high, d, s) for _, d, s in self.switches[:p.n]] + [(p.c_low, d, s) for _, d, s in self.switches[p.n:]]
                + [(p.cs, f"a{k}", f"x{k}") for k in range(1, p.n)] + [(p.co, "out", None)])
        cm = np.zeros((nv, nv))
        for c, a, b in caps:
            ia, ib = self.idx.get(a), self.idx.get(b)
            if ia is not None:
                cm[ia, ia] += c
            if ib is not None:
                cm[ib, ib] += c
            if ia is not None and ib is not None:
                cm[ia, ib] -= c; cm[ib, ia] -= c
        ns = nv + p.n
        self.M = np.zeros((ns, ns)); self.M[:nv, :nv] = cm; self.M[nv:, nv:] = p.L * np.eye(p.n)
        self.B = np.zeros((nv, p.n))
        for k in range(p.n):
            self.B[self.idx[f"x{k + 1}"], k] = 1.0; self.B[self.idx["out"], k] = -1.0

    def system(self, conducting, load_on):
        p = self.p; nv = self.nv
        G = np.zeros((nv, nv)); gv = np.zeros(nv)
        for on, (name, d, s) in zip(conducting, self.switches):
            if not on:
                continue
            g = p.g_on
            idd, iss = self.idx.get(d), self.idx.get(s)
            if d == "vin":
                G[iss, iss] += g; gv[iss] += g
                continue
            if idd is not None:
                G[idd, idd] += g
            if iss is not None:
                G[iss, iss] += g
            if idd is not None and iss is not None:
                G[idd, iss] -= g; G[iss, idd] -= g
        if load_on and p.load_kind == "r":
            G[self.idx["out"], self.idx["out"]] += 1.0 / p.r_load
        ns = nv + p.n
        A = np.zeros((ns, ns)); A[:nv, :nv] = -G; A[:nv, nv:] = -self.B; A[nv:, :nv] = self.B.T; A[nv:, nv:] = -p.R * np.eye(p.n)
        fv = np.zeros(ns); fv[:nv] = gv
        fl = np.zeros(ns); fl[self.idx["out"]] = -1.0
        return A, fv, fl

    def step(self, y, conducting, h, euler, t, load_on):
        key = (conducting, h, euler, load_on)
        entry = self.cache.get(key)
        if entry is None:
            A, fv, fl = self.system(conducting, load_on)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, fv, fl)
            if h == self.p.h:
                self.cache[key] = entry
        lu, rhs_m, fv, fl = entry
        p = self.p
        f1 = fv * p.vin_at(t + h) + fl * p.load_at(t + h)
        if euler:
            rhs = rhs_m @ y + h * f1
        else:
            f0 = fv * p.vin_at(t) + fl * p.load_at(t)
            rhs = rhs_m @ y + 0.5 * h * (f0 + f1)
        return lu_solve(lu, rhs)

    def vds(self, y, j, vin):
        name, d, s = self.switches[j]
        vd = vin if d == "vin" else y[self.idx[d]]
        vs = 0.0 if s is None else y[self.idx[s]]
        return vd - vs


def run(p: Params, log_every: int = 25, t_stop=None):
    sim = Sim(p); n = p.n; nv = sim.nv
    y = np.zeros(nv + n)
    if p.init_ladder:                  # phase 1 HIGH at t = 0: a1 = Vin, x1 = Vin - VC1; phases 2..N low: xk = 0, ak = VCk
        vin0 = p.vin_at(0.0)
        y[sim.idx["a1"]] = vin0; y[sim.idx["x1"]] = vin0 - p.init_ladder[0]
        for k in range(2, n):
            y[sim.idx[f"a{k}"]] = p.init_ladder[k - 1]
    if p.init_z:                       # A69's run(): y = (vin, a2, x1, 0, 0, out, i1, i2, i3), SH1 on, SL2/SL3 on
        a2, x1, out, i1, i2, i3 = p.init_z
        y[:] = [p.vin_at(0.0), a2, x1, 0.0, 0.0, out, i1, i2, i3]
    state = ["HIGH"] + ["LOW"] * (n - 1)
    t = 0.0; t_on = [0.0] + [None] * (n - 1); t_ref = 0.0; fired = [None] * n
    t_off = [None] * n; t_lo = [None] * n; t_lon = [None] * n
    restarts = []
    t_meas = [p.t0]; clamps = [0]; turnons = []   # A74: last phase-1 period; clamped periods; high-side turn-on log
    lowoffs = []                                  # A74 amendment 8: low-side turn-off log (diagnostic only)
    half_res = np.pi * np.sqrt(p.L * (p.c_high + p.c_low))  # A75: node half resonance period
    pending = [None] * n; t_vmin = [None] * n; v_lo = [None] * n; dt_pred = [half_res] * n   # A75
    pred_stats = {"early": 0, "late": 0}; latent = {"detections": 0}
    thr = [p.i_target] * n; trims = [0]                  # A76: comparator thresholds
    acc_i2 = [0.0] * n                                     # A78: integral of i_k^2 dt since the last section
    tau = [0.0] * n; ton_used = [0.0] * n; ton_last = [None] * n

    def bal_rate(yy, tt, k):
        vin = p.vin_at(tt)
        if p.k_b <= 0 or vin < p.k_b_vmin:
            return 1.0
        ref = vin / n
        return min(4.0, max(0.25, 1.0 - p.k_b * (yy[ix[k]] - ref) / ref))
    ctl = {"mode": "P" if p.t_hand <= 0 else "S", "t_hand_actual_s": 0.0 if p.t_hand <= 0 else None,
           "load_done": p.t_load <= 0, "ipk": 0.0}
    diode = [False] * (2 * n)
    euler_left = 2
    vmin = [None] * n
    vds_max = [0.0] * (2 * n)
    valley_events = []
    t0w = time.time()
    ia = [sim.idx[f"a{k}"] for k in range(1, n)]; ix = [sim.idx[f"x{k}"] for k in range(1, n + 1)]; io = sim.idx["out"]

    def record(y, t):
        vin = p.vin_at(t)
        return {"t_s": t, "v": [float(v) for v in y[:nv]], "i": [float(v) for v in y[nv:]], "vo": float(y[io]),
                "vin_v": vin, "vcs_v": [float(y[ia[k]] - y[ix[k]]) for k in range(n - 1)], "mode": ctl["mode"],
                "load_on": ctl["load_done"], "ipk_a": ctl["ipk"], "valley_count": len(valley_events),
                "ton_last_ns": [None if x is None else x * 1e9 for x in ton_last], "i2_int_a2s": list(acc_i2)}

    sections = [record(y, 0.0)]

    def gates():
        return [s == "HIGH" for s in state] + [s == "LOW" for s in state]

    def event_values(y, t):
        vin = p.vin_at(t)
        ev = {}
        if not ctl["load_done"]:
            ev[("load_on", -1)] = p.t_load - t
        S = ctl["mode"] == "S"
        for k in range(n):
            st = state[k]
            if not S and pending[k] is not None:   # A75: decision taken, gate edge after the latency
                ev[("pending", k)] = pending[k][1] - t
                continue
            if st == "HIGH":
                if S and p.k_b > 0:
                    tk = tau[k] if t == t_now[0] else tau[k] + (t - t_now[0]) * bal_rate(y, t, k)
                    ev[("off_high", k)] = ton_used[k] - tk
                    ev[("off_cap", k)] = (t_on[k] + 2 * ton_used[k]) - t
                else:
                    ev[("off_high", k)] = (t_on[k] + ton_used[k]) - t
            elif st == "DOWN":
                ev[("low_on", k)] = (t_off[k] + p.t_dead) - t if S else sim.vds(y, n + k, vin)
                if not S and p.t_restart_high > 0:
                    ev[("low_on_restart", k)] = (t_off[k] + p.t_restart_high) - t
            elif st == "LOW":
                if k == 0:
                    ev[("low_off", 0)] = (t_on[0] + p.t0 - p.t_dead) - t if S else y[nv] - thr[0]
                    if not S and p.t_restart_low > 0:
                        ev[("low_off_restart", 0)] = (t_lon[0] + p.t_restart_low) - t
                elif fired[k] != t_ref:
                    shift = k * t_meas[0] / n if (p.adaptive_shift and not S) else p.shifts[k - 1]
                    if p.qualify_current and not S:            # A76: slot passed AND own current below theta
                        ev[("low_off", k)] = max((t_ref + shift) - t, y[nv + k] - thr[k])
                    else:
                        ev[("low_off", k)] = (t_ref + shift) - t
            elif st == "UP":
                if S:
                    ev[("high_on", k)] = (t_lo[k] + p.t_dead) - t
                else:
                    if p.zvs_reactive or p.valley_mode != "predictive":
                        ev[("high_zvs", k)] = sim.vds(y, k, vin)
                    if p.valley and p.valley_mode == "predictive":
                        ev[("high_pred", k)] = (t_lo[k] + dt_pred[k]) - t
                    elif p.valley:
                        ev[("high_valley", k)] = (vmin[k] + p.v_hys) - sim.vds(y, k, vin)
                    if p.t_restart_high > 0:
                        ev[("high_restart", k)] = (t_lo[k] + p.t_restart_high) - t
        return ev

    t_now = [0.0]
    ton_used[0] = p.ton_at(0.0)
    t_end = p.t_end if t_stop is None else t_stop
    max_steps = int(t_end / p.h * 1.6) + 1000
    steps = 0
    status = "COMPLETED"
    diode_cuts = [0]

    def advance(y, h, t, g, euler, lo):
        """One step; with diode_check, a diode-only branch whose Vds ends > 0 is turned off and the step redone."""
        d = list(diode)
        for _ in range(2 * n + 1):
            cond = tuple(bool(a or b) for a, b in zip(g, d))
            y1 = sim.step(y, cond, h, euler, t, lo)
            if not p.diode_check:
                return y1, cond, d
            vin1 = p.vin_at(t + h)
            bad = [j for j in range(2 * n) if d[j] and not g[j] and sim.vds(y1, j, vin1) > 0]
            if not bad:
                return y1, cond, d
            for j in bad:
                d[j] = False
            diode_cuts[0] += len(bad)
        return y1, cond, d

    while t < t_end:
        g = gates()
        euler = euler_left > 0
        lo = ctl["load_done"]
        y1, conducting, dstep = advance(y, p.h, t, g, euler, lo)
        if p.diode_check and dstep != diode:
            diode = dstep; euler_left = 2
        e0, e1 = event_values(y, t), event_values(y1, t + p.h)
        crossed = [(k, e0[k] / (e0[k] - e1[k])) for k in e0 if e0[k] > 0 and e1.get(k, 1.0) <= 0]
        if p.level_events:
            crossed += [(k, 0.0) for k in e0 if e0[k] <= 0]
        if crossed:
            key, theta = min(crossed, key=lambda kv: kv[1])
            hp = max(theta * p.h, 1e-18)
            if p.diode_check:
                y, conducting, dstep = advance(y, hp, t, g, euler, lo); diode = dstep
            else:
                y = sim.step(y, conducting, hp, euler, t, lo)
            t += hp
            kind, k = key
            vin = p.vin_at(t)
            delayed = False
            bind = None                        # A76: which condition decided a mode-P low-side turn-off
            if kind == "low_off" and ctl["mode"] == "P":
                if k == 0:
                    bind = "current"
                elif p.qualify_current:
                    sh = k * t_meas[0] / n if p.adaptive_shift else p.shifts[k - 1]
                    bind = "current" if (y[nv + k] - thr[k]) > ((t_ref + sh) - t) else "timer"
                else:
                    bind = "timer"
            if kind == "pending":              # A75: the gate edge of a decision taken t_d earlier
                kind, _, bind = pending[k]; pending[k] = None; delayed = True
            elif (p.t_d > 0 and ctl["mode"] == "P"
                  and (kind in ("low_on", "high_zvs", "high_valley") or (kind == "low_off" and bind == "current"))):
                pending[k] = (kind, t + p.t_d, bind); latent["detections"] += 1
                kind = "latent"                # no transition now
            if kind in ("high_on", "high_zvs", "high_valley", "high_restart", "high_pred"):
                turnons.append({"t_s": t, "phase": k + 1, "how": kind, "vds_v": float(sim.vds(y, k, vin)),
                                "cycle": len(sections) - 1, "mode": ctl["mode"], "delayed": delayed,
                                "vds_min_v": None if vmin[k] is None else float(vmin[k]),
                                "t_since_lo_s": None if t_lo[k] is None else t - t_lo[k],
                                "i_a": float(y[nv + k])})
                if len(turnons) > 4000:
                    del turnons[:2000]
            if kind in ("low_off", "low_off_restart"):
                lowoffs.append({"t_s": t, "phase": k + 1, "how": kind, "i_a": float(y[nv + k]),
                                "t_since_ref_s": t - t_ref, "t_meas_s": t_meas[0], "cycle": len(sections) - 1,
                                "mode": ctl["mode"], "vds_high_v": float(sim.vds(y, k, vin)),
                                "states": list(state), "delayed": delayed, "bind": bind, "theta_a": thr[k]})
                if len(lowoffs) > 4000:
                    del lowoffs[:2000]
            if kind.endswith("restart"):
                restarts.append({"t_s": t, "phase": k + 1, "kind": kind, "cycle": len(sections) - 1})
                kind = {"low_on_restart": "low_on", "low_off_restart": "low_off", "high_restart": "high_on"}[kind]
            if kind == "off_cap":
                kind = "off_high"
            if kind == "load_on":
                ctl["load_done"] = True
            elif kind == "off_high":
                state[k] = "DOWN"; t_off[k] = t; ton_last[k] = t - t_on[k]
            elif kind == "low_on":
                state[k] = "LOW"; t_lon[k] = t
            elif kind == "low_off":
                state[k] = "UP"; fired[k] = t_ref; t_lo[k] = t
                vmin[k] = sim.vds(y, k, vin); t_vmin[k] = t; v_lo[k] = vmin[k]
                if p.trim_gain > 0 and bind == "current":   # A76: self-trim toward i_target at the edge
                    lo_t, hi_t = p.i_target + p.trim_clamp[0], p.i_target + p.trim_clamp[1]
                    thr[k] = min(max(thr[k] + p.trim_gain * (p.i_target - float(y[nv + k])), lo_t), hi_t)
                    trims[0] += 1
            elif kind in ("high_on", "high_zvs", "high_valley", "high_pred"):
                if kind == "high_pred":        # A75: correct the predicted valley time for the next cycle
                    if sim.vds(y, k, vin) < vmin[k]:                       # node still falling: early
                        dt_pred[k] = min(dt_pred[k] + p.dt_step, 3 * half_res); pred_stats["early"] += 1
                    elif vmin[k] < v_lo[k] - p.v_hys and t_vmin[k] > t_lo[k]:  # a dip was seen: late
                        dt_pred[k] = t_vmin[k] - t_lo[k]; pred_stats["late"] += 1
                    else:                                                  # flat node: no information
                        pred_stats["flat"] = pred_stats.get("flat", 0) + 1
                if kind == "high_valley":
                    valley_events.append({"t_s": t, "phase": k + 1, "vds_v": float(sim.vds(y, k, vin)),
                                          "vds_min_v": float(vmin[k]), "cycle": len(sections) - 1})
                state[k] = "HIGH"; t_on[k] = t; tau[k] = 0.0; ton_used[k] = p.ton_at(t)
                if k == 0:
                    tm = t - t_ref
                    lo_c, hi_c = p.t_meas_clamp[0] * p.t0, p.t_meas_clamp[1] * p.t0
                    if tm < lo_c or tm > hi_c:
                        clamps[0] += 1
                    t_meas[0] = min(max(tm, lo_c), hi_c)
                    t_ref = t
                    if ctl["mode"] == "S" and t >= p.t_hand:
                        ctl["mode"] = "P"; ctl["t_hand_actual_s"] = t
                    sections.append(record(y, t)); ctl["ipk"] = 0.0
                    for j in range(n):
                        acc_i2[j] = 0.0
                    m = len(sections) - 1
                    if log_every and m % log_every == 0:
                        s = sections[-1]; vi = max(s["vin_v"], 1e-12)
                        lad = [s["vcs_v"][j] / vi for j in range(n - 1)]
                        print(f"  cycle {m:5d} t {t * 1e6:8.3f} us {s['mode']} Vin {s['vin_v']:6.2f} Vo {s['vo']:7.4f} "
                              f"Cs/Vin {np.round(lad, 4)} i {np.round(s['i'], 1)} ipk {s['ipk_a']:6.1f} "
                              f"valley {s['valley_count']} vdsmax {max(vds_max):5.1f} wall {time.time() - t0w:.0f}s", flush=True)
            euler_left = 2
        else:
            t += p.h; y = y1
            euler_left = max(0, euler_left - 1)
        if p.k_b > 0:
            for k in range(n):
                if state[k] == "HIGH" and t_on[k] is not None and t_on[k] < t:
                    tau[k] += (t - t_now[0]) * bal_rate(y, t, k)
        dta = t - t_now[0]                 # A78: accumulate i^2 dt over the accepted step
        for j in range(n):
            acc_i2[j] += float(y[nv + j]) ** 2 * dta
        t_now[0] = t
        ctl["ipk"] = max(ctl["ipk"], float(np.max(np.abs(y[nv:]))))
        vin = p.vin_at(t)
        for k in range(n):             # valley tracking after every accepted (full or partial) step
            if state[k] == "UP":
                v = sim.vds(y, k, vin)
                if v < vmin[k]:
                    vmin[k] = v; t_vmin[k] = t
        g = gates()
        vd = [sim.vds(y, j, vin) for j in range(2 * n)]
        for j in range(2 * n):
            if vd[j] > vds_max[j]:
                vds_max[j] = vd[j]
        new_d = [(not g[j]) and vd[j] < 0 for j in range(2 * n)]
        if new_d != diode:
            diode = new_d; euler_left = 2
        steps += 1
        if steps > max_steps:
            status = "STEP_GUARD"; break
        if t - sections[-1]["t_s"] > p.stall_periods * p.t0:
            status = "STALLED"; break
    end = {"theta_final_a": list(thr), "trims": trims[0], "half_res_s": half_res, "dt_pred_s": list(dt_pred), "pred_stats": pred_stats,
           "latent_detections": latent["detections"], "pending_at_end": [None if q is None else list(q) for q in pending],
           "lowoffs_last": lowoffs[-1000:],
           "turnons_last": turnons[-1000:], "t_meas_clamps": clamps[0], "t_meas_last_s": t_meas[0],
           "diode_cuts": diode_cuts[0], "restarts": restarts[:500],"restart_count": len(restarts), "status": status, "t_s": t, "states": list(state), "y": y.tolist(), "mode": ctl["mode"],
           "t_hand_actual_s": ctl["t_hand_actual_s"], "vin_v": p.vin_at(t),
           "vds_max_v": {sim.switches[j][0]: vds_max[j] for j in range(2 * n)}}
    return sections, valley_events, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--t-ramp", type=float, default=68.61, help="us")
    ap.add_argument("--t-load", type=float, default=88.61, help="us")
    ap.add_argument("--t-hand", type=float, default=88.61, help="us; <= 0: mode P from t = 0")
    ap.add_argument("--t-end", type=float, default=388.61, help="us")
    ap.add_argument("--h", type=float, default=10e-12)
    ap.add_argument("--log-every", type=int, default=250)
    ap.add_argument("--t-dead", type=float, default=2.15, help="ns, mode S fixed dead time")
    ap.add_argument("--stall-periods", type=float, default=3.0)
    ap.add_argument("--level-events", action="store_true")
    ap.add_argument("--t-restart-high", type=float, default=0.0, help="ns")
    ap.add_argument("--t-restart-low", type=float, default=0.0, help="ns")
    ap.add_argument("--init-ladder", default="", help="comma-separated V, e.g. 36,24,12")
    ap.add_argument("--t-ss", type=float, default=0.0, help="us")
    ap.add_argument("--k-b", type=float, default=0.0)
    ap.add_argument("--diode-check", action="store_true")
    ap.add_argument("--preset", default="p24", choices=("p24", "p25"), help="p25: A71's three-phase P25-scale circuit (CC load)")
    ap.add_argument("--init-z-json", default="", help="json with z_star (A69 section names) for an N = 3 start")
    ap.add_argument("--no-valley", action="store_true")
    ap.add_argument("--adaptive-shift", action="store_true", help="A74: mode-P shifts follow the measured period")
    ap.add_argument("--t-d", type=float, default=0.0, help="A75: ns, comparator-to-gate latency in mode P")
    ap.add_argument("--valley-mode", default="reactive", choices=("reactive", "predictive"))
    ap.add_argument("--dt-step", type=float, default=0.2, help="A75: ns, predictive correction step")
    ap.add_argument("--trim-gain", type=float, default=0.0, help="A76: comparator self-trim gain per cycle")
    ap.add_argument("--qualify-current", action="store_true", help="A76: phases 2..N need i_k <= theta_k to turn off")
    ap.add_argument("--no-zvs-reactive", action="store_true", help="A76: no reactive ZVS decision in predictive mode")
    ap.add_argument("--i-target", type=float, default=None, help="A78: A, low-side turn-off current target")
    a = ap.parse_args()
    kw = dict(t_ramp=a.t_ramp * 1e-6, t_load=a.t_load * 1e-6, t_hand=a.t_hand * 1e-6, t_end=a.t_end * 1e-6, h=a.h,
              t_dead=a.t_dead * 1e-9, stall_periods=a.stall_periods, level_events=a.level_events,
              t_restart_high=a.t_restart_high * 1e-9, t_restart_low=a.t_restart_low * 1e-9,
              init_ladder=tuple(float(v) for v in a.init_ladder.split(",")) if a.init_ladder else (),
              t_ss=a.t_ss * 1e-6, k_b=a.k_b, diode_check=a.diode_check)
    if a.preset == "p25":
        kw.update(P25_PRESET)          # the preset's circuit values (incl. t_dead 20 ns) take precedence
    if a.init_z_json:
        zs = json.loads(Path(a.init_z_json).read_text())["z_star"]
        kw["init_z"] = tuple(zs[k] for k in ("a2_v", "x1_v", "out_v", "iL1_a", "iL2_a", "iL3_a"))
    kw["valley"] = not a.no_valley
    kw["adaptive_shift"] = a.adaptive_shift
    kw.update(t_d=a.t_d * 1e-9, valley_mode=a.valley_mode, dt_step=a.dt_step * 1e-9)
    kw.update(trim_gain=a.trim_gain, qualify_current=a.qualify_current, zvs_reactive=not a.no_zvs_reactive)
    if a.i_target is not None:
        kw["i_target"] = a.i_target
    p = Params(**kw)
    print(f"A78 {a.case}: trim {p.trim_gain} qualify {p.qualify_current} zvs_reactive {p.zvs_reactive}; "
          f"t_d {a.t_d} ns, valley {p.valley_mode}; adaptive_shift {p.adaptive_shift}; init_ladder {p.init_ladder} t_ss {a.t_ss} us k_b {p.k_b}; N={p.n} Vin {p.vin} V, t_ramp {a.t_ramp} us, t_load {a.t_load} us, t_hand {a.t_hand} us, "
          f"t_end {a.t_end} us, load {p.load_kind} {p.r_load if p.load_kind == 'r' else p.i_load}, h {p.h * 1e12:.0f} ps", flush=True)
    sections, valley_events, end = run(p, log_every=a.log_every)
    print(f"end: {end['status']} at t={end['t_s'] * 1e6:.3f} us, mode {end['mode']}, states {end['states']}, "
          f"{len(sections) - 1} sections, {len(valley_events)} valley firings, handover at "
          f"{None if end['t_hand_actual_s'] is None else round(end['t_hand_actual_s'] * 1e6, 3)} us, "
          f"vds max {max(end['vds_max_v'].values()):.2f} V", flush=True)
    stride = max(1, (len(sections) - 1) // 4000)          # keep the file small: every stride-th section + the last 400
    keep = sorted(set(range(0, len(sections), stride)) | set(range(max(0, len(sections) - 400), len(sections))))
    out = {"case": a.case, "argv": sys.argv[1:],
           "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.__dict__.items()},
           "end": end, "valley_events_count": len(valley_events),
           "valley_events_first_2000": valley_events[:2000], "valley_events_last_200": valley_events[-200:],
           "section_stride": stride, "sections_total": len(sections), "sections": [sections[i] | {"index": i} for i in keep]}
    path = HERE / f"run_{a.case}.json"
    k = 2
    while path.exists():
        path = HERE / f"run_{a.case}_v{k}.json"
        k += 1
    path.write_text(json.dumps(out))
    print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
