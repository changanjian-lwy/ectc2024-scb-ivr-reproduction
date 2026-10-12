"""A204: the disagreement between A201's ten networks as a guard and as an interval scale. Uses A201's stored
predictions (runs/pred_s*.npz) and A199's dataset for the true values; no training. Writes a204_summary.json;
prints <= 15 lines.

    PYTHONPATH=src python3 .../a204_spread.py [--smoke]        (numpy only)

spread   s(x): the standard deviation of the ten predictions of a capture, per parameter
guard    g(x) = max over the four parameters of s / (the calibration set's median s); a capture is flagged when g
         exceeds the calibration set's 95th percentile of g
scaled   intervals mean +- q (s + s0), s0 = the calibration median of s, q = the split-conformal rank of
         |mean - y| / (s + s0) on the calibration set (normalised conformal), against A201's fixed mean +- q
Rows: the test set (inside the training conditions) and A146's four robustness rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A201 = HERE.parent / "A201_cnn_seed_ensemble"
sys.path.insert(0, str(A201))

from a201_common import ROB, conformal_q, dataset, errors  # noqa: E402

NAMES = ("L", "Q_act", "di/dt", "k")
BAND, FLAG_BAND, FLAG_MIN, ROW_MIN = (0.87, 0.93), (0.03, 0.07), 0.50, 0.75
OUT_ROWS = ("noise_0p8", "probe_0p5ghz")                           # the rows whose captures themselves differ


def main():
    smoke = "--smoke" in sys.argv
    d = dataset()
    preds = [dict(np.load(p)) for p in sorted((A201 / "runs").glob("pred_s*.npz"))]
    sets = {"cal": ("ca", d["yca"]), "test": ("te", d["yte"]), **{nm: (nm, d["yte"][:1000]) for nm in ROB}}
    mean = {k: np.mean([p[src].astype(np.float64) for p in preds], axis=0) for k, (src, _) in sets.items()}
    sd = {k: np.std([p[src].astype(np.float64) for p in preds], axis=0, ddof=1) for k, (src, _) in sets.items()}
    y = {k: v for k, (_, v) in sets.items()}
    if smoke:
        print(f"smoke ok: {len(preds)} networks, sets {[(k, v.shape) for k, v in mean.items()][:2]}")
        return
    s0 = np.median(sd["cal"], axis=0)
    g = {k: (sd[k] / s0).max(axis=1) for k in sets}
    thr = float(np.percentile(g["cal"], 95))
    q_fix = conformal_q(mean["cal"], y["cal"])
    q_scl = conformal_q(mean["cal"] / (sd["cal"] + s0), y["cal"] / (sd["cal"] + s0))     # |mean - y| / (s + s0)
    rows = {}
    for k in sets:
        if k == "cal":
            continue
        res = np.abs(mean[k] - y[k])
        half = q_scl * (sd[k] + s0)
        flag = g[k] > thr
        e = np.abs(errors(mean[k], y[k]))
        rows[k] = {"n": len(res), "flagged": float(flag.mean()), "cover_fixed": (res <= q_fix).mean(axis=0).tolist(),
                   "cover_scaled": (res <= half).mean(axis=0).tolist(), "width_ratio": (np.median(half, axis=0) / q_fix).tolist(),
                   "spread_ratio": (np.median(sd[k], axis=0) / s0).tolist(), "median_err": np.median(e, axis=0).tolist(),
                   "median_err_unflagged": np.median(e[~flag], axis=0).tolist() if (~flag).any() else None,
                   "cover_fixed_unflagged": (res[~flag] <= q_fix).mean(axis=0).tolist() if (~flag).any() else None,
                   # does the spread rank the errors? Spearman rank correlation of s with |mean - y|, per parameter
                   "rank_corr": [float(np.corrcoef(np.argsort(np.argsort(sd[k][:, j])), np.argsort(np.argsort(res[:, j])))[0, 1]) for j in range(4)]}
    t = rows["test"]
    crit = {"c1_scaled_cover_in_range": {"cover": t["cover_scaled"], "pass": bool(min(t["cover_scaled"]) >= BAND[0] and max(t["cover_scaled"]) <= BAND[1])},
            "c2_false_flags": {"flagged": t["flagged"], "pass": bool(FLAG_BAND[0] <= t["flagged"] <= FLAG_BAND[1])},
            "c3_flags_out_of_range": {r: rows[r]["flagged"] for r in OUT_ROWS},
            "c4_scaled_cover_out_of_range": {r: rows[r]["cover_scaled"] for r in OUT_ROWS}}
    crit["c3_flags_out_of_range"]["pass"] = bool(all(rows[r]["flagged"] >= FLAG_MIN for r in OUT_ROWS))
    crit["c4_scaled_cover_out_of_range"]["pass"] = bool(all(min(rows[r]["cover_scaled"]) >= ROW_MIN for r in OUT_ROWS))
    out = {"networks": len(preds), "threshold_g": thr, "s0": s0.tolist(), "q_fixed": q_fix.tolist(), "q_scaled": q_scl.tolist(),
           "criteria": crit, "passed": int(sum(c["pass"] for c in crit.values())), "of": len(crit), "rows": rows}
    (HERE / "a204_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    f = lambda xs, n=3: " / ".join(f"{x:.{n}f}" for x in xs)
    ok = lambda c: "PASS" if crit[c]["pass"] else "FAIL"
    print(f"A204: {out['passed']} of {out['of']} criteria pass; {len(preds)} networks; parameters {' / '.join(NAMES)}")
    print(f"C1 {ok('c1_scaled_cover_in_range')} scaled intervals on the test set: cover {f(t['cover_scaled'])} (fixed {f(t['cover_fixed'])}), "
          f"median width / fixed {f(t['width_ratio'], 2)}")
    print(f"C2 {ok('c2_false_flags')} flagged on the test set: {t['flagged']:.3f}; spread ranks the error there (rank correlation) {f(t['rank_corr'], 2)}")
    for r in ROB:
        v = rows[r]
        print(f"  {r}: flagged {v['flagged']:.2f}; spread x{f(v['spread_ratio'], 1)}; cover fixed {f(v['cover_fixed'], 2)} -> scaled {f(v['cover_scaled'], 2)}"
              f"; unflagged fixed {f(v['cover_fixed_unflagged'], 2) if v['cover_fixed_unflagged'] else 'none'}")
    print(f"C3 {ok('c3_flags_out_of_range')} flags >= {FLAG_MIN:.0%} in the noise and probe rows | C4 {ok('c4_scaled_cover_out_of_range')} scaled cover >= {ROW_MIN} there")


if __name__ == "__main__":
    main()
