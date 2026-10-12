"""A201 analysis: A146's five criteria for every seed, for the ensemble (the mean of the seeds' predictions) and for
A146's stored numpy network (the control), then A201's own criteria (BOUNDARY.md). Writes a201_summary.json; prints
<= 15 lines.

    PYTHONPATH=src python3 .../a201_analyze.py        (numpy only)"""
from __future__ import annotations

import json
from itertools import combinations

import numpy as np
from a201_common import HERE, N_FIT, ROB, a146_criteria, conformal_q, dataset, errors, extra, load_json, reference

FAIL_ROWS, PASS_ROWS = ("noise_0p8", "probe_0p5ghz", "ierr_5pct"), ("jitter_150ps",)
SIZES = (1, 2, 3, 5, 10)


def theta(fits):
    return np.array([[np.log(f["l_ph"]), np.log(f["q_act"]), np.log(f["didt"]), f["k"]] for f in fits])


def fit_block(fits, name, p_ca, p_te, d):
    q = conformal_q(p_ca, d["yca"])
    p_f = theta(fits[name])
    return {"within": (np.abs(p_f - p_te[:N_FIT]) <= q).mean(axis=0).tolist(),
            "median_err": np.median(np.abs(errors(p_f, d["yte"][:N_FIT])), axis=0).tolist(),
            "nfev": float(np.mean([f["nfev"] for f in fits[name]])), "nfev_centre": float(np.mean([f["nfev"] for f in fits["centre"]])),
            "cost": float(np.median([f["cost"] for f in fits[name]])), "cost_centre": float(np.median([f["cost"] for f in fits["centre"]]))}


def rel(a, b):
    return float(np.max(np.abs(np.asarray(a, float) - np.asarray(b, float)) / np.abs(np.asarray(b, float))))


def main():
    d, ex = dataset(), extra()
    net, sc, _, ref = reference()
    fits = load_json(HERE / "a201_fits.json")
    sine = ref["sine"]["median_err"]
    pr = lambda x: sc.inv(net.predict(x))
    est = {}
    num = a146_criteria(pr(d["xca"]), pr(d["xte"]), {nm: pr(ex[f"rob_{nm}"]) for nm in ROB}, d, sine,
                        fit_block(fits, "numpy", pr(d["xca"]), pr(d["xte"]), d))
    preds = {p.stem[5:]: {k: v.astype(np.float64) for k, v in np.load(p).items()} for p in sorted((HERE / "runs").glob("pred_s*.npz"))}
    seeds = sorted(preds, key=lambda s: int(s[1:]))
    for s in seeds:
        p = preds[s]
        est[s] = a146_criteria(p["ca"], p["te"], {nm: p[nm] for nm in ROB}, d, sine, fit_block(fits, s, p["ca"], p["te"], d))
    mean = {k: np.mean([preds[s][k] for s in seeds], axis=0) for k in ("ca", "te", *ROB)}
    ens = a146_criteria(mean["ca"], mean["te"], {nm: mean[nm] for nm in ROB}, d, sine, fit_block(fits, "ens", mean["ca"], mean["te"], d))
    # control: the stored numpy network through this pipeline against A146's stored numbers
    ctrl = max(rel(num["fit"]["within"], ref["fit_cnn_start"]["within_cnn_interval"]), rel(num["fit"]["nfev"], ref["fit_cnn_start"]["nfev_mean"]),
               rel(num["fit"]["nfev_centre"], ref["fit_centre"]["nfev_mean"]), rel(num["fit"]["cost"], ref["fit_cnn_start"]["cost_med"]),
               rel(num["fit"]["cost_centre"], ref["fit_centre"]["cost_med"]), rel(num["median_err"], ref["cnn"]["median_err"]),
               *(rel(num["robust"][nm][k], ref["robust"][nm][k]) for nm in ROB for k in ("median_err", "cover90")))
    med = np.array([est[s]["median_err"] for s in seeds])
    cov = np.array([est[s]["cover90"] for s in seeds])
    pattern = lambda e: all(not e["c5_rows"][r] for r in FAIL_ROWS) and all(e["c5_rows"][r] for r in PASS_ROWS)
    ratio = np.array(ens["median_err"]) / med.mean(axis=0)
    # error against the number of networks averaged: the mean over all subsets (at most 120) of each size
    yte, curve = d["yte"], {}
    for k in SIZES:
        if k > len(seeds):
            continue
        subs = list(combinations(seeds, k))[:120]
        curve[k] = np.mean([np.median(np.abs(errors(np.mean([preds[s]["te"] for s in sub], axis=0), yte)), axis=0) for sub in subs], axis=0).tolist()
    crit = {"c1_control": {"max_rel": ctrl, "pass": ctrl <= 1e-6},
            "c2_a146_c1_c3_all_seeds": {"counts": {c: int(sum(est[s][c] for s in seeds)) for c in ("c1", "c2", "c3")},
                                        "pass": all(est[s][c] for s in seeds for c in ("c1", "c2", "c3"))},
            "c3_ensemble_error": {"ratio_to_seed_mean": ratio.tolist(), "cover": ens["cover90"],
                                  "pass": bool(np.all(ratio[:3] <= 0.90) and ratio[3] <= 1.00 and ens["c2"])},
            "c4_ensemble_a146_c4": {"within": ens["fit"]["within"], "nfev": ens["fit"]["nfev"], "nfev_centre": ens["fit"]["nfev_centre"],
                                    "cost": ens["fit"]["cost"], "cost_centre": ens["fit"]["cost_centre"], "pass": ens["c4"]},
            "c5_robust_pattern": {"seeds_with_pattern": int(sum(pattern(est[s]) for s in seeds)), "ensemble": pattern(ens),
                                  "pass": sum(pattern(est[s]) for s in seeds) >= 9 and pattern(ens)}}
    runs = {s: load_json(HERE / "runs" / f"{s}.json") for s in seeds}
    out = {"seeds": seeds, "criteria": crit, "passed": sum(c["pass"] for c in crit.values()), "of": len(crit),
           "spread": {"median_min": med.min(axis=0).tolist(), "median_max": med.max(axis=0).tolist(), "median_mean": med.mean(axis=0).tolist(),
                      "median_sd": med.std(axis=0, ddof=1).tolist(), "range_over_mean": ((med.max(axis=0) - med.min(axis=0)) / med.mean(axis=0)).tolist(),
                      "cover_min": cov.min(axis=0).tolist(), "cover_max": cov.max(axis=0).tolist()},
           "a146_criteria_pass_counts": {c: int(sum(est[s][c] for s in seeds)) for c in ("c1", "c2", "c3", "c4", "c5")},
           "a146_c4_within_per_seed": {s: est[s]["fit"]["within"] for s in seeds},
           "size_curve": curve, "ensemble": ens, "numpy_control": num, "per_seed": est,
           "epochs": {s: runs[s]["epochs"] for s in seeds}, "train_s": {s: runs[s]["train_s"] for s in seeds},
           "commits": sorted({r["provenance"]["commit"] for r in runs.values()}),
           "any_modified": any(r["provenance"]["extension_modified"] for r in runs.values())}
    (HERE / "a201_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    f = lambda xs, n=4: " / ".join(f"{x:.{n}f}" for x in xs)
    ok = lambda c: "PASS" if crit[c]["pass"] else "FAIL"
    print(f"A201: {out['passed']} of {out['of']} criteria pass; {len(seeds)} seeds; commits {out['commits']}{' (MODIFIED files)' if out['any_modified'] else ''}")
    print(f"C1 {ok('c1_control')} control max rel {ctrl:.1e}")
    print(f"seeds, median |err| L / Q / didt / k: min {f(med.min(axis=0))}, max {f(med.max(axis=0))}, mean {f(med.mean(axis=0))}")
    print(f"  range / mean {f(out['spread']['range_over_mean'], 2)}; covers {cov.min():.3f}-{cov.max():.3f}")
    print(f"C2 {ok('c2_a146_c1_c3_all_seeds')} A146 criteria 1-3 on seeds: {crit['c2_a146_c1_c3_all_seeds']['counts']}")
    print(f"A146 criterion 4 passes on {out['a146_criteria_pass_counts']['c4']} of {len(seeds)} seeds; min within per parameter "
          f"{f(np.min([est[s]['fit']['within'] for s in seeds], axis=0), 3)}, max {f(np.max([est[s]['fit']['within'] for s in seeds], axis=0), 3)}")
    print(f"ensemble: median {f(ens['median_err'])}, cover {f(ens['cover90'], 3)}")
    print(f"C3 {ok('c3_ensemble_error')} ensemble / seed mean {f(ratio, 2)}")
    print(f"C4 {ok('c4_ensemble_a146_c4')} ensemble within {f(ens['fit']['within'], 3)}, evals {ens['fit']['nfev']:.1f} vs centre {ens['fit']['nfev_centre']:.1f}, "
          f"cost {ens['fit']['cost']:.4f} vs {ens['fit']['cost_centre']:.4f}")
    print(f"C5 {ok('c5_robust_pattern')} A146's robustness pattern on {crit['c5_robust_pattern']['seeds_with_pattern']} of {len(seeds)} seeds, ensemble {crit['c5_robust_pattern']['ensemble']}")
    print("size curve (networks: L / Q / didt / k): " + "; ".join(f"{k}: {f(v)}" for k, v in curve.items()))


if __name__ == "__main__":
    main()
