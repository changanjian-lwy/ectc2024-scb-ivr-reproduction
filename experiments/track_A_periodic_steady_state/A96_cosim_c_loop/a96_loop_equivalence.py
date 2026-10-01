"""A96 gate 1: KernelPlant2 (the step loop and the bridge's per-step monitors in C) against ReferencePlant stepped in
Python with the same monitors in Python, bit for bit.

Both plants get the P24 plant (datasheet Coss(V), reverse drop) and the same jittered four-phase gate pattern. At
each gate edge the test does what the bridge does: a high-side turn-off starts that phase's zero-crossing TDC, a
low-side turn-off starts its high side's valley tracking (both cleared at the corresponding turn-on); and a latch
(i1 <= threshold) is armed in some intervals and fires a callback that records the time. Between edges the reference
steps one 10 ps step at a time with Monitors.py_step; KernelPlant2 integrates in C. After each interval: y, t, diode
flags, Euler counter, steps, reverse energy and time, peak V_DS and current, every V_DS, and every monitor array
must be identical, and the latch must fire at the same step. Cases: zero start (input ramp) and two A92 n0 sections.
Writes a96_loop_equivalence.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "tests"))
from scb_ivr.cosim.plant import KernelPlant2, Monitors, ReferencePlant  # noqa: E402
from test_cosim_plants import bits, params, schedule  # noqa: E402

N = 4
MON = ("hoff_set", "cross_set", "vprev_valid", "vmin_set", "t_hoff", "t_cross", "v_prev", "t_prev", "vmin", "t_vmin")


def state(pl, mon):
    return {"y": bits(pl.y), "t": pl.t, "diode": [bool(x) for x in pl.diode], "euler": pl.euler_left, "steps": pl.steps,
            "rev": bits(list(pl.rev_e) + list(pl.rev_t)), "vmax": bits(pl.vds_max), "ipk": pl.ipk,
            "vds": bits([pl.vds(j) for j in range(2 * N)]), **{k: bits(getattr(mon, k)) for k in MON}}


def run_case(name, p, y0, t0, load_on, n_events, seed):
    rng = np.random.default_rng(seed)
    gh, gl = [True] + [False] * (N - 1), [False] + [True] * (N - 1)
    r, f = ReferencePlant(p, y0, gh, gl), KernelPlant2(p, y0, gh, gl)
    mr, mf = Monitors(N), Monitors(N)
    f.attach_monitors(mf)
    r.t = f.t = t0; r.load_on = f.load_on = load_on
    ev = schedule(rng, t0, t0 + 3e-6)[:n_events]
    fires_r, fires_f = [], []
    first_bad, tr, tf = None, 0.0, 0.0
    for idx, (te, j, lvl) in enumerate(ev):
        armed = (idx % 3 == 0)
        thr = float(r.y[r.nv]) - 0.5                     # fires once the current falls 0.5 A below its value here
        lr = {"armed": armed}

        def r_step():
            mr.py_step(r)
            if lr["armed"] and r.y[r.nv] <= thr:
                lr["armed"] = False; fires_r.append(r.t)
        a = time.perf_counter()
        r.integrate_to(te, r_step)
        b = time.perf_counter()
        f.integrate_to(te, None, monitors=mf, latch=(armed, thr, lambda: fires_f.append(f.t)))
        c = time.perf_counter()
        tr += b - a; tf += c - b
        sr, sf = state(r, mr), state(f, mf)
        bad = [k for k in sr if sr[k] != sf[k]] + (["latch"] if fires_r != fires_f else [])
        if bad:
            first_bad = {"event": idx, "t_s": r.t, "fields": bad}
            break
        k = j % N                                        # the bridge's monitor starts and clears at this edge
        for mon, pl in ((mr, r), (mf, f)):
            if j < N and level_on(lvl):                  # high-side turn-on: valley tracking cleared
                mon.vmin_set[k] = 0
            if j < N and not level_on(lvl):              # high-side turn-off: zero-crossing TDC starts
                mon.hoff_set[k] = 1; mon.t_hoff[k] = pl.t; mon.cross_set[k] = 0; mon.vprev_valid[k] = 0
            if j >= N and level_on(lvl):                 # low-side turn-on: TDC cleared
                mon.hoff_set[k] = 0; mon.cross_set[k] = 0
            if j >= N and not level_on(lvl):             # low-side turn-off: valley tracking starts
                mon.vmin_set[k] = 1; mon.vmin[k] = pl.vds(k); mon.t_vmin[k] = pl.t
        r.set_gate(j, lvl); f.set_gate(j, lvl)
    res = {"case": name, "events": idx + 1, "steps": r.steps, "identical": first_bad is None, "first_difference": first_bad,
           "latch_fires": len(fires_r), "t_ref_s": tr, "t_c_s": tf, "speedup_vs_reference": tr / tf if tf else None,
           "chord_iters_c": int(f._run.chord_iters), "table_entries": len(f._table_keep)}
    print(name, {k: res[k] for k in ("events", "steps", "identical", "first_difference", "latch_fires", "speedup_vs_reference")},
          flush=True)
    return res


def level_on(lvl):
    return bool(lvl)


def main():
    p = params()
    out = {"cases": [run_case("ramp", p, [0.0] * (3 * N), 0.0, False, 120, 1)]}
    d = json.loads((PROJECT / "experiments" / "track_A_periodic_steady_state" / "A92_verilog_error_based_correctors" / "cosim"
                    / "run_n0_nominal.json").read_text())
    for seed, t in ((2, 300e-6), (3, 200e-6)):
        s = min(d["sections"], key=lambda x: abs(x["t_s"] - t))
        out["cases"].append(run_case(f"steady_{int(t * 1e6)}us", p, s["v"] + s["i"], s["t_s"], True, 120, seed))
    out["all_identical"] = all(c["identical"] for c in out["cases"])
    (HERE / "a96_loop_equivalence.json").write_text(json.dumps(out, indent=1, default=float))
    print("ALL IDENTICAL" if out["all_identical"] else "DIFFERENCE FOUND")


if __name__ == "__main__":
    main()
