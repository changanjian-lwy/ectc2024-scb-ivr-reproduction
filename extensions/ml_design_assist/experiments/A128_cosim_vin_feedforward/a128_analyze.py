"""A128 analysis against BOUNDARY Section 2: each row against A124's (a124_summary.json) - the peak after the step
(high-side turn-off records), step_stats' Vo extreme and recovery, phase 1's lowest turn-off current, overlaps, late
fires; n0 by A115's row statistics (L 2.933 nH). Criterion 0's identity: tmp/identity/run_p125_l_p48_1us.json (A124's
configuration rerun with the A128 code) against A124's archived run, section by section. A125's prospective test:
the share of rows inside the registered M80 / G80 peak bands and the |Vo| band. Writes a128_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

A124 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A124_p24_two_point_five_mhz"
spec = importlib.util.spec_from_file_location("a115_analyze", A124.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
A115.L1 = 7.3333333e-9 / 2.5
T_STEP = 800e-6


def load(p):
    return json.loads(Path(p).read_text())


def identity():
    new = PROJECT / "tmp" / "identity" / "run_p125_l_p48_1us.json"
    if not new.exists():
        return None
    a, b = load(A124 / "cosim" / "run_p125_l_p48_1us.json")["sections"], load(new)["sections"]
    keys = ("t_s", "v", "i", "vo", "vin_v", "ton_lsb", "vcs_v")
    same = len(a) == len(b) and all(all(x[k] == y[k] for k in keys) for x, y in zip(a, b))
    return {"sections": len(a), "identical": same}


def main():
    pr, ref = load(HERE / "a128_predictions.json"), load(A124 / "a124_summary.json")
    res = {"identity": identity()}
    print("identity (vff off, A124 p125_l_p48_1us):", res["identity"])
    inb = {"M80": [], "G80": [], "mv": []}
    for name, p in pr.items():
        f = HERE / "cosim" / f"run_v{name[1:]}.json"
        if not f.exists():
            continue
        d = load(f)
        st = step_stats(d, t_step=T_STEP)
        pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
        ph1 = min(q["i_a"] for q in d["lowoffs_last"] if q["phase"] == 1 and q["t_s"] >= T_STEP)
        late = sum(d["late_fires"])
        r0 = ref[name]
        a124_mv = r0["step"]["extreme_mv"]
        row = {"peak_after_a": pk, "a124_peak_a": r0["peak_after_a"], "step": st, "a124_extreme_mv": a124_mv,
               "ph1_min_a": ph1, "late": late, "overlaps": d["overlaps"],
               "in_M80": p["band_peak_M80"][0] <= pk <= p["band_peak_M80"][1],
               "in_G80": p["band_peak_G80"][0] <= pk <= p["band_peak_G80"][1],
               "in_mv_band": p["band_abs_mv"][0] <= abs(st["extreme_mv"]) <= p["band_abs_mv"][1]}
        for k, key in (("M80", "in_M80"), ("G80", "in_G80"), ("mv", "in_mv_band")):
            inb[k].append(row[key])
        res[name] = row
        print(f"{name:16s}: peak {pk:6.1f} A (A124 {r0['peak_after_a']:6.1f}, D63 {p['vff']['peak_a']:.0f}), Vo {st['extreme_mv']:+7.2f} mV "
              f"(A124 {a124_mv:+.2f}), back {st['back_within_1pct_us']:.1f} us, ph1 min {ph1:+.1f}, late {late}, overlaps {d['overlaps']}, "
              f"M80 {'in' if row['in_M80'] else 'OUT'}, G80 {'in' if row['in_G80'] else 'OUT'}")
    f = HERE / "cosim" / "run_v125_n0.json"
    if f.exists():
        d = load(f); x = A115.row(d); r0 = ref["p125_n0"]
        x["startup_ipk_a"] = d["ipk_a"]
        res["v125_n0"] = x
        print(f"v125_n0: efficiency {x['efficiency_pct']:.3f}% (A124 {r0['efficiency_pct']:.3f}), start-up {d['ipk_a']:.1f} A "
              f"(A124 {r0['startup_ipk_a']:.1f}), HS " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + " (A124 "
              + "/".join(f"{a:+.2f}" for a in r0["hs_on_vds_v"]) + f"), Vo {x['vo_mean_v']:.5f}")
    c = {}
    if "p125_l_p48_5us" in res:
        c["1_p48_5us_200a"] = res["p125_l_p48_5us"]["peak_after_a"] <= 200.0
    if "p125_l_m48_1us" in res:
        c["2_m48_1us_200a"] = res["p125_l_m48_1us"]["peak_after_a"] <= 200.0
    if "p125_l_p48_1us" in res:
        c["3_p48_1us_minus10a"] = res["p125_l_p48_1us"]["peak_after_a"] <= res["p125_l_p48_1us"]["a124_peak_a"] - 10.0
    steps = [k for k in pr if k in res]
    c["4_loads_3a"] = all(abs(res[k]["peak_after_a"] - res[k]["a124_peak_a"]) <= 3.0 for k in ("p125_s_p62", "p125_s_m62") if k in res)
    c["4_vo_3mv"] = all(abs(res[k]["step"]["extreme_mv"]) <= abs(res[k]["a124_extreme_mv"]) + 3.0 for k in steps)
    c["4_no_overlap_runaway"] = all(res[k]["overlaps"] == 0 and res[k]["late"] <= 100 and res[k]["peak_after_a"] <= 400 for k in steps)
    if "v125_n0" in res:
        x, r0 = res["v125_n0"], ref["p125_n0"]
        c["4_n0"] = (abs(x["efficiency_pct"] - r0["efficiency_pct"]) <= 0.05 and abs(x["startup_ipk_a"] - r0["startup_ipk_a"]) <= 2.0
                     and all(abs(a - b) <= 0.1 for a, b in zip(x["hs_on_vds_v"], r0["hs_on_vds_v"])))
    res["criteria"] = c
    res["a125_prospective"] = {k: f"{sum(v)}/{len(v)}" for k, v in inb.items()}
    print("criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()) + " | A125 bands: " + str(res["a125_prospective"]))
    (HERE / "a128_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
