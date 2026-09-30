"""A86 check of the nonlinear-Coss step against an independent integrator (after runs n0-n5; BOUNDARY Section 8).

Phase 4's switching node x4 carries only SL4 (3 devices, x4-gnd) and SH4 (2 devices, a3-x4). With phases 1-3 low
(x3 = 0, a3 held by Cs3 = 3 uF) and out held by Co = 4.672 mF, x4 is a one-dimensional nonlinear LC:
    C(x4) dx4/dt = -i4,   L di4/dt = x4 - out - R i4,   C(x4) = 3 c(x4) + 2 c(a3 - x4),
c(V) the PCHIP of A59's digitised datasheet curve (not A86's 1 mV table). solve_ivp (DOP853, rtol 1e-12) is the
reference. A86's Sim steps the full circuit (h = 10 ps, trapezoid, chord iteration) from the same state. The linear
case (nonlinear_coss off, and the ODE with the constant 1860 pF) measures how far the full circuit is from the 1-D
reduction by itself.

Cases: (a) valley ringing after phase 4's low-side turn-off at -1.85, -3.19, -5.74 A (A86 runs n1, n3, n4);
(b) phase 4's high-side turn-off at +120 A (node falls from a3 to 0; stopped before the low-side diode).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a86", HERE / "a86_transient.py")
a86 = importlib.util.module_from_spec(spec); sys.modules["a86"] = a86; spec.loader.exec_module(a86)

SEC = json.loads((HERE / "run_n3_3pct_nl.json").read_text())["sections"][-1]
VCS = SEC["vcs_v"]            # flying-capacitor voltages of run n3's last section
OUT_V = 1.0


def pchip_c():
    pts = {}
    with open(a86.COSS_CSV) as fh:
        for row in csv.DictReader(fh):
            if row["curve"] == "coss":
                pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
    v = np.array(sorted(pts)); c = np.array([pts[x] for x in v]); keep = v > 0
    v = np.concatenate([[0.0], v[keep]]); c = np.concatenate([[c[keep][0]], c[keep]])
    grid = np.arange(0.0, 40.0 + 1e-9, 0.1)
    return PchipInterpolator(grid, np.interp(grid, v, c), extrapolate=False)


CI = pchip_c()


def c_dev(v, nonlinear):
    return float(CI(abs(v))) if nonlinear else 1860e-12


def ode(x0, i0, a3, t_end, nonlinear, stop_at_zero):
    p = a86.Params()

    def f(t, z):
        x, i = z
        cn = 3 * c_dev(x, nonlinear) + 2 * c_dev(a3 - x, nonlinear)
        return [-i / cn, (x - OUT_V - p.R * i) / p.L]

    ev = None
    if stop_at_zero:
        ev = lambda t, z: z[0]
        ev.terminal, ev.direction = True, -1
    return solve_ivp(f, (0, t_end), [x0, i0], method="DOP853", rtol=1e-12, atol=[1e-12, 1e-12], dense_output=True,
                     events=ev, max_step=5e-12)


def full(x0, i0, t_end, nonlinear, high_on_before):
    p = a86.Params(t_ramp=0.0, nonlinear_coss=nonlinear)
    sim = a86.Sim(p)
    y = np.zeros(sim.nv + p.n)
    ix = sim.idx
    for k in (1, 2, 3):
        y[ix[f"a{k}"]] = VCS[k - 1]           # x1..x3 = 0 (low sides on)
    y[ix["x4"]] = x0; y[ix["out"]] = OUT_V
    y[sim.nv + 3] = i0
    y[sim.nv:sim.nv + 3] = SEC["i"][:3]
    conducting = (False,) * 4 + (True, True, True, False)
    ts, xs, iis, a3s = [0.0], [x0], [i0], [y[ix["a3"]]]
    t, n_steps = 0.0, int(round(t_end / p.h))
    for s in range(n_steps):
        y = sim.step(y, conducting, p.h, s < 2, t, True)          # 2 backward-Euler steps after the switch, as run()
        t += p.h
        ts.append(t); xs.append(y[ix["x4"]]); iis.append(y[sim.nv + 3]); a3s.append(y[ix["a3"]])
        if high_on_before and y[ix["x4"]] < 0:
            break
    return np.array(ts), np.array(xs), np.array(iis), np.array(a3s)


def valley(ts, xs, a3s):
    k = int(np.argmax(xs))
    if 0 < k < len(xs) - 1:                                    # parabolic refinement of the maximum
        y0, y1, y2 = xs[k - 1], xs[k], xs[k + 1]
        den = y0 - 2 * y1 + y2
        dk = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    else:
        dk = 0.0
    h = ts[1] - ts[0]
    return ts[k] + dk * h, a3s[k] - xs[k]


def main():
    a3 = VCS[2]
    res = {"a3_v": a3, "vcs_v": VCS, "valley": [], "falling": []}
    print(f"a3 = {a3:.4f} V (run n3 last section); out = {OUT_V} V")
    for i0 in (-1.85, -3.19, -5.74):
        for nl in (False, True):
            ts, xs, iis, a3s = full(0.0, i0, 20e-9, nl, False)
            sol = ode(0.0, i0, a3, 20e-9, nl, False)
            tv_f, vds_f = valley(ts, xs, a3s)
            tt = np.linspace(0, 20e-9, 200001)
            xo = sol.sol(tt)[0]
            k = int(np.argmax(xo)); tv_o, vds_o = tt[k], a3 - xo[k]
            dev = float(np.max(np.abs(np.interp(ts, tt, xo) - xs)))
            rec = {"i0_a": i0, "nonlinear": nl, "valley_t_ns": {"full": tv_f * 1e9, "ode": tv_o * 1e9},
                   "valley_vds_v": {"full": vds_f, "ode": vds_o}, "max_abs_dx4_v_0_20ns": dev}
            res["valley"].append(rec)
            print(f"valley  i0 {i0:+.2f} A {'nonlinear' if nl else 'linear   '}: t_valley full {tv_f * 1e9:.3f} / ode "
                  f"{tv_o * 1e9:.3f} ns; Vds_valley full {vds_f:.4f} / ode {vds_o:.4f} V; max|dx4| {dev * 1e3:.2f} mV")
    for nl in (False, True):
        ts, xs, iis, a3s = full(a3, 120.0, 5e-9, nl, True)
        sol = ode(a3, 120.0, a3, 5e-9, nl, True)
        t_f = float(np.interp(0.0, xs[::-1], ts[::-1]))
        t_o = float(sol.t_events[0][0])
        res["falling"].append({"nonlinear": nl, "t_fall_ns": {"full": t_f * 1e9, "ode": t_o * 1e9}})
        print(f"falling +120 A {'nonlinear' if nl else 'linear   '}: time a3 -> 0 full {t_f * 1e9:.4f} / ode {t_o * 1e9:.4f} ns")
    (HERE / "a86_verify_step.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
