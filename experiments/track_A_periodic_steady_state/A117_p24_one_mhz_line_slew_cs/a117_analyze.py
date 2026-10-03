"""A117 analysis against BOUNDARY Section 2: each step row's co-simulation outcome (runaway / slow / peak / ok),
step statistics (matrix.step_stats at 2000 us) and valleys after the step, against a117_predictions.json; the n0 rows
against A115 n10 / A116 c60_n0 (A115's row statistics). Writes a117_summary.json."""
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
spec = importlib.util.spec_from_file_location("a116_analyze", HERE.parent / "A116_p24_one_mhz_transients" / "a116_analyze.py")
A116 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A116)
T_STEP = 2000e-6
REFS = {"c3_tim_n0": HERE.parent / "A115_p24_one_mhz_design_point" / "cosim" / "run_n10.json",
        "c3_cmp_n0": HERE.parent / "A116_p24_one_mhz_transients" / "cosim" / "run_c60_n0.json"}


def load(p):
    return json.loads(Path(p).read_text())


def outcome(d, st):
    if sum(d["late_fires"]) > 100 or d["ipk_a"] > 400.0:
        return "runaway"
    if st["back_within_1pct_us"] > 60.0:
        return "slow"
    return "peak" if d["ipk_a"] > 200.0 else "ok"


def main():
    pred = load(HERE / "a117_predictions.json")
    res = {}
    for name, pr in pred.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        st = step_stats(d, t_step=T_STEP)
        o = outcome(d, st)
        m = pr["model"]
        c = {"no_overlap": d["overlaps"] == 0}
        if not pr["unreliable_timed_rising"]:
            c["outcome_as_d63"] = (o in ("slow", "runaway")) if pr["outcome"] == "slow_or_runaway" else (o == pr["outcome"])
            if pr["outcome"] in ("ok", "peak"):
                c["peak_10pct"] = abs(d["ipk_a"] / m["peak_max_a"] - 1) <= 0.10
        if name == "c3_cmp_s_m62":
            c["extreme_10pct"] = abs(st["extreme_mv"] / m["extreme_mv"] - 1) <= 0.10
            c["back_5us"] = abs(st["back_within_1pct_us"] - m["back_us"]) <= 5.0
        x = {"outcome": o, "d63_outcome": pr["outcome"], "flagged": pr["unreliable_timed_rising"], "step": st, "ipk_a": d["ipk_a"],
             "late_fires": d["late_fires"], "overlaps": d["overlaps"], "valleys_after_a": A116.valleys_after(d, T_STEP), "criteria": c}
        res[name] = x
        print(f"{name:20s}: {o:8s} (D63 {pr['outcome']}{', flagged' if pr['unreliable_timed_rising'] else ''}); peak {d['ipk_a']:5.0f} A (D63 "
              f"{m['peak_max_a']:.0f}), Vo {st['extreme_mv']:+8.2f} mV (D63 {m['extreme_mv']:+.1f}), back {st['back_within_1pct_us']:7.2f} us, late "
              f"{sum(d['late_fires'])}, valleys " + " ".join(f"[{a:+.0f},{b:+.0f}]" for a, b in x["valleys_after_a"]) + "; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    for name, ref in REFS.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        x, r = A115.row(load(p)), A115.row(load(ref))
        dv = [a - b for a, b in zip(x["hs_on_vds_v"], r["hs_on_vds_v"])]
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0, "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3,
             "hs_up_0p5_1p5V": all(0.5 <= v <= 1.5 for v in dv)}
        x["criteria"] = c; x["hs_shift_v"] = dv; x["ref_efficiency_pct"] = r["efficiency_pct"]
        res[name] = x
        print(f"{name}: HS on " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + " V (shift " + "/".join(f"{a:+.2f}" for a in dv)
              + f"), valleys " + "/".join(f"{a:+.2f}" for a in x["valleys_a"]) + ", sd " + "/".join(f"{a:.2f}" for a in x["off_sd_a"])
              + f", efficiency {x['efficiency_pct']:.2f}% (Cs 15 uF {r['efficiency_pct']:.2f}), ipk {x['ipk_a']:.0f} A, Vo {x['vo_mean_v']:.5f}; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a117_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a117_summary.json")


if __name__ == "__main__":
    main()
