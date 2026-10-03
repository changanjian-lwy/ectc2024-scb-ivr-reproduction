"""A119 analysis against BOUNDARY Section 2: driver rows over the last 200 periods (A115's row statistics) against
A118 f6_n0; step rows by step_stats at 2000 us, the peak after the step and phase 1's turn-off currents; l_m80_10us's
last 200 periods. Writes a119_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_analyze", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
T_STEP = 2000e-6
N0 = HERE.parent / "A118_p24_floor_turn_off" / "cosim" / "run_f6_n0.json"


def load(p):
    return json.loads(Path(p).read_text())


def main():
    pred = load(HERE / "a119_predictions.json")
    ref = A115.row(load(N0))
    res = {}
    for name in ("m1n", "m1p", "m3n", "m3p", "j30", "j100"):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p); x = A115.row(d)
        sd_lim = {"j30": 0.16, "j100": 0.6}.get(name, 0.1)
        c = {"no_overlap": x["overlaps"] == 0, "startup_200a": d["ipk_a"] <= 200.0,
             "hs_0p1V": all(abs(a - b) <= 0.1 for a, b in zip(x["hs_on_vds_v"], ref["hs_on_vds_v"])),
             f"sd_{sd_lim}A": max(x["off_sd_a"]) <= sd_lim}
        x["criteria"] = c; res[name] = x
        print(f"{name:5s}: HS on " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + " V (n0 " + "/".join(f"{a:+.2f}" for a in ref["hs_on_vds_v"])
              + "), sd " + "/".join(f"{a:.2f}" for a in x["off_sd_a"]) + f", ipk {d['ipk_a']:.0f} A, late {sum(d['late_fires'])}, efficiency "
              f"{x['efficiency_pct']:.2f}%; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    for name, m in pred.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        st = step_stats(d, t_step=T_STEP)
        pk = max(x["i_a"] for x in d["highoffs_last"] if x["t_s"] >= T_STEP)
        ph1 = [x["i_a"] for x in d["lowoffs_last"] if x["phase"] == 1 and x["t_s"] >= T_STEP]
        late = sum(d["late_fires"])
        c = {"no_overlap": d["overlaps"] == 0, "peak_200a": pk <= 200.0, "no_runaway": late <= 100 and pk <= 400.0}
        x = {"peak_after_a": pk, "step": st, "ph1_min_a": min(ph1), "ph1_max_a": max(ph1), "late": late, "d63": m}
        if name == "l_m80_10us":
            w = window_stats(d)
            x["last200_vo_pp_mv"] = w["vo_pp_mv"]; x["last200_hs_on_v"] = [q["hs_on_vds_v"] for q in w["phases"]]
        else:
            c["back_100us"] = st["back_within_1pct_us"] <= 100.0
            if name != "l_p48_10us":
                c["peak_10pct_d63"] = abs(pk / m["peak_max_a"] - 1) <= 0.10
        x["criteria"] = c; res[name] = x
        print(f"{name:11s}: peak after {pk:5.0f} A (D63 {m['peak_max_a']:.0f}), Vo {st['extreme_mv']:+8.2f} mV (D63 {m['extreme_mv']:+.1f}), back "
              f"{st['back_within_1pct_us']:7.2f} us (D63 {m['back_us']:.1f}), phase 1 [{min(ph1):+.1f}, {max(ph1):+.1f}] A, late {late}"
              + (f", last 200 periods Vo pp {x['last200_vo_pp_mv']:.2f} mV" if name == "l_m80_10us" else "") + "; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a119_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a119_summary.json")


if __name__ == "__main__":
    main()
