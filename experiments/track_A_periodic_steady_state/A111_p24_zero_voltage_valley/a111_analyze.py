"""A111 analysis against BOUNDARY Section 3, on A110's statistics (a110_analyze.row: high-side turn-on V_DS, valleys,
peaks, low-side maximum, sd, Ton, period and the D62 middle-case budget on the measured waveforms). z5 and z20 are
compared record by record with their sources. Writes a111_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a110_analyze", HERE.parent / "A110_p24_high_side_zvs" / "a110_analyze.py")
A110 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A110)
C02 = A110.C02
A110R = HERE.parent / "A110_p24_high_side_zvs" / "cosim"
SKIP = {"wall_s", "provenance", "cfg", "note"}


def load(p):
    return json.loads(Path(p).read_text())


def identical(a, b):
    x = {k: v for k, v in a.items() if k not in SKIP}
    y = {k: v for k, v in b.items() if k not in SKIP}
    return [k for k in set(x) | set(y) if json.dumps(x.get(k)) != json.dumps(y.get(k))]


def main():
    res = {}
    for name, src in (("z5", C02 / "run_s1_n0.json"), ("z20", A110R / "run_n20.json")):
        p = HERE / "cosim" / f"run_{name}.json"
        if p.exists():
            diff = identical(load(p), load(src))
            res[name] = {"diff_keys": diff, "criteria": {"identical": not diff}}
            print(f"{name}: identical to {src.parent.parent.name}/{src.name}: {not diff}" + (f" (differs: {diff})" if diff else ""))
    for name, ref in (("z25", "n25"), ("z30", "n30")):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        x, r = A110.row(d), A110.row(load(A110R / f"run_{ref}.json"))
        on = [t for t in d["turnons_last"] if t["t_s"] >= d["sections"][-200]["t_s"]]
        x["hs_on_vds_max_v"] = [max(t["vds_v"] for t in on if t["phase"] == k) for k in (1, 2, 3, 4)]
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0}
        if name == "z30":
            c.update(hs_mean_0p3V=max(x["hs_on_vds_v"]) <= 0.3, hs_max_1V=max(x["hs_on_vds_max_v"]) <= 1.0,
                     ls_zvs=max(x["ls_on_vds_max_v"]) <= 0.0, sd_0p5A=max(x["off_sd_a"]) <= 0.5,
                     vo_1mV=abs(x["vo_mean_v"] - 1.0) <= 1e-3, late_5=sum(x["late_fires"]) <= 5,
                     eff_ge_a110=x["efficiency_pct"] >= r["efficiency_pct"], eff_pred=abs(x["efficiency_pct"] - 89.91) <= 0.5,
                     p_rev_0p5W=x["p_rev_w"] <= 0.5)
        else:
            c["hs_mean_0p9V"] = max(x["hs_on_vds_v"]) <= 0.9
        x["criteria"] = c; x["a110"] = {k: r[k] for k in ("hs_on_vds_v", "efficiency_pct", "ipk_a", "off_sd_a")}
        res[name] = x
        print(f"{name}: HS on " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_v"]) + " V (max " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_max_v"])
              + f"), A110 " + "/".join(f"{v:+.2f}" for v in r["hs_on_vds_v"]) + "; valleys " + "/".join(f"{v:+.1f}" for v in x["valleys_a"])
              + ", peaks " + "/".join(f"{v:.0f}" for v in x["peaks_a"]) + f", ipk {x['ipk_a']:.0f} A (A110 {r['ipk_a']:.0f}), LS max {max(x['ls_on_vds_max_v']):+.2f} V, sd "
              + "/".join(f"{v:.2f}" for v in x["off_sd_a"]) + f", late {x['late_fires']}")
        b = x["budget_w"]
        print(f"     efficiency {x['efficiency_pct']:.2f}% (A110 {r['efficiency_pct']:.2f}%), reverse conduction {x['p_rev_w']:.2f} W, hard turn-on {b['hard_turn_on']:.2f} W, "
              f"Ton {x['ton_ns']:.2f} ns, T {x['period_ns']:.1f} ns")
        print("     criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    for name, ref in (("z30_s_p62", "s1_s_p62"), ("z30_s_m62", "s1_s_m62")):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d, rr = load(p), load(C02 / f"run_{ref}.json")
        s, rs = step_stats(d), step_stats(rr)
        c = {"no_overlap": d["overlaps"] == 0, "peak_200a": d["ipk_a"] <= 200.0,
             "step_25pct": abs(s["extreme_mv"] / rs["extreme_mv"] - 1) <= 0.25, "back_15us": s["back_within_1pct_us"] <= 15.0}
        res[name] = {"step": s, "ref_step": rs, "ipk_a": d["ipk_a"], "late_fires": d["late_fires"], "criteria": c}
        print(f"{name}: step {s['extreme_mv']:+.2f} mV, back {s['back_within_1pct_us']:.2f} us (5%: {rs['extreme_mv']:+.2f} / {rs['back_within_1pct_us']:.2f}), "
              f"ipk {d['ipk_a']:.0f} A, late {d['late_fires']}; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    p = HERE / "cosim" / "run_z30_j30.json"
    if p.exists():
        x, r = A110.row(load(p)), A110.row(load(C02 / "run_s1_j30.json"))
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0,
             "sd_band": all(abs(a / b - 1) <= 0.5 for a, b in zip(x["off_sd_a"], r["off_sd_a"])), "hs_0p5V": max(x["hs_on_vds_v"]) <= 0.5}
        x["criteria"] = c
        res["z30_j30"] = x
        print("z30_j30: HS on " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_v"]) + " V, sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"])
              + " (5% j30 " + "/".join(f"{v:.2f}" for v in r["off_sd_a"]) + f"), ipk {x['ipk_a']:.0f} A, efficiency {x['efficiency_pct']:.2f}%; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a111_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a111_summary.json")


if __name__ == "__main__":
    main()
