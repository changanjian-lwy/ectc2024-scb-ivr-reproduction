"""A109 analysis against BOUNDARY Section 3. Steady and load-step rows: the shared window statistics against C02's
one-module runs (C03's for m4_n0); line rows: A108's transient statistics (a108_analyze.summary) against A108's runs;
m4_ls_p10: slave 1's current (C03's piecewise-linear currents) and valleys. Writes a109_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import lsoff_after, ref_turnons, step_stats, window_stats  # noqa: E402

TA = HERE.parent
C = TA.parent / "track_C_multi_module"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


A108 = module(TA / "A108_p24_line_slew_tolerance" / "a108_analyze.py", "a108_analyze")
C03 = module(C / "C03_four_module_standard_matrix" / "c03_analyze.py", "c03_analyze")
REF = {"s1_n0": C / "C02_uniform_interleave" / "cosim" / "run_s1_n0.json",
       "s1_j30": C / "C02_uniform_interleave" / "cosim" / "run_s1_j30.json",
       "s1_s_m62": C / "C02_uniform_interleave" / "cosim" / "run_s1_s_m62.json",
       "s1_s_p62": C / "C02_uniform_interleave" / "cosim" / "run_s1_s_p62.json",
       "m4_n0": C / "C03_four_module_standard_matrix" / "cosim" / "run_n0.json",
       "m4_ls_p10": C / "C03_four_module_standard_matrix" / "cosim" / "run_ls_p10.json",
       "m4_l_m48_10us": C / "C03_four_module_standard_matrix" / "cosim" / "run_l_m48_10us.json"}
LINE = ("m48_1us", "m48_10us", "m48_50us", "p48_1us", "p48_10us")
TGT = -6.25


def load(p):
    return json.loads(Path(p).read_text())


def steady(d, t1=None):
    mods = [d] + d.get("modules_rest", [])
    ws = [window_stats(r, t1=t1) for r in mods]
    out = {"valleys_a": [[p["i_off_mean_a"] for p in w["phases"]] for w in ws],
           "hs_on_vds_v": [[p["hs_on_vds_v"] for p in w["phases"]] for w in ws],
           "ls_on_vds_max_v": [[p["ls_on_vds_max_v"] for p in w["phases"]] for w in ws],
           "off_sd_a": [[p["i_off_sd_a"] for p in w["phases"]] for w in ws],
           "vo_mean_v": ws[0]["vo_mean_v"], "overlaps": [r["overlaps"] for r in mods], "ipk_a": [r["ipk_a"] for r in mods],
           "slot_ofs_lsb": [r.get("slot_ofs_final_lsb") for r in mods], "late_fires": [r["late_fires"] for r in mods]}
    if len(mods) > 1:
        _, per = ref_turnons(d, t1)
        offs = [o for r in mods for o in lsoff_after(d, r, t1)]
        t = np.sort(np.mod(np.array(offs), per))
        g = np.diff(np.append(t, t[0] + per)) * 1e9
        out.update(gaps_ns=[float(g.min()), float(g.max())], t16_ns=per / 16 * 1e9)
    return out


def main():
    res = {}
    for name in ("s1_n0", "s1_j30", "s1_s_m62", "s1_s_p62", "m4_n0", "m4_ls_p10"):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        t1 = 400e-6 if "_s_" in name else None
        d, r = load(p), load(REF[name])
        x, rx = steady(d, t1), steady(r, t1)
        c = {"no_overlap": all(o == 0 for o in x["overlaps"]), "peak_200a": max(x["ipk_a"]) <= 200.0}
        if name in ("s1_n0", "m4_n0"):
            slotted = [v for m, vs in enumerate(x["valleys_a"]) for k, v in enumerate(vs) if k > 0 or m > 0]
            c["slotted_valleys_0p3A"] = all(abs(v - TGT) <= 0.3 for v in slotted)
            c["phase1_master"] = abs(x["valleys_a"][0][0] - rx["valleys_a"][0][0]) <= 0.05
            c["hs_on_0p15V"] = all(abs(a - b) <= 0.15 for m, n in zip(x["hs_on_vds_v"], rx["hs_on_vds_v"]) for a, b in zip(m, n))
            c["ls_zvs"] = max(v for m in x["ls_on_vds_max_v"] for v in m) <= 0.0
            c["ofs_64"] = all(abs(o) <= 64 for m in x["slot_ofs_lsb"] for o in m)
            c["vo_1mV"] = abs(x["vo_mean_v"] - 1.0) <= 1e-3
            if "gaps_ns" in x:
                c["gaps_2ns"] = max(abs(x["gaps_ns"][0] - x["t16_ns"]), abs(x["gaps_ns"][1] - x["t16_ns"])) <= 2.0
        if name == "s1_j30":
            c["sd_band"] = all(abs(a / b - 1) <= 0.3 for a, b in zip(x["off_sd_a"][0], rx["off_sd_a"][0]))
        if t1:
            x["step"], rx["step"] = step_stats(d), step_stats(r)
            c["step_10pct"] = abs(x["step"]["extreme_mv"] / rx["step"]["extreme_mv"] - 1) <= 0.1
        if name == "m4_ls_p10":
            cur = C03.pl_currents([d] + d["modules_rest"], None)
            x["currents_a"] = cur; x["slave1_rel"] = cur[1] / ((cur[2] + cur[3]) / 2) - 1
            c["slave1_valleys_0p3A"] = all(abs(v - TGT) <= 0.3 for v in x["valleys_a"][1])
            c["slave1_current_d61"] = abs(x["slave1_rel"] + 0.100) <= 0.01
            c["slave1_ls_zvs"] = max(x["ls_on_vds_max_v"][1]) <= 0.0
        x["criteria"] = c; x["ref"] = rx
        res[name] = x
        print(f"{name}: overlaps {x['overlaps']}, ipk {[round(v) for v in x['ipk_a']]} A, Vo {x['vo_mean_v']:.5f}, late {x['late_fires']}, "
              f"offsets {x['slot_ofs_lsb']}" + (f", gaps {x['gaps_ns'][0]:.2f}-{x['gaps_ns'][1]:.2f} ns" if "gaps_ns" in x else ""))
        for m in range(len(x["valleys_a"])):
            print(f"   module {m}: valleys " + "/".join(f"{v:+.2f}" for v in x["valleys_a"][m]) + " (before " + "/".join(f"{v:+.2f}" for v in rx["valleys_a"][m])
                  + "), HS on " + "/".join(f"{v:.2f}" for v in x["hs_on_vds_v"][m]) + " (" + "/".join(f"{v:.2f}" for v in rx["hs_on_vds_v"][m])
                  + "), LS max " + "/".join(f"{v:+.2f}" for v in x["ls_on_vds_max_v"][m]) + ", sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"][m]))
        if "step" in x:
            print(f"   step {x['step']['extreme_mv']:+.2f} mV (before {rx['step']['extreme_mv']:+.2f})")
        if "currents_a" in x:
            print("   currents " + "/".join(f"{v:.1f}" for v in x["currents_a"]) + f" A; slave 1 {x['slave1_rel'] * 100:+.2f}%")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    for r in LINE:
        p = HERE / "cosim" / f"run_s1_{r}.json"
        if not p.exists():
            continue
        x, b = A108.summary(load(p)), A108.summary(load(TA / "A108_p24_line_slew_tolerance" / "cosim" / f"run_{r}.json"))
        c = {"no_overlap": x["overlaps"] == 0}
        vmax = [q["valley_max_a"] for q in x["phases"]]; vmin = [q["valley_min_a"] for q in x["phases"]]
        if r in ("m48_10us", "m48_50us"):
            c["valleys_le_m2A"] = max(vmax) <= -2.0
        if r == "m48_1us":
            c["slotted_max_le_25A"] = max(vmax[1:]) <= 25.0
        if r.startswith("p"):
            c["phase1_unchanged"] = abs(vmax[0] - b["phases"][0]["valley_max_a"]) <= 3.0
            c["slotted_min_ge_m15A"] = min(vmin[1:]) >= -15.0
        x["criteria"] = c; x["a108"] = b
        res[f"s1_{r}"] = x
        print(f"s1_{r}: overlaps {x['overlaps']}, ipk {x['ipk_a']:.1f} A, peaks " + "/".join(f"{q['peak_a']:.0f}" for q in x["phases"])
              + ", valleys " + " ".join(f"[{q['valley_min_a']:+.1f},{q['valley_max_a']:+.1f}]" for q in x["phases"])
              + f", HS-on max {x['hs_on_vds_max_v']:.1f} V, Vo {x['vo_extreme_mv']:+.2f} mV, late {x['late_fires']}")
        print("   A108: peaks " + "/".join(f"{q['peak_a']:.0f}" for q in b["phases"]) + ", valleys "
              + " ".join(f"[{q['valley_min_a']:+.1f},{q['valley_max_a']:+.1f}]" for q in b["phases"]) + f", HS-on max {b['hs_on_vds_max_v']:.1f} V, Vo {b['vo_extreme_mv']:+.2f} mV")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    p = HERE / "cosim" / "run_m4_l_m48_10us.json"
    if p.exists():
        d = load(p)
        rows = [A108.summary(m) for m in [d] + d["modules_rest"]]
        ref = load(REF["m4_l_m48_10us"]); rrows = [A108.summary(m) for m in [ref] + ref["modules_rest"]]
        x = {"modules": rows, "c03": rrows, "criteria": {"no_overlap": all(q["overlaps"] == 0 for q in rows),
                                                          "all_valleys_negative": all(q["valley_max_a"] < 0 for q in rows)}}
        res["m4_l_m48_10us"] = x
        print("m4_l_m48_10us: most positive valley per module " + "/".join(f"{q['valley_max_a']:+.1f}" for q in rows)
              + " A (C03 " + "/".join(f"{q['valley_max_a']:+.1f}" for q in rrows) + "), peaks " + "/".join(f"{q['peak_a']:.0f}" for q in rows)
              + "; criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in x["criteria"].items()))
    (HERE / "a109_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a109_summary.json")


if __name__ == "__main__":
    main()
