"""A94 gate 1 (BOUNDARY Section 3): FastPlant against the bridges' Plant, step by step, bit for bit.

The reference Plant is imported read-only from A93's bridge (cosim/test_cosim.py, the newest copy; A89-A93 hold the
same class). Both plants get the A93 n0 plant (Params from A79 r1's run with datasheet Coss(V) and the Fig. 8 reverse
drop) and are advanced in lockstep with the same step sizes. The gate sequence is a four-phase pattern (Ton, dead
times, slots at T/4) with random jitter, so edges fall between 10 ps steps. After every step the state y, t, diode
flags, Euler counter, reverse energy and time, peak Vds, peak current and every switch's V_DS must be identical
bit for bit. Cases:
- "ramp": from the zero state at t = 0 (input ramp active, load off);
- "steady": from an A92 n0 section late in the run (vin 48 V, load on), with its flying-capacitor and output voltages.
Writes a94_step_equivalence.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
sys.path.insert(0, str(HERE))
from fast_plant import FastPlant, Params, fit_fig8  # noqa: E402

spec = importlib.util.spec_from_file_location("a93_bridge", TA / "A93_verilog_period_following_slots" / "cosim" / "test_cosim.py")
a93 = importlib.util.module_from_spec(spec); spec.loader.exec_module(a93)
RefPlant = a93.Plant
N = 4


def params():
    cfg = json.loads((TA / "A93_verilog_period_following_slots" / "cosim" / "cfg_n0_both.json").read_text())
    pr = json.loads((TA / "A93_verilog_period_following_slots" / "cosim" / cfg["init_run"]).resolve().read_text())["params"]
    keep = ("n", "vin", "L", "R", "c_high", "c_low", "cs", "co", "load_kind", "r_load", "i_load", "g_on", "h",
            "t_ramp", "t_load", "t_hand")
    vf, rr, _ = fit_fig8(10.0, 100.0)
    return Params(**{k: pr[k] for k in keep}, diode_check=True, nonlinear_coss=True, rev_drop=True, rev_vf=vf, rev_r=rr)


def schedule(rng, t0, t_end, ton=17.75e-9, period=232e-9, d_lo=1.2e-9, d_hi=9.0e-9, jit=0.3e-9):
    """(t, j, level) edges of a four-phase pattern from t0: phase k high at t0 + k*T/4 for Ton, low after d_lo,
    low off d_hi before the next high-side turn-on; every edge time jittered."""
    ev = []
    k_cyc = 0
    while True:
        base = t0 + k_cyc * period
        if base > t_end:
            break
        for k in range(N):
            th = base + k * period / N + rng.normal(0, jit)
            ev += [(th - d_hi + rng.normal(0, jit), N + k, 0), (th, k, 1), (th + ton + rng.normal(0, jit), k, 0),
                   (th + ton + d_lo + rng.normal(0, jit), N + k, 1)]
        k_cyc += 1
    return sorted(e for e in ev if t0 < e[0] < t_end)


def same(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    return a.shape == b.shape and np.array_equal(a.view(np.int64), b.view(np.int64))


def compare(r, f):
    out = []
    if not same(r.y, f.y): out.append("y")
    if r.t != f.t: out.append("t")
    if [bool(x) for x in r.diode] != [bool(x) for x in f.diode]: out.append("diode")
    if r.euler_left != f.euler_left: out.append("euler")
    if not same(r.rev_e, f.rev_e) or not same(r.rev_t, f.rev_t): out.append("rev")
    if not same(r.vds_max, f.vds_max): out.append("vds_max")
    if r.ipk != f.ipk: out.append("ipk")
    if r.steps != f.steps: out.append("steps")
    if not same([r.vds(j) for j in range(2 * N)], [f.vds(j) for j in range(2 * N)]): out.append("vds")
    return out


def run_case(name, p, y0, gh, gl, t0, n_steps, load_on, seed):
    rng = np.random.default_rng(seed)
    r = RefPlant(p, y0, gh, gl); f = FastPlant(p, y0, gh, gl)
    r.t = f.t = t0; r.load_on = f.load_on = load_on
    ev = schedule(rng, t0, t0 + n_steps * p.h * 1.05)
    steps, first_bad, tr, tf = 0, None, 0.0, 0.0
    for (te, j, lvl) in ev:
        while r.t < te - 1e-18 and steps < n_steps:
            hh = min(p.h, te - r.t)
            a = time.perf_counter(); r._advance(hh); b = time.perf_counter(); f._advance(hh); c = time.perf_counter()
            tr += b - a; tf += c - b
            steps += 1
            bad = compare(r, f)
            if bad and first_bad is None:
                first_bad = {"step": steps, "t_s": r.t, "fields": bad}
                break
        if first_bad or steps >= n_steps:
            break
        r.set_gate(j, lvl); f.set_gate(j, lvl)
    res = {"case": name, "steps": steps, "identical": first_bad is None, "first_difference": first_bad,
           "rev_steps": int(sum(1 for x in r.rev_t if x > 0)), "ipk_a": r.ipk, "vds_max_v": r.vds_max,
           "t_ref_s": tr, "t_fast_s": tf, "speedup": tr / tf if tf else None,
           "nonlinear_stats": r.sim.nl["stats"]}
    print(name, {k: res[k] for k in ("steps", "identical", "first_difference", "speedup", "ipk_a")}, flush=True)
    return res


def main():
    p = params()
    nv = 8
    out = {"cases": []}
    # case 1: zero start at t = 0, SH1 and SL2..4 on (A73's initial state), ramp active
    y0 = [0.0] * (nv + N)
    out["cases"].append(run_case("ramp", p, y0, [True] + [False] * (N - 1), [False] + [True] * (N - 1), 0.0, 100_000,
                                 False, 1))
    # case 2: from an A92 n0 section at about 300 us (vin 48 V, load on): SH1 just on, SL2..4 on
    d = json.loads((TA / "A92_verilog_error_based_correctors" / "cosim" / "run_n0_nominal.json").read_text())
    s = min(d["sections"], key=lambda x: abs(x["t_s"] - 300e-6))
    y1 = s["v"] + s["i"]
    for seed in (2, 3):
        out["cases"].append(run_case(f"steady_seed{seed}", p, y1, [True] + [False] * (N - 1), [False] + [True] * (N - 1),
                                     s["t_s"], 100_000, True, seed))
    out["all_identical"] = all(c["identical"] for c in out["cases"])
    out["total_steps"] = sum(c["steps"] for c in out["cases"])
    (HERE / "a94_step_equivalence.json").write_text(json.dumps(out, indent=1, default=float))
    print("ALL IDENTICAL" if out["all_identical"] else "DIFFERENCE FOUND", out["total_steps"], "steps")


if __name__ == "__main__":
    main()
