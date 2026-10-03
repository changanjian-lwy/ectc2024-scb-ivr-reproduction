"""A129 analysis against BOUNDARY Section 2. Stage 1 (A128's analysis): each step row's peak after the step, Vo
extreme and recovery against A124 and A128, the A125 bands, the gate's g recomputed from the Vin samples (RTL Q8, each
section one sample); identity reruns in tmp/identity_a129/ against A124's / A128's archived runs and the inert rows
against A128's, section by section; n0 by A115's row statistics. Stage 2: matrix.window_stats (last 200 periods) and,
for the load rows, step_stats at 800 us, gated (g125) against off (o125). Writes a129_summary.json."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

A124 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A124_p24_two_point_five_mhz"
A128 = HERE.parent / "A128_cosim_vin_feedforward"
spec = importlib.util.spec_from_file_location("a115_analyze", A124.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
A115.L1 = 7.3333333e-9 / 2.5
T_STEP = 800e-6
KEYS = ("t_s", "v", "i", "vo", "vin_v", "ton_lsb", "vcs_v")
INERT = ("p125_l_p48_1us", "p125_l_p48_5us", "p125_s_p62", "p125_s_m62", "p125_n0")
MATRIX = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")


def load(p):
    return json.loads(Path(p).read_text())


def same(a, b):
    a, b = load(a)["sections"], load(b)["sections"]
    return {"sections": len(a), "identical": len(a) == len(b) and all(all(x[k] == y[k] for k in KEYS) for x, y in zip(a, b))}


def gate_trace(d, gth):
    q, gmax, t_open = None, 0.0, None
    for s in d["sections"]:
        v8 = min(max(int(round(s["vin_v"] / 0.02)), 0), 4095) * 256
        q = v8 if q is None else q + ((v8 - q) >> 2)
        g = max(q - v8, 0) / 256
        gmax = max(gmax, g)
        if t_open is None and g >= gth:
            t_open = (s["t_s"] - T_STEP) * 1e6
    return {"gmax_codes": gmax, "opened_us_after_step": t_open}


def stage1(pr):
    ref, r128 = load(A124 / "a124_summary.json"), load(A128 / "a128_summary.json")
    idd = PROJECT / "tmp" / "identity_a129"
    res = {"identity": {}}
    for name, arch in (("p125_l_p48_1us", A124 / "cosim" / "run_p125_l_p48_1us.json"),
                       ("v125_l_m48_1us", A128 / "cosim" / "run_v125_l_m48_1us.json")):
        if (idd / f"run_{name}.json").exists():
            res["identity"][name] = same(arch, idd / f"run_{name}.json")
    log = PROJECT / "tmp" / "logs" / "a129_run.log"
    res["identity"]["regression_full"] = ("REGRESSION_EXIT 0" in log.read_text()) if log.exists() else None
    res["inert_vs_a128"] = {n: same(A128 / "cosim" / f"run_v{n[1:]}.json", HERE / "cosim" / f"run_g{n[1:]}.json")
                            for n in INERT if (HERE / "cosim" / f"run_g{n[1:]}.json").exists()}
    print("identity:", res["identity"], "| inert:", {k: v["identical"] for k, v in res["inert_vs_a128"].items()})
    inb = {"M80": [], "G80": [], "mv": []}
    for name in pr:
        f = HERE / "cosim" / f"run_g{name[1:]}.json"
        if name.startswith("x_") or name == "gth_codes" or not f.exists():
            continue
        d, p = load(f), pr[name]
        st = step_stats(d, t_step=T_STEP)
        pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
        late = sum(d["late_fires"])
        row = {"peak_after_a": pk, "a124_peak_a": ref[name]["peak_after_a"], "a128_peak_a": r128[name]["peak_after_a"],
               "step": st, "a124_extreme_mv": ref[name]["step"]["extreme_mv"], "a128_extreme_mv": r128[name]["step"]["extreme_mv"],
               "late": late, "overlaps": d["overlaps"], "gate": gate_trace(d, pr["gth_codes"]),
               "in_M80": p["band_peak_M80"][0] <= pk <= p["band_peak_M80"][1],
               "in_G80": p["band_peak_G80"][0] <= pk <= p["band_peak_G80"][1],
               "in_mv_band": p["band_abs_mv"][0] <= abs(st["extreme_mv"]) <= p["band_abs_mv"][1]}
        for k, key in (("M80", "in_M80"), ("G80", "in_G80"), ("mv", "in_mv_band")):
            inb[k].append(row[key])
        res[name] = row
        print(f"{name:16s}: peak {pk:6.1f} A (A124 {row['a124_peak_a']:6.1f}, A128 {row['a128_peak_a']:6.1f}, D63 {p['gated']['peak_a']:.0f}), "
              f"Vo {st['extreme_mv']:+6.1f} mV (A124 {row['a124_extreme_mv']:+.1f}, A128 {row['a128_extreme_mv']:+.1f}), "
              f"back {st['back_within_1pct_us']:.1f} us, gmax {row['gate']['gmax_codes']:.0f}, M80 {'in' if row['in_M80'] else 'OUT'}")
    f = HERE / "cosim" / "run_g125_n0.json"
    if f.exists():
        d = load(f); x = A115.row(d); x["startup_ipk_a"] = d["ipk_a"]; res["g125_n0"] = x
        print(f"g125_n0: efficiency {x['efficiency_pct']:.3f}% (A124 {ref['p125_n0']['efficiency_pct']:.3f}), start-up {d['ipk_a']:.1f} A")
    c = {"0_identity": all(v["identical"] if isinstance(v, dict) else bool(v) for v in res["identity"].values())}
    steps = [k for k in pr if k in res]
    c["1_all_200a"] = all(res[k]["peak_after_a"] <= 200.0 for k in steps)
    if "p125_l_m80_10us" in res:
        r = res["p125_l_m80_10us"]
        c["2_m80_vo"] = abs(r["step"]["extreme_mv"]) <= abs(r["a124_extreme_mv"]) + 3.0
        c["2_m80_back_to_level"] = c["2_m80_vo"] and r["peak_after_a"] <= r["a124_peak_a"] + 3.0
    falls = [k for k in steps if "_l_m" in k]
    c["3_loads_3a"] = all(abs(res[k]["peak_after_a"] - res[k]["a124_peak_a"]) <= 3.0 for k in ("p125_s_p62", "p125_s_m62") if k in res)
    c["3_falls_vo_3mv"] = all(abs(res[k]["step"]["extreme_mv"]) <= abs(res[k]["a124_extreme_mv"]) + 3.0 for k in falls)
    c["3_no_overlap_runaway"] = all(res[k]["overlaps"] == 0 and res[k]["late"] <= 100 and res[k]["peak_after_a"] <= 400 for k in steps)
    if "g125_n0" in res:
        x, r0 = res["g125_n0"], ref["p125_n0"]
        c["3_n0"] = (abs(x["efficiency_pct"] - r0["efficiency_pct"]) <= 0.05 and abs(x["startup_ipk_a"] - r0["startup_ipk_a"]) <= 2.0
                     and all(abs(a - b) <= 0.1 for a, b in zip(x["hs_on_vds_v"], r0["hs_on_vds_v"])))
    c["4_inert_vs_a128"] = len(res["inert_vs_a128"]) == len(INERT) and all(v["identical"] for v in res["inert_vs_a128"].values())
    res["criteria"] = c
    res["a125_prospective"] = {k: f"{sum(v)}/{len(v)}" for k, v in inb.items()}
    return res


def stage2():
    out, c5, c6 = {}, [], []
    n0 = {"o": window_stats(load(A124 / "cosim" / "run_p125_n0.json")), "g": window_stats(load(HERE / "cosim" / "run_g125_n0.json"))}
    for row in MATRIX:
        for arm in ("o", "g"):
            f = HERE / "cosim" / f"run_{arm}125_{row}.json"
            if not f.exists():
                continue
            d = load(f); w = window_stats(d); x = {"window": w, "late": sum(d["late_fires"])}
            if row.startswith("s_"):
                x["step"] = step_stats(d, t_step=T_STEP)
                x["peak_after_a"] = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
            ok = w["overlaps"] == 0 and x["late"] <= 100 and w["ipk_a"] <= 200.0 and x.get("peak_after_a", 0) <= 200.0
            if row[0] in "mj":
                ok &= all(abs(p["hs_on_vds_v"] - q["hs_on_vds_v"]) <= 0.5 for p, q in zip(w["phases"], n0[arm]["phases"]))
            if row[0] == "m":
                ok &= all(p["ls_on_vds_max_v"] <= 0.0 for p in w["phases"])
            if row == "j30":
                ok &= all(p["i_off_sd_a"] <= 0.5 for p in w["phases"])
            if row.startswith("s_"):
                ok &= math.isfinite(x["step"]["back_within_1pct_us"]) and x["step"]["back_within_1pct_us"] <= 60.0
            x["c5"] = bool(ok); c5.append(ok)
            out[f"{arm}125_{row}"] = x
        if f"o125_{row}" in out and f"g125_{row}" in out:
            o, g = out[f"o125_{row}"], out[f"g125_{row}"]
            ok = abs(g["window"]["ipk_a"] - o["window"]["ipk_a"]) <= 3.0
            ok &= all(abs(p["hs_on_vds_v"] - q["hs_on_vds_v"]) <= 0.1 and
                      abs(p["i_off_sd_a"] - q["i_off_sd_a"]) <= max(0.2 * q["i_off_sd_a"], 0.05)
                      for p, q in zip(g["window"]["phases"], o["window"]["phases"]))
            if row.startswith("s_"):
                ok &= abs(g["peak_after_a"] - o["peak_after_a"]) <= 3.0 and abs(g["step"]["extreme_mv"] - o["step"]["extreme_mv"]) <= 3.0
            out[f"g125_{row}"]["c6"] = bool(ok); c6.append(ok)
        for arm in ("o", "g"):
            x = out.get(f"{arm}125_{row}")
            if x:
                w = x["window"]
                print(f"{arm}125_{row:5s}: ipk {w['ipk_a']:6.1f} A, i_off " + "/".join(f"{p['i_off_mean_a']:+.2f}" for p in w["phases"])
                      + " sd " + "/".join(f"{p['i_off_sd_a']:.2f}" for p in w["phases"]) + ", HS " + "/".join(f"{p['hs_on_vds_v']:.2f}" for p in w["phases"])
                      + (f", step pk {x['peak_after_a']:.1f} Vo {x['step']['extreme_mv']:+.1f} mV back {x['step']['back_within_1pct_us']:.1f} us"
                         if "step" in x else "") + f", c5 {'ok' if x['c5'] else 'MISS'}" + (f", c6 {'ok' if x['c6'] else 'MISS'}" if "c6" in x else ""))
    out["criteria"] = {"5_matrix_both_arms": bool(c5) and all(c5), "6_gated_vs_off": bool(c6) and all(c6), "n_runs": len(c5)}
    out["n0_windows"] = n0
    return out


def posthoc(pr):
    """Not registered criteria: d125 (cap off) against A124; the x rows against their registered D63 predictions; the
    post-step peak's spread when the step moves by 1/3 and 2/3 of a period (no125 / ng125)."""
    cos, out = HERE / "cosim", {}
    if (cos / "run_d125_l_m80_10us.json").exists():
        out["d125_vs_a124"] = same(A124 / "cosim" / "run_p125_l_m80_10us.json", cos / "run_d125_l_m80_10us.json")
    for name in ("x_l_m48_2us", "x_l_m48_3us", "x_l_m80_5us"):
        f = cos / f"run_x125{name[1:]}.json"
        if f.exists():
            d, p = load(f), pr[name]
            pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
            out[name] = {"peak_after_a": pk, "extreme_mv": step_stats(d, t_step=T_STEP)["extreme_mv"], "d63_gated_a": p["gated"]["peak_a"],
                         "band_peak_M80": p["band_peak_M80"], "in_M80": p["band_peak_M80"][0] <= pk <= p["band_peak_M80"][1],
                         "gate": gate_trace(d, pr["gth_codes"])}
    spread = {}
    for arm, base in (("o125_s_m25", cos / "run_o125_s_m25.json"), ("g125_s_m25", cos / "run_g125_s_m25.json"),
                      ("o125_l_m80_10us", A124 / "cosim" / "run_p125_l_m80_10us.json")):
        vals = []
        for t, f in ((800.0, base), (800.17, cos / f"run_n{arm}_t17.json"), (800.33, cos / f"run_n{arm}_t33.json")):
            if f.exists():
                d = load(f)
                vals.append({"t_step_us": t, "peak_after_a": max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= t * 1e-6),
                             "extreme_mv": step_stats(d, t_step=t * 1e-6)["extreme_mv"]})
        spread[arm] = vals
    out["step_phase_spread"] = spread
    for k, v in out.items():
        print("posthoc", k, v if k != "step_phase_spread" else {a: [(x["t_step_us"], round(x["peak_after_a"], 1), round(x["extreme_mv"], 1))
                                                                  for x in vals] for a, vals in v.items()})
    return out


def main():
    pr = load(HERE / "a129_predictions.json")
    res = {"stage1": stage1(pr)}
    if (HERE / "cosim" / "run_g125_n0.json").exists():
        res["stage2"] = stage2()
    res["posthoc"] = posthoc(pr)
    print("criteria:", res["stage1"]["criteria"], res.get("stage2", {}).get("criteria"), "| A125:", res["stage1"]["a125_prospective"])
    (HERE / "a129_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
