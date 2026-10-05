"""A146 data: double-pulse turn-offs of SH1 in A145's single-edge harness (the cosim plant, FastPlant, with A145's
finite edges) with random loop inductance L, damping Q, edge rate didt, turn-off current I0 and Coss spread k.
V_DS of SH1 from the gate edge for T_WIN at the plant's 10 ps step, kept every 2nd sample (20 ps).

    PYTHONPATH=src python3 .../a146_data.py [--n 24000] [--jobs 10]   -> tmp/a146/traces.npz (git-ignored)

trace(theta) is shared with the Cramer-Rao check and the simulator fit (a146_baselines.py). The measurement model
(probe low-pass, sampling, noise, trigger jitter, current-sense error) is applied later (measure())."""
from __future__ import annotations

import argparse
import dataclasses
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A145_p24_finite_switching_edges"))
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
from a144_edge import params, q_rp, y0  # noqa: E402

from scb_ivr.cosim.plant import FastPlant  # noqa: E402

OUT = PROJECT / "tmp" / "a146"
T_ON, T_WIN, H, KEEP = 2e-9, 32e-9, 10e-12, 2
# ranges: L pH, Q, didt A/ns (log-uniform); I0 A, k (uniform)
RANGES = {"l_ph": (25.0, 300.0), "q": (2.0, 30.0), "didt": (36.0, 576.0), "i0": (60.0, 200.0), "k": (0.85, 1.15)}
LOGS = ("l_ph", "q", "didt")
V_RAIL = 12.0


def sample(n, rng):
    out = {}
    for nm, (a, b) in RANGES.items():
        out[nm] = np.exp(rng.uniform(np.log(a), np.log(b), n)) if nm in LOGS else rng.uniform(a, b, n)
    return out


def trace(l_ph, q, didt, i0, k):
    """V_DS of SH1 (V) every KEEP x 10 ps from the gate edge, T_WIN long."""
    p = params(l_ph, q_rp(l_ph * 1e-12, q))
    p = dataclasses.replace(p, edge_didt_off=didt * 1e9, edge_didt_on=didt * 1e9, coss_scale=k,
                            c_high=p.c_high * k, c_low=p.c_low * k)
    pl = FastPlant(p, y0(p, i0), gh=[True, False, False, False], gl=[False, True, True, True])
    pl.integrate_to(T_ON, lambda: None)
    pl.set_gate(0, False)
    v = []
    pl.integrate_to(T_ON + T_WIN, lambda: v.append(float(pl.vds(0))))
    return np.asarray(v[KEEP - 1::KEEP], dtype=np.float64)


def _one(row):
    return trace(*row).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24000)
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    th = sample(a.n, np.random.default_rng(146))
    rows = list(zip(*(th[k] for k in RANGES)))
    t0 = time.time()
    with Pool(a.jobs) as pool:
        x = np.stack(pool.map(_one, rows, chunksize=50))
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / "traces.npz", v=x, dt=H * KEEP, **{k: th[k] for k in RANGES})
    print(f"{a.n} traces x {x.shape[1]} samples in {time.time() - t0:.0f} s; V_DS {x.min():.1f}..{x.max():.1f} V")


if __name__ == "__main__":
    main()
