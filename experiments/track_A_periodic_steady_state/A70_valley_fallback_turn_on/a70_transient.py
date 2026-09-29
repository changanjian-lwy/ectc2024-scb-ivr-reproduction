"""A70 - A69's simulator plus a valley-switching fallback for the high-side turn-on (BOUNDARY.md).

Copied from A69 (a69_transient.py, unmodified there). The only controller change
is in the UP state: besides the ZVS path (Vds <= 0), SHk also turns on once its
Vds has passed its minimum and risen by v_hys (Chiang & Chen, TPEL 2009,
DOI 10.1109/TPEL.2009.2021186: "VDD/Peak detecting" turn-on path).

A69 docstring follows.

Does NOT import the mathematical model (scb_ivr.p25_*). Nodal equations
    [Cm 0; 0 L] d/dt [v; i] = [[-G, -B], [B^T, -R]] [v; i] + [g_vin*Vin - e_out*I_load; 0],
    v = (a1, a2, x1, x2, x3, out), i = (i1, i2, i3) (x_k -> out).
Trapezoidal steps of size h; backward Euler for the first two steps after a
topology change. Controller events (timers, ZVS detections, the phase-1
current target) are landed on by a partial step to the linearly
interpolated crossing, so event-time error is O(h^2), not O(h).
Diode (reverse-channel) states update at step boundaries.
"""
from __future__ import annotations

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
# switch: (name, drain, source); 'vin' fixed, None = ground
SWITCHES = (("SH1", "vin", "a1"), ("SH2", "a1", "a2"), ("SH3", "a2", "x3"),
            ("SL1", "x1", None), ("SL2", "x2", None), ("SL3", "x3", None))
SECTION_NAMES = ("a2_v", "x1_v", "out_v", "iL1_a", "iL2_a", "iL3_a")


@dataclass
class Params:
    vin: float = 12.0
    L: float = 30e-9
    R: float = 0.0
    c_high: float = 0.69e-9
    c_low: float = 1.38e-9
    cs: float = 100e-6
    co: float = 100e-6
    i_load: float = 67.5
    ton: float = 500e-9
    i_target: float = -2.5
    shifts: tuple = (2e-6 / 3, 4e-6 / 3)
    g_on: float = 1e7          # 0.1 uOhm ON switch (BOUNDARY amendment; 10 uOhm gave a 0.25 ns offset)
    g_diode: float = 1e7       # 0.1 uOhm reverse channel
    h: float = 10e-12
    v_hys: float = 0.05        # valley-path comparator hysteresis (PROJECT_DECISION)
    valley: bool = True        # False reproduces A69's controller


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
        """A, f for a tuple of six conducting flags (gate ON or diode ON)."""
        p = self.p
        G = np.zeros((6, 6)); gv = np.zeros(6)
        for on, (name, d, s) in zip(conducting, SWITCHES):
            if not on:
                continue
            g = p.g_on
            idd, iss = IDX.get(d), IDX.get(s)
            if d == "vin":
                G[iss, iss] += g; gv[iss] += g * p.vin
                continue
            if idd is not None:
                G[idd, idd] += g
            if iss is not None:
                G[iss, iss] += g
            if idd is not None and iss is not None:
                G[idd, iss] -= g; G[iss, idd] -= g
        A = np.zeros((9, 9)); A[:6, :6] = -G; A[:6, 6:] = -self.B; A[6:, :6] = self.B.T; A[6:, 6:] = -p.R * np.eye(3)
        f = np.zeros(9); f[:6] = gv; f[IDX["out"]] -= p.i_load
        return A, f

    def step(self, y, conducting, h, euler):
        key = (conducting, h, euler)
        entry = self.cache.get(key)
        if entry is None:
            A, f = self.system(conducting)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, h * f)
            if h == self.p.h:          # cache only full steps
                self.cache[key] = entry
        lu, rhs_m, hf = entry
        return lu_solve(lu, rhs_m @ y + hf)


def vds(y, k, vin):
    name, d, s = SWITCHES[k]
    vd = vin if d == "vin" else y[IDX[d]]
    vs = 0.0 if s is None else y[IDX[s]]
    return vd - vs


def run(p: Params, section0, cycles: int, log_every: int = 10):
    """section0 = (a2, x1, out, i1, i2, i3) at a phase-1 high-side turn-on."""
    sim = Sim(p)
    a2, x1, out, i1, i2, i3 = section0
    y = np.array([p.vin, a2, x1, 0.0, 0.0, out, i1, i2, i3], float)   # SH1 on: a1 = vin; SL2, SL3 on
    state = ["HIGH", "LOW", "LOW"]            # phase controller states
    t = 0.0; t_on = [0.0, None, None]; t_ref = 0.0; fired = [None, None, None]
    diode = [False] * 6
    vmin = [None, None, None]                 # min Vds(SHk) since entering UP
    valley_events = []
    euler_left = 2
    sections = [{"t_s": 0.0, "z": list(map(float, section0))}]
    guard = {"max_steps": int(cycles * 2.2e-6 / p.h * 1.5)}
    steps = 0
    t0 = time.time()

    def gates():
        high = [s == "HIGH" for s in state]
        low = [s == "LOW" for s in state]
        return high + low

    def event_values(y, t):
        """Signed quantities that trigger controller events when they cross to <= 0."""
        ev = {}
        for k in range(3):
            if state[k] == "HIGH":
                ev[("off_high", k)] = (t_on[k] + p.ton) - t
            elif state[k] == "DOWN":
                ev[("low_zvs", k)] = vds(y, 3 + k, p.vin)
            elif state[k] == "LOW":
                if k == 0:
                    ev[("low_off", k)] = y[6] - p.i_target
                elif fired[k] != t_ref:
                    ev[("low_off", k)] = (t_ref + p.shifts[k - 1]) - t
            elif state[k] == "UP":
                ev[("high_zvs", k)] = vds(y, k, p.vin)
                if p.valley:
                    ev[("high_valley", k)] = (vmin[k] + p.v_hys) - vds(y, k, p.vin)
        return ev

    while len(sections) <= cycles:
        g = gates()
        conducting = tuple(bool(a or b) for a, b in zip(g, diode))
        euler = euler_left > 0
        y1 = sim.step(y, conducting, p.h, euler)
        e0, e1 = event_values(y, t), event_values(y1, t + p.h)
        crossed = [(k, e0[k] / (e0[k] - e1[k])) for k in e0 if e0[k] > 0 and e1.get(k, 1.0) <= 0]
        if crossed:
            key, theta = min(crossed, key=lambda kv: kv[1])
            hp = max(theta * p.h, 1e-18)
            y1 = sim.step(y, conducting, hp, euler)
            t += hp; y = y1
            kind, k = key
            if kind == "off_high":
                state[k] = "DOWN"
            elif kind == "low_zvs":
                state[k] = "LOW"
            elif kind == "low_off":
                state[k] = "UP"; fired[k] = t_ref
                vmin[k] = vds(y, k, p.vin)
            elif kind in ("high_zvs", "high_valley"):
                if kind == "high_valley":
                    valley_events.append({"t_s": t, "phase": k + 1, "vds_v": float(vds(y, k, p.vin)),
                                          "vds_min_v": float(vmin[k]), "cycle": len(sections) - 1})
                state[k] = "HIGH"; t_on[k] = t
                if k == 0:
                    t_ref = t
                    sections.append({"t_s": t, "z": [float(y[1]), float(y[2]), float(y[5]), float(y[6]), float(y[7]), float(y[8])],
                                     "valley_count": len(valley_events)})
                    if log_every and (len(sections) - 1) % log_every == 0:
                        z = sections[-1]["z"]; T = sections[-1]["t_s"] - sections[-2]["t_s"]
                        print(f"  cycle {len(sections) - 1:4d}  T {T * 1e9:.4f} ns  z {np.round(z, 4)}  wall {time.time() - t0:.0f}s", flush=True)
            euler_left = 2
        else:
            t += p.h; y = y1
            euler_left = max(0, euler_left - 1)
        for k in range(3):             # valley tracking after every accepted (full or partial) step
            if state[k] == "UP":
                vmin[k] = min(vmin[k], vds(y, k, p.vin))
        # diode states from the new voltages (gate-OFF switches only)
        g = gates()
        new_d = [(not g[k]) and vds(y, k, p.vin) < 0 for k in range(6)]
        if new_d != diode:
            diode = new_d; euler_left = 2
        steps += 1
        if steps > guard["max_steps"]:
            return sections, valley_events, {"status": "STEP_GUARD", "t_s": t, "states": list(state), "y": y.tolist()}
        if t - sections[-1]["t_s"] > 3 * 2e-6:      # also covers a stall before the first section (BOUNDARY 7)
            return sections, valley_events, {"status": "STALLED", "t_s": t, "states": list(state), "y": y.tolist()}
    return sections, valley_events, {"status": "COMPLETED", "t_s": t, "states": list(state), "y": y.tolist()}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--cycles", type=int, default=250)
    ap.add_argument("--h", type=float, default=10e-12)
    ap.add_argument("--ref", required=True, help="json with z_star (and R_ohm): reference orbit")
    ap.add_argument("--start", help="json with z_star: start state (default: the reference)")
    ap.add_argument("--g-on", type=float, default=1e7)
    ap.add_argument("--v-hys", type=float, default=0.05)
    ap.add_argument("--zero-currents", action="store_true", help="start with all inductor currents at zero")
    ap.add_argument("--no-valley", action="store_true", help="A69 controller (no valley path)")
    a = ap.parse_args()
    ref = json.loads(Path(a.ref).read_text())
    p = Params(R=ref.get("R_ohm", 0.0), h=a.h, g_on=a.g_on, g_diode=a.g_on, v_hys=a.v_hys, valley=not a.no_valley)
    z0 = json.loads(Path(a.start).read_text())["z_star"] if a.start else ref["z_star"]
    z0 = [z0[n] for n in SECTION_NAMES] if isinstance(z0, dict) else list(z0)
    if a.zero_currents:
        z0[3:] = [0.0, 0.0, 0.0]
    print(f"A70 {a.case}: R={p.R * 1e3:.2f} mOhm h={a.h * 1e12:.1f} ps cycles={a.cycles} v_hys={p.v_hys} "
          f"valley={p.valley} start {np.round(z0, 6)}", flush=True)
    sections, valley_events, end = run(p, z0, a.cycles)
    print(f"end: {end['status']} at t={end['t_s'] * 1e6:.3f} us, states {end['states']}, "
          f"{len(sections) - 1} cycles, {len(valley_events)} valley firings", flush=True)
    out = {"case": a.case, "argv": sys.argv[1:], "h_s": a.h,
           "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.__dict__.items()},
           "reference": ref, "start_z": z0, "end": end, "valley_events": valley_events, "sections": sections}
    path = HERE / f"run_{a.case}.json"
    k = 2
    while path.exists():
        path = HERE / f"run_{a.case}_v{k}.json"
        k += 1
    path.write_text(json.dumps(out, indent=1))
    print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
