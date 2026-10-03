"""A120 exploration (after the registered checks, not a criterion): the surrogate searches 100 000 random 1 MHz designs
on the 8 standard transients (+-62.5 A; +-4.8 V over 1, 5 and 20 us), finds the feasible region (every peak <= 200 A,
phase 1 inside D63's refitted rule), and D63 re-checks the surrogate's best and borderline designs. A design's margin is
200 A minus its worst peak. Writes a120_explore.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions import ml_d63_data as DD  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP, Scaler  # noqa: E402

STANDARD = [("load", -62.5, 0.0, 1.0), ("load", 62.5, 0.0, 1.0)] + [("line", 0.0, dv, s) for s in (1.0, 5.0, 20.0) for dv in (4.8, -4.8)]


def verdict(peaks, depth, periods):
    return bool(np.all(peaks <= 200.0) and not np.any((depth > 12.0) & (periods >= 25)))


def main():
    net, z = MLP.load(HERE / "a120_mlp.npz")
    sx, sy = Scaler(z["x_mean"], z["x_sd"]), Scaler(z["y_mean"], z["y_sd"])
    ttr = json.loads(str(np.load(HERE / "a120_dataset.npz")["ttr"]))
    ith = tuple(tuple(v) for v in json.loads(DD.D63_DIAG.read_text())["thresholds"][str(DD.L1)])
    designs = DD.sample(100_000, 2024)
    feats = DD.features([dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl) for d in designs for k, di, dv, sl in STANDARD])
    p = sy.inv(net.predict(sx.fwd(feats))).reshape(len(designs), len(STANDARD), -1)
    peaks, depth, periods = p[:, :, 0], p[:, :, 2], np.expm1(p[:, :, 3])
    worst = peaks.max(axis=1)
    feas = np.array([verdict(peaks[i], depth[i], periods[i]) for i in range(len(designs))])
    print(f"surrogate: {feas.sum()} of {len(designs)} designs feasible ({feas.mean():.2%})")
    rows = [dict(designs[i], worst_peak_a=float(worst[i])) for i in np.nonzero(feas)[0]]
    out = {"n": len(designs), "feasible": int(feas.sum())}
    if rows:
        for key in ("rule",):
            from collections import Counter
            c = Counter(r[key] for r in rows)
            out["by_rule"] = dict(c)
            print("feasible by rule:", dict(c))
        a = np.array([[r["pct"], r["cs_uf"], r["fc_khz"], r["floor_a"]] for r in rows])
        out["ranges"] = {k: [float(a[:, j].min()), float(np.median(a[:, j])), float(a[:, j].max())] for j, k in
                         enumerate(("pct", "cs_uf", "fc_khz", "floor_a"))}
        print("feasible ranges [min, median, max]:", {k: [round(v, 1) for v in vals] for k, vals in out["ranges"].items()})
    # by rule: the share feasible against Cs and the fraction of designs per Cs band
    bands = [(3, 5), (5, 8), (8, 12), (12, 20)]
    out["share_by_rule_cs"] = {}
    for rule in DD.RULES:
        sel = np.array([d["rule"] == rule for d in designs])
        cs = np.array([d["cs_uf"] for d in designs])
        out["share_by_rule_cs"][rule] = {f"{lo}-{hi}": float(feas[sel & (cs >= lo) & (cs < hi)].mean()) for lo, hi in bands}
    print("feasible share by rule and Cs band:", {r: {k: f"{v:.1%}" for k, v in b.items()} for r, b in out["share_by_rule_cs"].items()})
    # D63 re-checks the 15 best (largest margin) and 15 borderline (worst peak 190-200 A) surrogate-feasible designs
    idx = np.nonzero(feas)[0]
    best = idx[np.argsort(worst[idx])[:15]]
    border = [i for i in idx if 190 <= worst[i] <= 200][:15]
    checks = []
    for tag, group in (("best", best), ("border", border)):
        for i in group:
            d = designs[i]
            res = [DD.evaluate((dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl), ith, ttr)) for k, di, dv, sl in STANDARD]
            ok = all(not r["diverged"] for r in res)
            f = ok and verdict(np.array([r["peak_a"] for r in res]), np.array([r["ph1_depth_a"] for r in res]),
                               np.array([r["ph1_periods"] for r in res]))
            checks.append({"tag": tag, "design": {k: d[k] for k in ("pct", "cs_uf", "fc_khz", "rule", "floor_a")},
                           "mlp_worst_a": float(worst[i]), "d63_worst_a": max(r["peak_a"] for r in res) if ok else math.inf,
                           "d63_feasible": f})
    for tag in ("best", "border"):
        cc = [c for c in checks if c["tag"] == tag]
        if cc:
            print(f"D63 re-check of the surrogate's {tag} designs: {sum(c['d63_feasible'] for c in cc)} of {len(cc)} feasible; "
                  f"worst peak MLP {np.mean([c['mlp_worst_a'] for c in cc]):.1f} A vs D63 {np.mean([c['d63_worst_a'] for c in cc]):.1f} A")
    for c in checks[:15]:
        d = c["design"]
        print(f"   {d['rule']:5s} pct {d['pct']:4.1f}, Cs {d['cs_uf']:4.1f} uF, fc {d['fc_khz']:4.1f} kHz, floor {d['floor_a']:.1f} A: "
              f"MLP {c['mlp_worst_a']:.0f} A, D63 {c['d63_worst_a']:.0f} A, D63 feasible {c['d63_feasible']}")
    out["checks"] = checks
    # the same search with the bus slew limited to >= 5 us (the 1 us line steps left out)
    keep = [j for j, (k, di, dv, sl) in enumerate(STANDARD) if not (k == "line" and sl < 5)]
    feas5 = np.array([verdict(peaks[i, keep], depth[i, keep], periods[i, keep]) for i in range(len(designs))])
    cs = np.array([d["cs_uf"] for d in designs]); pct = np.array([d["pct"] for d in designs])
    out["slew_ge_5us"] = {"feasible": int(feas5.sum()), "share_by_rule_cs": {
        rule: {f"{lo}-{hi}": float(feas5[np.array([d["rule"] == rule for d in designs]) & (cs >= lo) & (cs < hi)].mean())
               for lo, hi in bands} for rule in DD.RULES},
        "share_by_rule_pct": {rule: {f"{lo}-{hi}": float(feas5[np.array([d["rule"] == rule for d in designs]) & (pct >= lo) & (pct < hi)].mean())
                                     for lo, hi in ((5, 8), (8, 11), (11, 15))} for rule in DD.RULES}}
    print(f"bus slew >= 5 us: {feas5.sum()} of {len(designs)} feasible ({feas5.mean():.1%})")
    print("   by rule and Cs band:", {r: {k: f"{v:.0%}" for k, v in b.items()} for r, b in out["slew_ge_5us"]["share_by_rule_cs"].items()})
    print("   by rule and pct band:", {r: {k: f"{v:.0%}" for k, v in b.items()} for r, b in out["slew_ge_5us"]["share_by_rule_pct"].items()})
    (HERE / "a120_explore.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
