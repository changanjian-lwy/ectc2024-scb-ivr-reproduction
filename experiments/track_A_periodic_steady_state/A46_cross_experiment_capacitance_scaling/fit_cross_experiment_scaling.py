"""Rebuild and fit the cross-experiment (A41/A42/A45) capacitance-scaling
regression as a committed, rerunnable script -- see BOUNDARY.md for why this
exists as its own experiment rather than only living in chat output."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

TRACK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def load_combined() -> pd.DataFrame:
    frames = []
    for rel, ch, cl, source in [
        ("A42_zero_snubber_negative_current_threshold/coarse_results.csv", 385.0, 770.0, "A42"),
        ("A42_zero_snubber_negative_current_threshold/refinement_results.csv", 385.0, 770.0, "A42"),
        ("A45_epc2067_table3_candidate_commutation/coarse_results.csv", 3720.0, 5580.0, "A45"),
        ("A45_epc2067_table3_candidate_commutation/wide_bracket_results.csv", 3720.0, 5580.0, "A45"),
        ("A45_epc2067_table3_candidate_commutation/refinement_results.csv", 3720.0, 5580.0, "A45"),
    ]:
        df = pd.read_csv(TRACK / rel)
        df["CH_pF"] = ch
        df["CL_pF"] = cl
        df["source"] = source
        frames.append(df[["negative_target_a", "minimum_vds_high_after_release_v", "CH_pF", "CL_pF", "source"]])

    a41 = pd.read_csv(TRACK / "A41_p24_snubber_local_sensitivity/results.csv")
    a41["negative_target_a"] = a41["negative_fraction_pct"] * 1.25
    a41["CH_pF"] = 385.0 + a41["added_snubber_pf"]
    a41["CL_pF"] = np.where(a41["branch"] == "symmetric", 770.0 + a41["added_snubber_pf"], 770.0)
    a41["source"] = "A41_" + a41["branch"]
    frames.append(a41[["negative_target_a", "minimum_vds_high_after_release_v", "CH_pF", "CL_pF", "source"]])

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined.dropna(subset=["negative_target_a", "minimum_vds_high_after_release_v", "CH_pF", "CL_pF"])


def model(x, v0, k, p):
    ineg, ceff = x
    return v0 - k * ineg / np.power(ceff, p)


def main() -> None:
    combined = load_combined()
    combined["Ceff_pF"] = combined["CH_pF"] * combined["CL_pF"] / (combined["CH_pF"] + combined["CL_pF"])
    combined.to_csv(OUT / "combined_dataset.csv", index=False)

    ineg = combined["negative_target_a"].to_numpy()
    ceff = combined["Ceff_pF"].to_numpy()
    vmin = combined["minimum_vds_high_after_release_v"].to_numpy()

    popt, pcov = curve_fit(model, (ineg, ceff), vmin, p0=[12.0, 1.0, 0.5], maxfev=20000)
    v0, k, p = popt
    perr = np.sqrt(np.diag(pcov))
    pred = model((ineg, ceff), *popt)
    ss_res = float(np.sum((vmin - pred) ** 2))
    ss_tot = float(np.sum((vmin - vmin.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot

    # Fixed p=0.5 comparison point (naive resonant-energy exponent).
    def model_fixed(x, v0, k):
        ineg, ceff = x
        return v0 - k * ineg / np.sqrt(ceff)

    popt_fixed, _ = curve_fit(model_fixed, (ineg, ceff), vmin, p0=[12.0, 1.0], maxfev=20000)
    pred_fixed = model_fixed((ineg, ceff), *popt_fixed)
    r2_fixed = 1 - np.sum((vmin - pred_fixed) ** 2) / ss_tot

    threshold_checks = []
    for label, ceff_val, actual_low, actual_high in [
        ("A42 (GS61008T, Ceff=256.7pF)", 385.0 * 770.0 / (385.0 + 770.0), 7.76, 7.77),
        ("A45 (EPC2067, Ceff=2232pF)", 3720.0 * 5580.0 / (3720.0 + 5580.0), 22.04, 22.05),
    ]:
        ineg_thr_a = v0 * ceff_val**p / k
        pct = ineg_thr_a / 1.25
        threshold_checks.append(
            {
                "label": label,
                "Ceff_pF": ceff_val,
                "predicted_threshold_pct": pct,
                "actual_bracket_low_pct": actual_low,
                "actual_bracket_high_pct": actual_high,
                "relative_error_pct": 100 * (pct - (actual_low + actual_high) / 2) / ((actual_low + actual_high) / 2),
            }
        )

    result = {
        "n_points": int(len(combined)),
        "sources": combined["source"].value_counts().to_dict(),
        "model": "Vds_min = V0 - k*Ineg/Ceff^p",
        "fit": {"V0": v0, "k": k, "p": p, "V0_stderr": perr[0], "k_stderr": perr[1], "p_stderr": perr[2], "R2": r2},
        "fixed_p_0p5_comparison": {"V0": popt_fixed[0], "k": popt_fixed[1], "R2": r2_fixed},
        "direction": {
            "at_fixed_Ineg": "Vds_min increases (moves away from ZVS) as Ceff grows: Vds_min ~ V0 - k*Ineg*Ceff^(-p)",
            "threshold_vs_Ceff": "Ineg_threshold increases as Ceff grows: Ineg_threshold = (V0/k) * Ceff^(+p), NOT Ceff^(-p)",
        },
        "threshold_consistency_checks": threshold_checks,
    }
    (OUT / "fit_results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
