"""A71 - zero start of the P25 three-phase SCB following a published sequence (BOUNDARY.md).

Built from A70's simulator (a70_transient.py, unmodified there): same circuit,
integration (trapezoid, backward Euler for two steps after a topology change),
diode branches and interpolated event landing. Changes:
- a ramped input source Vin(t) = Vin * min(t / t_ramp, 1);
- a constant-current load switched from 0 to i_load at t_load (a landed event);
- an all-zero initial state;
- mode S (fixed timing, fixed dead time) from t = 0, handed over to mode P
  (A70's controller: D41 single-sensor rule + Chiang valley fallback) at the
  first phase-1 high-side turn-on at or after t_hand.
Nodal equations as in A69:
    [Cm 0; 0 L] d/dt [v; i] = [[-G, -B], [B^T, -R]] [v; i] + f(t),
    f(t) = g_vin * Vin(t) - e_out * I_load(t),
    v = (a1, a2, x1, x2, x3, out), i = (i1, i2, i3) (x_k -> out).
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
NODES = ("a1", "a2", "x1", "x2", "x3", "out")
IDX = {n: k for k, n in enumerate(NODES)}
SWITCHES = (("SH1", "vin", "a1"), ("SH2", "a1", "a2"), ("SH3", "a2", "x3"),
            ("SL1", "x1", None), ("SL2", "x2", None), ("SL3", "x3", None))
SECTION_NAMES = ("a2_v", "x1_v", "out_v", "iL1_a", "iL2_a", "iL3_a")


@dataclass
class Params:
    vin: float = 12.0          # final input voltage
    L: float = 30e-9
    R: float = 4.9e-3          # per-phase series resistance (D42 PROJECT_DECISION)
    c_high: float = 0.69e-9
    c_low: float = 1.38e-9
    cs: float = 100e-6
    co: float = 100e-6
    i_load: float = 67.5       # load after t_load
    ton: float = 500e-9
    i_target: float = -2.5
    t0: float = 2e-6           # mode S period (P25 0.5 MHz)
    shifts: tuple = (2e-6 / 3, 4e-6 / 3)
    t_dead: float = 20e-9      # mode S fixed dead time (PROJECT_DECISION)
    g_on: float = 1e7          # 0.1 uOhm ON switch / diode (A69 amendment)
    h: float = 10e-12
    v_hys: float = 0.05        # valley-path hysteresis (A70)
    t_ramp: float = 457e-6
    t_load: float = 507e-6
    t_hand: float = 607e-6     # <= 0: mode P from t = 0
    t_end: float = 1207e-6

    def vin_at(self, t):
        return self.vin * min(t / self.t_ramp, 1.0) if self.t_ramp > 0 else self.vin

    def load_at(self, t):
        return self.i_load if t >= self.t_load else 0.0


@dataclass
class Sim:
    p: Params
    cache: dict = field(default_factory=dict)

    def __post_init__(self):
        p = self.p
        caps = [(p.c_high, "vin", "a1"), (p.c_high, "a1", "a2"), (p.c_high, "a2", "x3"),
                (p.c_low, "x1", None), (p.c_low, "x2", None), (p.c_low, "x3", None),
                (p.cs, "a1", "x1"), (p.cs, "a2", "x2"), (p.co, "out", None)]
        cm = np.zeros((6, 6))
        for c, a, b in caps:
            ia, ib = IDX.get(a), IDX.get(b)
            if ia is not None:
                cm[ia, ia] += c
            if ib is not None:
                cm[ib, ib] += c
            if ia is not None and ib is not None:
                cm[ia, ib] -= c; cm[ib, ia] -= c
        self.M = np.zeros((9, 9)); self.M[:6, :6] = cm; self.M[6:, 6:] = p.L * np.eye(3)
        self.B = np.zeros((6, 3))
        for k in range(3):
            self.B[IDX[f"x{k + 1}"], k] = 1.0; self.B[IDX["out"], k] = -1.0

    def system(self, conducting):
        """A, f per unit Vin, f per unit load current, for six conducting flags."""
        p = self.p
        G = np.zeros((6, 6)); gv = np.zeros(6)
        for on, (name, d, s) in zip(conducting, SWITCHES):
            if not on:
                continue
            g = p.g_on
            idd, iss = IDX.get(d), IDX.get(s)
            if d == "vin":
                G[iss, iss] += g; gv[iss] += g
                continue
            if idd is not None:
                G[idd, idd] += g
            if iss is not None:
                G[iss, iss] += g
            if idd is not None and iss is not None:
                G[idd, iss] -= g; G[iss, idd] -= g
        A = np.zeros((9, 9)); A[:6, :6] = -G; A[:6, 6:] = -self.B; A[6:, :6] = self.B.T; A[6:, 6:] = -p.R * np.eye(3)
        fv = np.zeros(9); fv[:6] = gv
        fl = np.zeros(9); fl[IDX["out"]] = -1.0
        return A, fv, fl

    def step(self, y, conducting, h, euler, t):
        key = (conducting, h, euler)
        entry = self.cache.get(key)
        if entry is None:
            A, fv, fl = self.system(conducting)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, fv, fl)
            if h == self.p.h:          # cache only full steps
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


def vds(y, k, vin):
    name, d, s = SWITCHES[k]
    vd = vin if d == "vin" else y[IDX[d]]
    vs = 0.0 if s is None else y[IDX[s]]
    return vd - vs


def run(p: Params, log_every: int = 25):
    sim = Sim(p)
    y = np.zeros(9)
    state = ["HIGH", "LOW", "LOW"]
    t = 0.0; t_on = [0.0, None, None]; t_ref = 0.0; fired = [None, None, None]
    t_off = [None, None, None]; t_lo = [None, None, None]
    ctl = {"mode": "P" if p.t_hand <= 0 else "S", "t_hand_actual_s": 0.0 if p.t_hand <= 0 else None,
           "load_done": p.t_load <= 0, "ipk": 0.0}
    diode = [False] * 6
    euler_left = 2
    vmin = [None, None, None]
    valley_events = []
    t0w = time.time()

    def record(y, t):
        vin = p.vin_at(t)
        return {"t_s": t, "z": [float(y[1]), float(y[2]), float(y[5]), float(y[6]), float(y[7]), float(y[8])],
                "vin_v": vin, "vcs1_v": float(y[0] - y[2]), "vcs2_v": float(y[1] - y[3]), "mode": ctl["mode"],
                "load_a": p.load_at(t), "ipk_a": ctl["ipk"], "valley_count": len(valley_events)}

    sections = [record(y, 0.0)]

    def gates():
        return [s == "HIGH" for s in state] + [s == "LOW" for s in state]

    def event_values(y, t):
        """Signed quantities whose crossing to <= 0 triggers an event."""
        vin = p.vin_at(t)
        ev = {}
        if not ctl["load_done"]:
            ev[("load_on", -1)] = p.t_load - t
        S = ctl["mode"] == "S"
        for k in range(3):
            st = state[k]
            if st == "HIGH":
                ev[("off_high", k)] = (t_on[k] + p.ton) - t
            elif st == "DOWN":
                ev[("low_on", k)] = (t_off[k] + p.t_dead) - t if S else vds(y, 3 + k, vin)
            elif st == "LOW":
                if k == 0:
                    ev[("low_off", 0)] = (t_on[0] + p.t0 - p.t_dead) - t if S else y[6] - p.i_target
                elif fired[k] != t_ref:
                    ev[("low_off", k)] = (t_ref + p.shifts[k - 1]) - t
            elif st == "UP":
                if S:
                    ev[("high_on", k)] = (t_lo[k] + p.t_dead) - t
                else:
                    ev[("high_zvs", k)] = vds(y, k, vin)
                    ev[("high_valley", k)] = (vmin[k] + p.v_hys) - vds(y, k, vin)
        return ev

    max_steps = int(p.t_end / p.h * 1.6) + 1000
    steps = 0
    status = "COMPLETED"
    while t < p.t_end:
        g = gates()
        conducting = tuple(bool(a or b) for a, b in zip(g, diode))
        euler = euler_left > 0
        y1 = sim.step(y, conducting, p.h, euler, t)
        e0, e1 = event_values(y, t), event_values(y1, t + p.h)
        crossed = [(k, e0[k] / (e0[k] - e1[k])) for k in e0 if e0[k] > 0 and e1.get(k, 1.0) <= 0]
        if crossed:
            key, theta = min(crossed, key=lambda kv: kv[1])
            hp = max(theta * p.h, 1e-18)
            y = sim.step(y, conducting, hp, euler, t); t += hp
            kind, k = key
            vin = p.vin_at(t)
            if kind == "load_on":
                ctl["load_done"] = True
            elif kind == "off_high":
                state[k] = "DOWN"; t_off[k] = t
            elif kind == "low_on":
                state[k] = "LOW"
            elif kind == "low_off":
                state[k] = "UP"; fired[k] = t_ref; t_lo[k] = t
                vmin[k] = vds(y, k, vin)
            elif kind in ("high_on", "high_zvs", "high_valley"):
                if kind == "high_valley":
                    valley_events.append({"t_s": t, "phase": k + 1, "vds_v": float(vds(y, k, vin)),
                                          "vds_min_v": float(vmin[k]), "cycle": len(sections) - 1})
                state[k] = "HIGH"; t_on[k] = t
                if k == 0:
                    t_ref = t
                    if ctl["mode"] == "S" and t >= p.t_hand:
                        ctl["mode"] = "P"; ctl["t_hand_actual_s"] = t
                    sections.append(record(y, t)); ctl["ipk"] = 0.0
                    n = len(sections) - 1
                    if log_every and n % log_every == 0:
                        s = sections[-1]; vi = max(s["vin_v"], 1e-12)
                        print(f"  cycle {n:4d} t {t * 1e6:8.2f} us  {s['mode']}  Vin {s['vin_v']:6.3f}  Vo {s['z'][2]:7.4f}  "
                              f"Cs1/Vin {s['vcs1_v'] / vi:6.4f}  Cs2/Vin {s['vcs2_v'] / vi:6.4f}  "
                              f"i {np.round(s['z'][3:], 2)}  ipk {s['ipk_a']:6.1f}  valley {s['valley_count']}  "
                              f"wall {time.time() - t0w:.0f}s", flush=True)
            euler_left = 2
        else:
            t += p.h; y = y1
            euler_left = max(0, euler_left - 1)
        ctl["ipk"] = max(ctl["ipk"], float(np.max(np.abs(y[6:]))))
        vin = p.vin_at(t)
        for k in range(3):             # valley tracking after every accepted (full or partial) step
            if state[k] == "UP":
                vmin[k] = min(vmin[k], vds(y, k, vin))
        g = gates()
        new_d = [(not g[k]) and vds(y, k, vin) < 0 for k in range(6)]
        if new_d != diode:
            diode = new_d; euler_left = 2
        steps += 1
        if steps > max_steps:
            status = "STEP_GUARD"; break
        if t - sections[-1]["t_s"] > 3 * p.t0:
            status = "STALLED"; break
    end = {"status": status, "t_s": t, "states": list(state), "y": y.tolist(), "mode": ctl["mode"],
           "t_hand_actual_s": ctl["t_hand_actual_s"], "vin_v": p.vin_at(t)}
    return sections, valley_events, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--t-ramp", type=float, default=457.0, help="us")
    ap.add_argument("--t-load", type=float, default=507.0, help="us")
    ap.add_argument("--t-hand", type=float, default=607.0, help="us; <= 0: P25 rule from t = 0")
    ap.add_argument("--t-end", type=float, default=1207.0, help="us")
    ap.add_argument("--h", type=float, default=10e-12)
    a = ap.parse_args()
    p = Params(t_ramp=a.t_ramp * 1e-6, t_load=a.t_load * 1e-6, t_hand=a.t_hand * 1e-6, t_end=a.t_end * 1e-6, h=a.h)
    print(f"A71 {a.case}: t_ramp {a.t_ramp} us, t_load {a.t_load} us, t_hand {a.t_hand} us, t_end {a.t_end} us, "
          f"R {p.R * 1e3} mOhm, h {p.h * 1e12:.0f} ps", flush=True)
    sections, valley_events, end = run(p)
    print(f"end: {end['status']} at t={end['t_s'] * 1e6:.3f} us, mode {end['mode']}, states {end['states']}, "
          f"{len(sections) - 1} sections, {len(valley_events)} valley firings, handover at "
          f"{None if end['t_hand_actual_s'] is None else round(end['t_hand_actual_s'] * 1e6, 3)} us", flush=True)
    out = {"case": a.case, "argv": sys.argv[1:],
           "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.__dict__.items()},
           "end": end, "valley_events": valley_events, "sections": sections}
    path = HERE / f"run_{a.case}.json"
    k = 2
    while path.exists():
        path = HERE / f"run_{a.case}_v{k}.json"
        k += 1
    path.write_text(json.dumps(out, indent=1))
    print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
