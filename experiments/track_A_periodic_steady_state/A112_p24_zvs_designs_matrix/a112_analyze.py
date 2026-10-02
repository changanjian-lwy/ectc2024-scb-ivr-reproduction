"""A112 analysis against BOUNDARY Section 1: per design (20%, 25%) and matrix row - overlaps, the run's peak and the
peak after 150 us (recorded high-side turn-off currents), the high side's turn-on V_DS and the low side's maximum
(last 200 periods before any step), the turn-off spread, the step's extreme and recovery - against the design's n0 and
the 5% design's row (A105 i2_<row>, A106 pi100_<row>). n0 rows are checked against A110's runs record by record.
Writes a112_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import ROWS, step_stats, window_stats  # noqa: E402

TA = HERE.parent
A110 = TA / "A110_p24_high_side_zvs" / "cosim"
PEAK5 = {"l_p48_1us": 203.0, "l_m48_1us": 190.0, "l_p48_10us": 166.0, "l_m48_10us": 138.0}
DPEAK = {20: 17.0, 25: 24.0}
SKIP = {"wall_s", "provenance"}


def load(p):
    return json.loads(Path(p).read_text())


def ref5(row):
    if row.startswith("l_"):
        return TA / "A106_p24_line_steps" / "cosim" / f"run_pi100_{row[2:]}.json"
    return TA / "A105_p24_integrated_standard_matrix" / "cosim" / f"run_i2_{row}.json"


def summarise(d, stepped):
    t1 = 400e-6 if stepped else None
    w = window_stats(d, t1=t1)
    after = [h["i_a"] for h in d["highoffs_last"] if h["t_s"] >= 150e-6]
    x = {"overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "peak_after_150us_a": max(after),
         "hs_on_vds_v": [p["hs_on_vds_v"] for p in w["phases"]], "ls_on_vds_max_v": [p["ls_on_vds_max_v"] for p in w["phases"]],
         "off_sd_a": [p["i_off_sd_a"] for p in w["phases"]], "late_fires": d["late_fires"]}
    if stepped:
        x["step"] = step_stats(d)
    return x


def main():
    res = {}
    for pct in (20, 25):
        n0 = None
        for row in ROWS:
            p = HERE / "cosim" / f"run_p{pct}_{row}.json"
            if not p.exists():
                continue
            d = load(p)
            stepped = row.startswith(("s_", "l_"))
            x = summarise(d, stepped)
            r5 = ref5(row)
            x5 = summarise(load(r5), stepped)
            if row == "n0":
                n0 = x
                a = load(A110 / f"run_n{pct}.json")
                strip = lambda r: {k: ({q: u for q, u in v.items() if q not in ("note", "out")} if k == "cfg" else v)
                                   for k, v in r.items() if k not in SKIP}          # the note and output name differ by design
                sd, sa = strip(d), strip(a)
                diff = [k for k in set(sd) | set(sa) if json.dumps(sd.get(k)) != json.dumps(sa.get(k))]
                x["identical_to_a110"] = not diff
            c = {"no_overlap": x["overlaps"] == 0}
            if pct == 20:
                c["run_peak_200a"] = x["ipk_a"] <= 200.0
            if row in PEAK5:
                c["line_peak_pred"] = abs(x["peak_after_150us_a"] - (PEAK5[row] + DPEAK[pct])) <= 10.0
            else:
                c["peak_after_150us_200a"] = x["peak_after_150us_a"] <= 200.0
            if row == "n0":
                c["identical_to_a110"] = x["identical_to_a110"]
            if row[0] in "mj" and n0 is not None:
                c["hs_level_0p5V"] = all(abs(a - b) <= 0.5 for a, b in zip(x["hs_on_vds_v"], n0["hs_on_vds_v"]))
            if row[0] == "m":
                c["ls_zvs"] = max(x["ls_on_vds_max_v"]) <= 0.0
            if row[0] == "j":
                c["sd_band"] = all(abs(a / b - 1) <= 0.5 for a, b in zip(x["off_sd_a"], x5["off_sd_a"]))
            if stepped:
                s, s5 = x["step"], x5["step"]
                c["recovered"] = s["back_within_1pct_us"] != float("inf")
                c["step_30pct"] = abs(s["extreme_mv"] / s5["extreme_mv"] - 1) <= 0.3
                x["step_5pct"] = s5
            x["criteria"] = c; x["ref_5pct"] = {k: x5[k] for k in ("ipk_a", "peak_after_150us_a", "hs_on_vds_v", "off_sd_a")}
            res[f"p{pct}_{row}"] = x
            line = (f"p{pct}_{row:11s} ovl {x['overlaps']} ipk {x['ipk_a']:5.1f} after150 {x['peak_after_150us_a']:5.1f} A (5%: {x5['peak_after_150us_a']:5.1f}) "
                    f"HS " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_v"]) + f" LSmax {max(x['ls_on_vds_max_v']):+.2f} sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"]))
            if stepped:
                line += f" | step {x['step']['extreme_mv']:+.2f} mV back {x['step']['back_within_1pct_us']:.2f} us (5%: {x5['step']['extreme_mv']:+.2f})"
            miss = [k for k, v in c.items() if not v]
            print(line + (" | MISS " + ",".join(miss) if miss else " | ok"))
    (HERE / "a112_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a112_summary.json")


if __name__ == "__main__":
    main()
