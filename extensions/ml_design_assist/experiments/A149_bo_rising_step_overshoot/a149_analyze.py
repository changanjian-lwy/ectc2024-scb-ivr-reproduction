"""A149 post hoc cosim analysis (BOUNDARY addendum): the rail term alone, gr 1.0 / 0.75, against criterion 3's conditions
(50 pH loop + edge whole-run max V_DS <= 40 V; peak <= 200 A on l_p48_1us at L x 0.7 / 1 / 1.3 and l_p48_5us; Vo back
within 1 % <= 27.6 us on l_p48_1us; late fires <= the option-off record per row; committed code), with A148's per-run
stats. Cross-checks: D63's grid prediction at the same points, and the SH block applied to the loop-free records' own
rails and turn-on V_DS (no D63). Writes a149_summary.json; prints <= 15 lines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A148_rl_zvs_line_step"))
import a148_analyze as A  # noqa: E402

COS = HERE / "cosim"
TA = HERE.parents[3] / "experiments" / "track_A_periodic_steady_state"
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
A145C = TA / "A145_p24_finite_switching_edges" / "cosim"
ARMS = {"r100": (1.0, 0, 0, 0), "r075": (0.75, 0, 0, 0)}
ROWS = {"l_p48_1us": "l_p48_1us@1.0", "l_p48_5us": "l_p48_5us@1.0", "s070_l_p48_1us": "l_p48_1us@0.7",
        "s130_l_p48_1us": "l_p48_1us@1.3"}
V_LIM, PK_LIM, BACK_LIM = 40.0, 200.0, 27.6


def off_path(base):
    if base.startswith("e72_"):
        return A145C / f"run_{base}.json"
    for s in ("s070", "s130"):
        if base.startswith(s + "_"):
            return A143C / f"run_g4_{s}_{base[5:]}_k4.json"
    return A143C / f"run_g4_s100_{base}_k4.json"


def block_pred(r, tab, t0):
    """Max over 0.4 us windows after t0 of rail_(k-1) + rail_k + f(phase k-1's largest turn-on V_DS in the window)."""
    sec = r["sections"]
    t = np.array([s["t_s"] for s in sec])
    vin = np.array([s["vin_v"] for s in sec])
    vcs = np.array([s["vcs_v"] for s in sec])
    rails = np.stack([vin - vcs[:, 0], vcs[:, 0] - vcs[:, 1], vcs[:, 1] - vcs[:, 2], vcs[:, 2]], 1)
    best = -np.inf
    for e in r["turnons_last"]:
        if e["t_s"] < t0 or e["phase"] == 4:
            continue
        i = int(np.searchsorted(t, e["t_s"] + 5e-9))
        if 1 <= i < len(t):
            k = e["phase"]                                   # upstream phase k -> SH(k+1)
            best = max(best, rails[i - 1, k - 1] + rails[i - 1, k] + np.interp(e["vds_v"], tab["grid"], tab["x"]))
    return float(best)


def main():
    tabs = json.loads((HERE / "a149_sh_table.json").read_text())
    grid = {tuple(p["th"]): p["rows"] for p in json.loads((HERE / "a149_grid.json").read_text())["points"]}
    out = {}
    for arm, th in ARMS.items():
        runs = {}
        for f in sorted(COS.glob(f"run_{arm}_*.json")):
            name = f.stem[4:]
            base = name.split("_", 1)[1]
            r = A.load(f)
            s = A.stats(r, name)
            ref = A.load(off_path(base))
            s["late_off"] = ref["late_fires"]
            s["late_ok"] = sum(r["late_fires"]) <= sum(ref["late_fires"])
            if base in ROWS:
                s["sh50_block"] = block_pred(r, tabs["L50_e72"], A.t_step(r))
                s["d63"] = {k: grid[th][ROWS[base]][k] for k in ("sh50", "sh100", "peak", "vo27_mv", "back_us")}
                s["d63"]["von1"] = grid[th][ROWS[base]]["von"][0]
            runs[base] = s
        if not runs:
            continue
        c = {"vds50": runs.get("e72_l50_l_p48_1us", {}).get("vds", {}).get("whole"),
             "peaks": {b: runs[b]["peak_post"] for b in ROWS if b in runs},
             "back_us": runs.get("l_p48_1us", {}).get("back_within_1pct_us"),
             "late_ok": all(s["late_ok"] for s in runs.values()),
             "committed": all(s["src_modified"] is False and s["status"] == "COMPLETED" for s in runs.values())}
        c["pass"] = bool(c["vds50"] is not None and c["vds50"] <= V_LIM and len(c["peaks"]) == 4
                         and max(c["peaks"].values()) <= PK_LIM and c["back_us"] is not None and c["back_us"] <= BACK_LIM
                         and c["late_ok"] and c["committed"])
        out[arm] = {"th": th, "criterion_3_conditions": c, "runs": runs}
    (HERE / "a149_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for arm, o in out.items():
        c, R = o["criterion_3_conditions"], o["runs"]
        v = {b: round(R[b]["vds"]["whole"], 1) for b in R if "vds" in R[b]}
        print(f"{arm} gr {o['th'][0]}: {'PASS' if c['pass'] else 'FAIL'}; V_DS whole {v}; back {c['back_us']} us; late ok {c['late_ok']}")
        print("  peaks", {b: round(p, 1) for b, p in c["peaks"].items()})
        for b in ROWS:
            if b in R:
                s = R[b]
                print(f"  {b:15s} von1 {s['von_max'][0]:.1f} (D63 {s['d63']['von1']:.1f}) SH50 block {s['sh50_block']:.1f} "
                      f"(D63 {s['d63']['sh50']:.1f}) pk {s['peak_post']:.1f} (D63 {s['d63']['peak']:.1f}) "
                      f"Vo {s['extreme_mv']:+.1f} mV back {s['back_within_1pct_us']:.1f} us")


if __name__ == "__main__":
    main()
