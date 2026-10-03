"""A130 registered predictions (before any run): a129_predict's gated D63 law on A130's five rows (Cs x 1, 600
periods), A125 M80 / G80 peak bands. Writes a130_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a129_predict", HERE.parent / "A129_cosim_vff_slope_gate" / "a129_predict.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
ROWS = {"l_m80_6us": ("line", -8.0, 6.0), "l_m80_7p5us": ("line", -8.0, 7.5), "l_p48_2us": ("line", 4.8, 2.0),
        "l_p48_3us": ("line", 4.8, 3.0), "l_p80_10us": ("line", 8.0, 10.0)}


def main():
    env = A.R.make_env("vin_ff")
    out = {"gth_codes": A.GTH}
    for name, dist in ROWS.items():
        row = {}
        for arm, law in (("gated", A.law_gated), ("none", A.F.law_none)):
            recs, _, div = A.R.run(env, ("law", law), dist, 1.0, 600)
            s = A.F.summarise(recs)
            row[arm] = {"peak_a": s["peak_a"], "extreme_mv": s["extreme_mv"], "diverged": div}
            if arm == "gated":
                row[arm].update(gmax_codes=env._rtl["gmax"], opened_period=env._rtl["opened"])
        group = "rising" if dist[1] > 0 else "other"
        p = row["gated"]["peak_a"]
        row["band_peak_M80"] = A.C.register_band(p, "peak", group, 0.2, "M")
        row["band_peak_G80"] = A.C.register_band(p, "peak", group, 0.2, "G")
        out[name] = row
        print(f"{name:12s}: gated {p:5.1f} A (none {row['none']['peak_a']:5.1f}), M80 {row['band_peak_M80'][0]:.0f}-"
              f"{row['band_peak_M80'][1]:.0f}, G80 {row['band_peak_G80'][0]:.0f}-{row['band_peak_G80'][1]:.0f}; "
              f"opened {row['gated']['opened_period']}")
    (HERE / "a130_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
