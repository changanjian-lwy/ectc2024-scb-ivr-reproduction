"""A199 analysis: a199_checks.json and runs/*.json against the criteria of BOUNDARY.md. Writes a199_summary.json;
prints <= 15 lines.

    python3 .../a199_analyze.py        (numpy only)"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A146 = HERE.parents[3] / "extensions" / "ml_design_assist" / "experiments" / "A146_cnn_loop_identification"
EXACT, STEP, BAND, COVER = 1e-9, 1e-6, 1.25, (0.875, 0.925)
C4_TAGS, C5_TAG = ("s0_f64_cpu", "s1_f64_cpu", "s2_f64_cpu"), "s0_f32_mps"


def main():
    ck = json.loads((HERE / "a199_checks.json").read_text())
    ref = json.loads((A146 / "a146_summary.json").read_text())
    runs = {p.stem: json.loads(p.read_text()) for p in sorted((HERE / "runs").glob("*.json"))}
    r0 = np.array(ref["cnn"]["median_err"])
    c0 = max(ck["c0"][k] for k in ("q90", "q90_summary", "median_err", "p90_err", "cover90", "scaler"))
    c2 = max(max(r["grad_rel"]) for r in ck["c2"].values())
    c3p, c3l = max(s["param_max_abs"] for s in ck["c3"]), max(s["loss_rel"] for s in ck["c3"])
    med = np.array([runs[t]["median_err"] for t in C4_TAGS])
    cov = np.array([runs[t]["cover90"] for t in C4_TAGS])
    in_band = lambda c: bool(np.all((np.asarray(c) >= COVER[0]) & (np.asarray(c) <= COVER[1])))
    r5 = runs[C5_TAG]
    crit = {"c0": {"max_rel": c0, "pass": c0 <= EXACT},
            "c1": {"max_abs": ck["c1"]["max_abs"], "pass": ck["c1"]["max_abs"] <= EXACT},
            "c2": {"max_rel": c2, "pass": c2 <= EXACT},
            "c3": {"param_max_abs": c3p, "loss_rel": c3l, "clipped_steps": [s["clipped_steps"] for s in ck["c3"]],
                   "pass": c3p <= STEP and c3l <= STEP},
            "c4": {"ratio_per_seed": (med / r0).tolist(), "ratio_mean": (med.mean(axis=0) / r0).tolist(), "cover": cov.tolist(),
                   "pass": bool(np.all(med <= BAND * r0) and np.all(med.mean(axis=0) >= r0 / BAND)) and in_band(cov)},
            "c5": {"ratio": (np.array(r5["median_err"]) / r0).tolist(), "cover": r5["cover90"],
                   "pass": bool(np.all(np.array(r5["median_err"]) <= BAND * r0)) and in_band(r5["cover90"])}}
    out = {"reference": {"median_err": ref["cnn"]["median_err"], "cover90": ref["cnn"]["cover90"], "epochs": ref["epochs"],
                         "train_s": ref["train_s"], "ms_per_waveform": ref["ms_per_waveform"]},
           "criteria": crit, "passed": sum(c["pass"] for c in crit.values()), "of": len(crit),
           "runs": {t: {k: r[k] for k in ("epochs", "best_epoch", "best_val", "train_s", "s_per_epoch", "ms_per_waveform",
                                          "median_err", "p90_err", "cover90", "reload_max_abs")} for t, r in runs.items()},
           "commits": sorted({ck["provenance"]["commit"]} | {r["provenance"]["commit"] for r in runs.values()}),
           "any_modified": ck["provenance"]["extension_modified"] or any(r["provenance"]["extension_modified"] for r in runs.values()),
           "ms_per_step": {k: ck["c3"][0][k] for k in ("ms_per_step_numpy", "ms_per_step_torch")}}
    (HERE / "a199_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    f = lambda xs, n=4: " / ".join(f"{x:.{n}f}" for x in xs)
    ok = lambda c: "PASS" if crit[c]["pass"] else "FAIL"
    print(f"A199: {out['passed']} of {out['of']} criteria pass; commits {out['commits']}{' (MODIFIED files)' if out['any_modified'] else ''}")
    print(f"C0 {ok('c0')} stored numbers max rel {c0:.1e} | C1 {ok('c1')} forward max abs {ck['c1']['max_abs']:.1e} | "
          f"C2 {ok('c2')} gradients max rel {c2:.1e}")
    print(f"C3 {ok('c3')} 20 Adam steps: param max abs {c3p:.1e}, loss rel {c3l:.1e}, clipped steps {crit['c3']['clipped_steps']}")
    print(f"reference numpy (L / Q / didt / k): median {f(r0)}, cover {f(ref['cnn']['cover90'], 3)}, {ref['epochs']} epochs, {ref['train_s']:.0f} s")
    for t in (*C4_TAGS, C5_TAG):
        r = runs[t]
        print(f"  {t}: median {f(r['median_err'])}, cover {f(r['cover90'], 3)}, {r['epochs']} epochs, {r['train_s']:.0f} s")
    print(f"C4 {ok('c4')} ratio to numpy, mean of 3 seeds {f(crit['c4']['ratio_mean'], 2)}; worst seed {f(np.max(med / r0, axis=0), 2)}")
    print(f"C5 {ok('c5')} ratio to numpy {f(crit['c5']['ratio'], 2)}")
    print(f"step numpy {out['ms_per_step']['ms_per_step_numpy']:.0f} ms, torch float64 cpu {out['ms_per_step']['ms_per_step_torch']:.0f} ms")


if __name__ == "__main__":
    main()
