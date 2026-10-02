"""A105 analysis: the integrated candidates I1 and I2 on the standard matrix, against the references
(reference_stats.json: A97's comparator runs, A100's ADM32 runs), D59's step predictions and BOUNDARY Section 4.

Rows without a step: matrix_stats.window_stats over the last 200 periods. Step rows: the same before the step, the
step's extreme and time, the last exit from 1 V +/- 1%, and the last 200 periods after it. I1's +-62.5 A rows are
also compared section by section with A104's fc100 runs (the same configuration). Writes a105_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from matrix_stats import window_stats  # noqa: E402

ROWS = ("n0", "m1n", "m1p", "m3n", "m3p", "j30", "j100")
STEPS = {"s_m25": -25.0, "s_p25": 25.0, "s_m62": -62.5, "s_p62": 62.5}
T_STEP = 400e-6


def load(name):
    p = HERE / "cosim" / f"run_{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def step_metrics(d):
    t = np.array([s["t_s"] for s in d["sections"]]); vo = np.array([s["vo"] for s in d["sections"]])
    a = t >= T_STEP
    ta, va = t[a], vo[a]
    i = int(np.argmax(np.abs(va - 1.0)))
    bad = np.nonzero(np.abs(va - 1.0) > 0.01)[0]
    return {"extreme_mv": float((va[i] - 1.0) * 1e3), "t_extreme_us": float((ta[i] - T_STEP) * 1e6),
            "back_within_1pct_us": float((ta[bad[-1]] - T_STEP) * 1e6) if len(bad) else 0.0}


def fmt(x):
    return (f"{x['status']}, ov {x['overlaps']}, ipk {x['ipk_a']:.0f} A, vds {x['vds_max_v']:.1f} V | Vo {x['vo_mean_v']:.4f} "
            f"(pp {x['vo_pp_mv']:.2f} mV), period sd {x['period_sd_ns']:.3f} ns | off sd "
            + "/".join(f"{p['i_off_sd_a']:.3f}" for p in x["phases"]) + " A (mean "
            + "/".join(f"{p['i_off_mean_a']:.2f}" for p in x["phases"]) + ") | LS max "
            + "/".join(f"{p['ls_on_vds_max_v']:+.2f}" for p in x["phases"]))


def main():
    ref = json.loads((HERE / "reference_stats.json").read_text())
    d59 = json.loads((HERE / "d59_step_predictions.json").read_text())["steps"]
    out = {"runs": {}, "checks": {}}
    for cand in ("i1", "i2"):
        for row in ROWS:
            d = load(f"{cand}_{row}")
            if d is None:
                continue
            x = window_stats(d)
            x["t_lo_timed_us"] = d["t_lo_timed_s"] * 1e6 if d.get("t_lo_timed_s") else None
            out["runs"][f"{cand}_{row}"] = x
            r = ref.get(row) if cand == "i1" else ref.get(f"adm_{row}")
            c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0}
            if r is not None:
                tol = 0.3 if cand == "i2" else 0.25
                ph = range(1, 4) if cand == "i2" else range(4)
                c["off_sd"] = all(abs(x["phases"][k]["i_off_sd_a"] / r["phases"][k]["i_off_sd_a"] - 1) <= tol
                                  or x["phases"][k]["i_off_sd_a"] - r["phases"][k]["i_off_sd_a"] <= 0.05 for k in ph)
                if cand == "i2":
                    c["phase1_sd"] = abs(x["phases"][0]["i_off_sd_a"] / r["phases"][0]["i_off_sd_a"] - 1) <= 0.5
                if cand == "i1":
                    c["period_sd"] = abs(x["period_sd_ns"] / r["period_sd_ns"] - 1) <= 0.3
                    lim = 1.0 if row.startswith("j") else 0.3
                    c["low_side"] = max(p["ls_on_vds_max_v"] for p in x["phases"]) <= max(p["ls_on_vds_max_v"] for p in r["phases"]) + lim
            if cand == "i2" and row == "n0":
                c["t6_phase1_sd_le_0p6"] = x["phases"][0]["i_off_sd_a"] <= 0.6
            out["checks"][f"{cand}_{row}"] = c
            print(f"{cand}_{row:5s}: {fmt(x)}" + (f" | timed from {x['t_lo_timed_us']:.1f} us" if x["t_lo_timed_us"] else ""))
            if r is not None:
                print(f"   ref {row if cand == 'i1' else 'adm_' + row:9s}: off sd " + "/".join(f"{p['i_off_sd_a']:.3f}" for p in r["phases"])
                      + f", period sd {r['period_sd_ns']:.3f} ns, LS max " + "/".join(f"{p['ls_on_vds_max_v']:+.2f}" for p in r["phases"]))
            print("   checks: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
        for row, i_step in STEPS.items():
            d = load(f"{cand}_{row}")
            if d is None:
                continue
            pre, post, st = window_stats(d, t1=T_STEP), window_stats(d), step_metrics(d)
            out["runs"][f"{cand}_{row}"] = {"pre": pre, "post": post, "step": st}
            p = d59[row[2:]]
            c = {"no_overlap": d["overlaps"] == 0, "peak_200a": pre["ipk_a"] <= 200.0,
                 "d59_extreme": abs(st["extreme_mv"] / p["extreme_mv"] - 1) <= 0.3,
                 "low_side_after": max(q["ls_on_vds_max_v"] for q in post["phases"]) <= 0.0}
            if cand == "i1" and row in ("s_m62", "s_p62"):
                a104 = json.loads((HERE.parent / "A104_p24_voltage_loop_pi" / "cosim" / f"run_fc100_{row[2:]}.json").read_text())
                c["identical_to_a104"] = a104["sections"] == d["sections"]
            out["checks"][f"{cand}_{row}"] = c
            print(f"{cand}_{row:5s}: step {st['extreme_mv']:+.1f} mV at {st['t_extreme_us']:.1f} us (D59 {p['extreme_mv']:+.1f}), back within 1% "
                  f"{st['back_within_1pct_us']:.1f} us | after: {fmt(post)}")
            print("   checks: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a105_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a105_summary.json")


if __name__ == "__main__":
    main()
