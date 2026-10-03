"""A123 analysis against BOUNDARY: per variant, n0 (start-up peak, efficiency against A118 f6_n0) and the three steps
(peak after the step from the high-side turn-off records, step_stats, late fires); a variant closes the candidate if
all three peaks are <= 200 A. Writes a123_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_analyze", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
T_STEP = 2000e-6
REF = {"l_p48_1us": 206, "l_m48_1us": 201, "l_m80_10us": 205}


def load(p):
    return json.loads(Path(p).read_text())


def main():
    pred = load(HERE / "a123_predictions.json")
    f6 = A115.row(load(HERE.parent / "A118_p24_floor_turn_off" / "cosim" / "run_f6_n0.json"))
    res = {}
    for v in ("c45", "f3", "k66"):
        x = {"steps": {}}
        d = load(HERE / "cosim" / f"run_{v}_n0.json")
        r = A115.row(d)
        x["n0"] = {"startup_ipk_a": d["ipk_a"], "efficiency_pct": r["efficiency_pct"], "hs_on_vds_v": r["hs_on_vds_v"], "off_sd_a": r["off_sd_a"]}
        c = {"no_overlap_n0": d["overlaps"] == 0, "startup_200a": d["ipk_a"] <= 200.0,
             "efficiency_0p1": abs(r["efficiency_pct"] - f6["efficiency_pct"]) <= 0.1}
        peaks = []
        for row in ("l_p48_1us", "l_m48_1us", "l_m80_10us"):
            d = load(HERE / "cosim" / f"run_{v}_{row}.json")
            st = step_stats(d, t_step=T_STEP)
            pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
            late = sum(d["late_fires"])
            x["steps"][row] = {"peak_after_a": pk, "extreme_mv": st["extreme_mv"], "back_us": st["back_within_1pct_us"], "late": late,
                               "d63_peak_a": pred[v][row]["peak_max_a"], "f6_peak_a": REF[row]}
            c[f"no_overlap_{row}"] = d["overlaps"] == 0
            c[f"no_runaway_{row}"] = late <= 100 and pk <= 400.0
            peaks.append(pk)
        res[f"{v}_n0"] = {**x["n0"], "criteria": {k: c[k] for k in ("no_overlap_n0", "startup_200a", "efficiency_0p1")}}
        for row, st in x["steps"].items():
            res[f"{v}_{row}"] = {**st, "criteria": {k: c[f"{k}_{row}"] for k in ("no_overlap", "no_runaway")}}
        c["closes_all_le_200a"] = all(pk <= 200.0 for pk in peaks)
        res[f"{v}_closes"] = {"peaks_a": peaks, "criteria": {"closes_all_le_200a": c["closes_all_le_200a"]}}
        x["criteria"] = c
        print(f"{v}: start-up {x['n0']['startup_ipk_a']:.0f} A, efficiency {x['n0']['efficiency_pct']:.2f}% (f6 {f6['efficiency_pct']:.2f}); "
              + "; ".join(f"{row} {s['peak_after_a']:.0f} A (f6 {s['f6_peak_a']}, D63 {s['d63_peak_a']:.0f}), {s['extreme_mv']:+.1f} mV, back {s['back_us']:.1f} us, late {s['late']}"
                          for row, s in x["steps"].items()))
        print("   " + ", ".join(f"{k} {'ok' if b else 'MISS'}" for k, b in c.items()))
    (HERE / "a123_summary.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
