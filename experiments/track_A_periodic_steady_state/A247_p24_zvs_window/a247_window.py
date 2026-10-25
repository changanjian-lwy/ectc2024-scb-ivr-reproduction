"""A247 physics: D57's free node after a low-side turn-off at i_off (A, + into the inductor), no turn-on, as the whole
trace V_DS(t) = rail - x(t) on 0-40 ns (EPC2067 Coss, both sides' reverse conduction; the same model and solver settings
as p24_valley_map.von_point, A148). Boards by L: N0 2.933 nH, N75 / S75h 2.2 nH. Node: phases 2-3 carry the next
phase's high side biased at the rail times D63's ratio (EdgeCircuit dv_cs / v_rail); phase 4 has none (last).
Windows on the grid: the delays with V_DS <= V_SOFT (and <= 0), the valley's time and V_DS.
  python3 a247_window.py [--jobs 10] [--smoke] -> tmp/a247_window.npz (traces), a247_window.json (windows)"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
LF = (2.9333333e-9, 2.2e-9)                      # N0; N75 / S75h
LAST = (False, True)                             # phases 2-3; phase 4
RAILS = np.arange(6.0, 20.01, 1.0)
CURRENTS = np.arange(-100.0, 30.01, 2.0)
T_NS = np.arange(0.0, 40.0001, 0.05)
V_SOFT = 2.0                                     # V: a soft turn-on (BOUNDARY Section 2)


def trace(args):
    """V_DS(t) on T_NS for one (lf, last, rail, i_off)."""
    from scipy.integrate import solve_ivp
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import node_model
    lf, last, rail, i_off = args
    e = EdgeCircuit()
    k = e.dv_cs / e.v_rail
    m = node_model(replace(e, lf=lf, v_rail=float(rail), dv_cs=0.0 if last else float(rail) * k,
                           n_next=0 if last else e.n_next))
    s = solve_ivp(m._rhs_free(None), (0.0, T_NS[-1] * 1e-9), [0.0, float(i_off), 0.0], max_step=2e-12, rtol=1e-9,
                  atol=1e-7, dense_output=True)
    return (rail - s.sol(T_NS * 1e-9)[0]).astype(np.float32)


def window(v, level):
    """(first, last) time in ns of the first run of v <= level, or None."""
    idx = np.flatnonzero(v <= level)
    if idx.size == 0:
        return None
    j = idx[0]
    end = j
    while end + 1 < v.size and v[end + 1] <= level:
        end += 1
    return float(T_NS[j]), float(T_NS[end])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    tasks = [(lf, last, float(r), float(i)) for lf in LF for last in LAST for r in RAILS for i in CURRENTS]
    if a.smoke:
        t0 = time.time()
        for t in tasks[:: len(tasks) // 4][:4]:
            trace(t)
        print(f"smoke: {(time.time() - t0) / 4:.2f} s per trace, {len(tasks)} traces")
        return
    from multiprocessing import Pool
    with Pool(a.jobs) as p:
        tr = np.array(p.map(trace, tasks, chunksize=8)).reshape(len(LF), len(LAST), len(RAILS), len(CURRENTS), -1)
    out = PROJECT / "tmp" / "a247_window.npz"
    np.savez_compressed(out, traces=tr, lf=np.array(LF), last=np.array(LAST), rails=RAILS, currents=CURRENTS, t_ns=T_NS)
    win = []
    for a_, lf in enumerate(LF):
        for b_, last in enumerate(LAST):
            for c_, r in enumerate(RAILS):
                for d_, i in enumerate(CURRENTS):
                    v = tr[a_, b_, c_, d_]
                    j = int(np.argmin(v))
                    win.append({"lf_nh": round(lf * 1e9, 4), "last": last, "rail_v": float(r), "i_off_a": float(i),
                                "soft": window(v, V_SOFT), "zero": window(v, 0.0),
                                "t_min_ns": float(T_NS[j]), "v_min_v": round(float(v[j]), 3)})
    (HERE / "a247_window.json").write_text(json.dumps({"v_soft_v": V_SOFT, "windows": win}) + "\n")
    print(len(win), "windows ->", out.relative_to(PROJECT))


if __name__ == "__main__":
    main()
