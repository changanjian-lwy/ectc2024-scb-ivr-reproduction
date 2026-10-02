"""A107 analysis: A105's I2 at Cs 0.6 and 8.7 uF on six standard-matrix rows, with the shared statistics
(scb_ivr.cosim.matrix), against D60/D59 (d60_predictions.json), the 3 uF references (A105's i2, A106's pi100) and
BOUNDARY Section 4. Added here: the ladder deviation's largest rebound after its peak (a resonance would show one).
Writes a107_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

TA = HERE.parent
ROWS = ("n0", "j30", "s_m62", "s_p62", "l_m48_1us", "l_p48_1us")
REF = {"n0": ("A105_p24_integrated_standard_matrix", "i2_n0"), "j30": ("A105_p24_integrated_standard_matrix", "i2_j30"),
       "s_m62": ("A105_p24_integrated_standard_matrix", "i2_s_m62"), "s_p62": ("A105_p24_integrated_standard_matrix", "i2_s_p62"),
       "l_m48_1us": ("A106_p24_line_steps", "pi100_m48_1us"), "l_p48_1us": ("A106_p24_line_steps", "pi100_p48_1us")}


def load(folder, name):
    return json.loads((folder / "cosim" / f"run_{name}.json").read_text())


def rebound(d, t_step=400e-6):
    secs = [s for s in d["sections"] if s["t_s"] >= t_step]
    dev = np.array([np.max(np.abs(np.array(s["vcs_v"]) / s["vin_v"] - np.array([0.75, 0.5, 0.25]))) for s in secs])
    i = int(np.argmax(dev))
    run_min = np.minimum.accumulate(dev[i:])
    return float(np.max(dev[i:] - run_min))


def row_summary(d, row):
    x = {"status": d["status"], "overlaps": d["overlaps"], "ipk_a": float(d["ipk_a"]), "vds_max_v": float(max(d["vds_max_v"]))}
    if row in ("n0", "j30"):
        x["window"] = window_stats(d)
    else:
        x["pre"], x["post"], x["step"] = window_stats(d, t1=400e-6), window_stats(d), step_stats(d)
        if row.startswith("l_"):
            x["rebound"] = rebound(d)
    return x


def main():
    pred = json.loads((HERE / "d60_predictions.json").read_text())
    out = {}
    for row in ROWS:
        r = row_summary(load(TA / REF[row][0], REF[row][1]), row)
        out[f"ref3uF_{row}"] = r
    for tag in ("cs0p6", "cs8p7"):
        for row in ROWS:
            d = load(HERE, f"{tag}_{row}")
            x = row_summary(d, row)
            ref = out[f"ref3uF_{row}"]
            c = {"no_overlap": x["overlaps"] == 0}
            if row == "l_p48_1us":
                c["peak_direction"] = (x["ipk_a"] < ref["ipk_a"]) if tag == "cs0p6" else (x["ipk_a"] > ref["ipk_a"])
            else:
                c["peak_200a"] = x["ipk_a"] <= 200.0
            if row in ("n0", "j30"):
                c["stable"] = x["window"]["vo_pp_mv"] <= 5.0
                if row == "n0":
                    c["low_side_zvs"] = max(p["ls_on_vds_max_v"] for p in x["window"]["phases"]) <= 0.0
            if row.startswith("s_"):
                c["cs_independent"] = abs(x["step"]["extreme_mv"] / ref["step"]["extreme_mv"] - 1) <= 0.2
            if row.startswith("l_"):
                p = pred[tag][row]
                c["no_ringing"] = x["rebound"] <= 0.005
                c["settle_vs_d60"] = 0.3 * p["ladder_back_below_1pct_us"] <= x["step"]["ladder_back_below_1pct_us"] <= 1.2 * p["ladder_back_below_1pct_us"]
                c["peak_vs_d60"] = abs(x["step"]["ladder_dev_peak"] / p["ladder_dev_peak"] - 1) <= 0.3
            x["criteria"] = c
            out[f"{tag}_{row}"] = x
            w = x.get("window") or x["post"]
            line = (f"{tag}_{row:10s}: {x['status']}, ov {x['overlaps']}, ipk {x['ipk_a']:.0f} A (3 uF {ref['ipk_a']:.0f}), vds {x['vds_max_v']:.1f} V | "
                    f"Vo pp {w['vo_pp_mv']:.2f} mV, off sd " + "/".join(f"{q['i_off_sd_a']:.3f}" for q in w["phases"])
                    + " (3 uF " + "/".join(f"{q['i_off_sd_a']:.3f}" for q in (ref.get('window') or ref['post'])["phases"]) + ")"
                    + ", HS V_DS " + "/".join(f"{q['hs_on_vds_v']:.2f}" for q in w["phases"]) + ", LS max " + "/".join(f"{q['ls_on_vds_max_v']:+.2f}" for q in w["phases"]))
            print(line)
            if "step" in x:
                s, rs = x["step"], ref["step"]
                extra = (f"; ladder peak {100 * s['ladder_dev_peak']:.2f}% (D60 {100 * pred[tag][row]['ladder_dev_peak']:.2f}, 3 uF {100 * rs['ladder_dev_peak']:.2f}), "
                         f"back below 1% {s['ladder_back_below_1pct_us']:.1f} us (D60 {pred[tag][row]['ladder_back_below_1pct_us']:.1f}, 3 uF {rs['ladder_back_below_1pct_us']:.1f}), "
                         f"rebound {100 * x['rebound']:.2f} pp") if row.startswith("l_") else ""
                print(f"   step: Vo {s['extreme_mv']:+.1f} mV at {s['t_extreme_us']:.1f} us (3 uF {rs['extreme_mv']:+.1f}), back within 1% {s['back_within_1pct_us']:.1f} us" + extra)
            print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a107_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a107_summary.json")


if __name__ == "__main__":
    main()
