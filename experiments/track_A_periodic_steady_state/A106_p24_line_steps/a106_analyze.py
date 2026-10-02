"""A106 analysis: line steps on A105's I2 (PI 100 kHz, and the I-only loop), against D59 (d59_predictions.json) and
BOUNDARY Section 4. Per run: Vo's extreme after the step and its time, the last exit from 1 V +/- 1%; the ladder
deviation (A73's max |VCs_k / Vin - (4 - k) / 4| at the sections, against the instantaneous input): its peak after the
step and the time it is back below 1%; A105's window statistics before the step and over the last 200 periods.
Writes a106_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A105_p24_integrated_standard_matrix"))
from matrix_stats import window_stats  # noqa: E402

T_STEP = 400e-6
RUNS = ("pi100_m48_1us", "pi100_p48_1us", "pi100_m48_10us", "pi100_p48_10us", "pi100_m80_10us",
        "ionly_m48_1us", "ionly_p48_1us", "ionly_m48_10us", "ionly_p48_10us")


def main():
    pred = json.loads((HERE / "d59_predictions.json").read_text())
    out = {}
    for name in RUNS:
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        secs = d["sections"]
        t = np.array([s["t_s"] for s in secs]); vo = np.array([s["vo"] for s in secs])
        vin = np.array([s["vin_v"] for s in secs]); vcs = np.array([s["vcs_v"] for s in secs])
        a = t >= T_STEP
        ta, va = t[a], vo[a]
        i = int(np.argmax(np.abs(va - 1.0)))
        bad = np.nonzero(np.abs(va - 1.0) > 0.01)[0]
        dev = np.max(np.abs(vcs / vin[:, None] - np.array([0.75, 0.5, 0.25])), axis=1)
        da = dev[a]
        lad_bad = np.nonzero(da > 0.01)[0]
        pre, post = window_stats(d, t1=T_STEP), window_stats(d)
        x = {"status": d["status"], "overlaps": d["overlaps"], "ipk_a": float(d["ipk_a"]), "vds_max_v": float(max(d["vds_max_v"])),
             "extreme_mv": float((va[i] - 1.0) * 1e3), "t_extreme_us": float((ta[i] - T_STEP) * 1e6),
             "back_within_1pct_us": float((ta[bad[-1]] - T_STEP) * 1e6) if len(bad) else 0.0,
             "ladder_dev_peak": float(da.max()), "ladder_back_below_1pct_us": float((ta[lad_bad[-1]] - T_STEP) * 1e6) if len(lad_bad) else 0.0,
             "ladder_dev_before": float(dev[~a][-200:].max()), "vin_final_v": float(vin[-1]), "vcs_final_v": [float(v) for v in vcs[-1]],
             "pre": pre, "post": post}
        q = pred[name]
        sd = lambda w: max(ph["i_off_sd_a"] for ph in w["phases"][1:])
        crit = {"no_overlap": d["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0,
                "d59_extreme": abs(x["extreme_mv"] / q["extreme_mv"] - 1) <= 0.3,
                "low_side_after": max(ph["ls_on_vds_max_v"] for ph in post["phases"]) <= 0.0,
                "spread_after": sd(post) <= 1.5 * sd(pre),
                "ladder_settles": x["ladder_back_below_1pct_us"] <= 100.0}
        x["criteria"] = crit
        out[name] = x
        print(f"{name}: {d['status']}, ov {d['overlaps']}, ipk {x['ipk_a']:.0f} A, vds max {x['vds_max_v']:.1f} V | Vo {x['extreme_mv']:+.1f} mV at "
              f"{x['t_extreme_us']:.1f} us (D59 {q['extreme_mv']:+.1f} at {q['t_extreme_us']:.1f}), back within 1% {x['back_within_1pct_us']:.1f} us")
        print(f"   ladder: before {100 * x['ladder_dev_before']:.2f}%, peak after {100 * x['ladder_dev_peak']:.2f}%, back below 1% at "
              f"{x['ladder_back_below_1pct_us']:.1f} us; final Vin {x['vin_final_v']:.1f} V, VCs " + "/".join(f"{v:.2f}" for v in x["vcs_final_v"]))
        print(f"   after: Vo {post['vo_mean_v']:.4f}, turn-off mean " + "/".join(f"{ph['i_off_mean_a']:.2f}" for ph in post["phases"])
              + " sd " + "/".join(f"{ph['i_off_sd_a']:.3f}" for ph in post["phases"]) + " (before sd " + "/".join(f"{ph['i_off_sd_a']:.3f}" for ph in pre["phases"])
              + "), HS V_DS " + "/".join(f"{ph['hs_on_vds_v']:.2f}" for ph in post["phases"]) + ", LS max " + "/".join(f"{ph['ls_on_vds_max_v']:+.2f}" for ph in post["phases"]))
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in crit.items()))
    (HERE / "a106_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a106_summary.json")


if __name__ == "__main__":
    main()
