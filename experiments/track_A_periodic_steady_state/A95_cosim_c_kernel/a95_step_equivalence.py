"""A95 gate 1: KernelPlant against the bridges' original Plant (A93's bridge), step by step, bit for bit.

Same procedure, cases and comparisons as A94's a94_step_equivalence.py (imported read-only): four-phase gate pattern
with jitter, from the zero state with the input ramp and from two A92 n0 sections at about 300 us; after every step
y, t, diode flags, Euler counter, reverse energy and time, peak Vds, peak current and every V_DS must be identical.
Adds a third, longer steady case and reports how many steps the C kernel handed back to Python. Writes
a95_step_equivalence.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
sys.path.insert(0, str(TA / "A94_cosim_plant_speedup"))
sys.path.insert(0, str(HERE))
import a94_step_equivalence as E  # noqa: E402
from kernel_plant import KernelPlant  # noqa: E402

N = 4


def run_case(name, p, y0, gh, gl, t0, n_steps, load_on, seed):
    rng = np.random.default_rng(seed)
    r = E.RefPlant(p, y0, gh, gl); f = KernelPlant(p, y0, gh, gl)
    r.t = f.t = t0; r.load_on = f.load_on = load_on
    ev = E.schedule(rng, t0, t0 + n_steps * p.h * 1.05)
    steps, first_bad, tr, tf = 0, None, 0.0, 0.0
    for (te, j, lvl) in ev:
        while r.t < te - 1e-18 and steps < n_steps:
            hh = min(p.h, te - r.t)
            a = time.perf_counter(); r._advance(hh); b = time.perf_counter(); f._advance(hh); c = time.perf_counter()
            tr += b - a; tf += c - b
            steps += 1
            bad = E.compare(r, f)
            if bad and first_bad is None:
                first_bad = {"step": steps, "t_s": r.t, "fields": bad}
                break
        if first_bad or steps >= n_steps:
            break
        r.set_gate(j, lvl); f.set_gate(j, lvl)
    res = {"case": name, "steps": steps, "identical": first_bad is None, "first_difference": first_bad,
           "t_ref_s": tr, "t_kernel_s": tf, "speedup_vs_original": tr / tf if tf else None,
           "kernel_stats": f.sim.kernel_stats, "nonlinear_stats_ref": r.sim.nl["stats"]}
    print(name, {k: res[k] for k in ("steps", "identical", "first_difference", "speedup_vs_original", "kernel_stats")},
          flush=True)
    return res


def main():
    p = E.params()
    out = {"cases": []}
    nv = 8
    out["cases"].append(run_case("ramp", p, [0.0] * (nv + N), [True] + [False] * (N - 1), [False] + [True] * (N - 1),
                                 0.0, 100_000, False, 1))
    d = json.loads((TA / "A92_verilog_error_based_correctors" / "cosim" / "run_n0_nominal.json").read_text())
    s = min(d["sections"], key=lambda x: abs(x["t_s"] - 300e-6))
    for seed, n in ((2, 100_000), (3, 100_000), (4, 200_000)):
        out["cases"].append(run_case(f"steady_seed{seed}", p, s["v"] + s["i"], [True] + [False] * (N - 1),
                                     [False] + [True] * (N - 1), s["t_s"], n, True, seed))
    out["all_identical"] = all(c["identical"] for c in out["cases"])
    out["total_steps"] = sum(c["steps"] for c in out["cases"])
    (HERE / "a95_step_equivalence.json").write_text(json.dumps(out, indent=1, default=float))
    print("ALL IDENTICAL" if out["all_identical"] else "DIFFERENCE FOUND", out["total_steps"], "steps")


if __name__ == "__main__":
    main()
