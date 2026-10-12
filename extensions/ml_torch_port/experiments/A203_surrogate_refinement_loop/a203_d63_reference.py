"""A203 reference: D63 itself on A120's 100 000 random designs (DD.sample(100 000, 2024), the designs A120 and A202
searched on the surrogate), each on the 8 standard transients. Writes tmp/a203/d63_100k.npz (peak, extreme, depth,
periods, diverged, time back per transient) and a203_reference.json (counts, the feasible designs, the best); prints <= 15 lines.

    PYTHONPATH=src python3 .../a203_d63_reference.py [--jobs 8] [--n 100000]        (numpy only)"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
A120 = PROJECT / "extensions" / "ml_design_assist" / "experiments" / "A120_d63_surrogate_mlp"
sys.path.insert(0, str(A120))

from explore_a120 import STANDARD, verdict  # noqa: E402

from scb_ivr.extensions import ml_d63_data as DD  # noqa: E402

TMP = PROJECT / "tmp" / "a203"
ITH = tuple(tuple(v) for v in json.loads(DD.D63_DIAG.read_text())["thresholds"][str(DD.L1)])
TTR = json.loads(str(np.load(A120 / "a120_dataset.npz")["ttr"]))


def run_design(d):
    """(8, 6): peak, extreme, depth, periods, diverged, time back for one design on the standard transients."""
    out = np.empty((len(STANDARD), 6))
    for t, (k, di, dv, sl) in enumerate(STANDARD):
        r = DD.evaluate((dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl), ITH, TTR))
        out[t] = (r["peak_a"], r["extreme_mv"], r["ph1_depth_a"], r["ph1_periods"], float(r["diverged"]), r["back_us"])
    return out


def judge(res):
    """f1, f2, feasible (A120's verdict, and no transient diverged) from (n, 8, 6) D63 results."""
    div = res[:, :, 4].any(axis=1)
    f1, f2 = res[:, :, 0].max(axis=1), np.abs(res[:, :, 1]).max(axis=1)
    feas = np.array([(not div[i]) and verdict(res[i, :, 0], res[i, :, 2], res[i, :, 3]) for i in range(len(res))])
    return f1, f2, feas, div


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--n", type=int, default=100_000)
    a = ap.parse_args()
    designs = DD.sample(a.n, 2024)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        res = np.array(list(ex.map(run_design, designs, chunksize=64)))
    secs = time.time() - t0
    f1, f2, feas, div = judge(res)
    if a.n < 100_000:
        print(f"smoke ok: {a.n} designs in {secs:.1f} s on {a.jobs} jobs -> 100 000 in {secs / a.n * 1e5 / 60:.1f} min")
        return
    TMP.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(TMP / "d63_100k.npz", res=res.astype(np.float32))
    idx = np.nonzero(feas)[0]
    best = int(idx[np.argmin(f1[idx])])
    out = {"n": a.n, "seed": 2024, "seconds": secs, "jobs": a.jobs, "diverged": int(div.sum()), "feasible": int(feas.sum()),
           "by_rule": {r: int(sum(designs[i]["rule"] == r for i in idx)) for r in DD.RULES},
           "best": {"index": best, "f1": float(f1[best]), "f2": float(f2[best]), **designs[best]},
           "feasible_designs": [{"index": int(i), "f1": float(f1[i]), "f2": float(f2[i]), **designs[i]} for i in idx[np.argsort(f1[idx])]]}
    (HERE / "a203_reference.json").write_text(json.dumps(out, indent=1) + "\n")
    b = out["best"]
    print(f"D63 on {a.n} designs x 8 transients: {secs / 60:.1f} min on {a.jobs} jobs; {out['diverged']} with a diverged transient")
    print(f"feasible in D63: {out['feasible']} ({out['feasible'] / a.n:.2%}), by rule {out['by_rule']}")
    print(f"best: worst peak {b['f1']:.2f} A, worst |Vo extreme| {b['f2']:.1f} mV: {b['rule']} pct {b['pct']:.2f}, Cs {b['cs_uf']:.2f} uF, "
          f"fc {b['fc_khz']:.1f} kHz, floor {b['floor_a']:.2f} A")
    q = np.percentile(f1[idx], [10, 50, 90])
    print(f"feasible designs' worst peak: 10 / 50 / 90 % = {q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} A")


if __name__ == "__main__":
    main()
