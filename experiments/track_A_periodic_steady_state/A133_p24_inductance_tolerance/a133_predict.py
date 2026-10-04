"""A133 predictions (registered, not criteria): D63 step-row peaks with the fixed 15.625 A target at each corner -
k_L 0.7 / 1.0 / 1.3 (C nominal) and C 0.7 / L 1.3 from A132's a132_d63.json, k_L 1.2 computed here with A132's
d63_case - each with A125's 80 % band (x 0.875-1.125). D63 starts from the balanced steady state and has no phase
floors, so it stands for the floored design if the floors do not fire. Writes a133_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
A132 = PROJECT / "experiments/track_A_periodic_steady_state/A132_p24_neg_current_autotune"
spec = importlib.util.spec_from_file_location("a132_predict", A132 / "a132_predict.py")
PR = importlib.util.module_from_spec(spec); spec.loader.exec_module(PR)
CORNERS = {"nom": (1.0, 1.0), "l07": (1.0, 0.7), "l12": (1.0, 1.2), "l13": (1.0, 1.3), "c07l13": (0.7, 1.3)}
BAND = (0.875, 1.125)


def main():
    old = json.loads((A132 / "a132_d63.json").read_text())["runs"]
    out = {}
    for corner, (k_c, k_l) in CORNERS.items():
        if k_l == 1.2:
            rs = [PR.d63_case((k_c, k_l, "fixed", PR.I_TGT, row)) for row in PR.FF.A124_ROWS]
        else:
            rs = [r for r in old if r["k_c"] == k_c and r["k_l"] == k_l and r["target"] == "fixed"]
        out[corner] = {r["row"].split("_", 1)[1]: {"peak_a": r["peak_a"], "band_a": [r["peak_a"] * BAND[0], r["peak_a"] * BAND[1]],
                                                   "outcome": r["outcome"], "slot_depth_a": r["slot_depth_a"],
                                                   "extreme_mv": r["extreme_mv"]} for r in rs}
    (HERE / "a133_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for corner, rows in out.items():
        print(corner, " ".join(f"{k} {v['peak_a']:.0f}{'' if v['outcome'] == 'ok' else '!'}" for k, v in rows.items()))


if __name__ == "__main__":
    main()
