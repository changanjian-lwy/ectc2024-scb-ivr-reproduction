"""C07 analysis against BOUNDARY Section 2 (C07's analysis on the final design; references C06 n0 / s_p62; floor-on vs floor-off controls). Per run: hard
constraints, locked periods and the 16 gaps, each module's valleys and V_DS, the currents normalised to the load,
the step (all_s_p62). Writes c07_summary.json."""
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

spec = importlib.util.spec_from_file_location("c03_analyze", HERE.parent / "C03_four_module_standard_matrix" / "c03_analyze.py")
C03 = importlib.util.module_from_spec(spec); spec.loader.exec_module(C03)
C06R = HERE.parent / "C06_slave_floor" / "cosim"
RUNS = {"cs20_n0": "n0", "r30_n0": "n0", "all_n0": "n0", "all_s_p62": "s_p62", "r30_n0_nf": "n0", "all_n0_nf": "n0"}
R_SYS = 1e-3


def stats(d, t1):
    mods = [d] + d["modules_rest"]
    ws = [window_stats(r, t1=t1) for r in mods]
    _, per = ref_turnons(d, t1)
    offs = [o for r in mods for o in lsoff_after(d, r, t1)]
    t = np.sort(np.mod(np.array(offs), per)); g = np.diff(np.append(t, t[0] + per)) * 1e9
    cur = C03.pl_currents(mods, t1)
    norm = [c / sum(cur) * ws[0]["vo_mean_v"] / R_SYS for c in cur]
    return {"valleys_a": [[p["i_off_mean_a"] for p in w["phases"]] for w in ws],
            "hs_on_vds_v": [[p["hs_on_vds_v"] for p in w["phases"]] for w in ws],
            "ls_on_vds_max_v": [[p["ls_on_vds_max_v"] for p in w["phases"]] for w in ws],
            "period_ns": [w["period_ns"] for w in ws], "gaps_ns": [float(g.min()), float(g.max())], "t16_ns": per / 16 * 1e9,
            "currents_a": norm, "vo_mean_v": ws[0]["vo_mean_v"], "overlaps": [r["overlaps"] for r in mods],
            "ipk_a": [r["ipk_a"] for r in mods], "join_max_v": d["system"]["equalisation_max_v"],
            "late_fires": [sum(r["late_fires"]) for r in mods], "floor_fires_total": [int(r["async_fires"]) for r in mods[1:]]}


def main():
    res = {}
    for name, row in RUNS.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        t1 = 400e-6 if "_s_" in name else None
        d, ref = json.loads(p.read_text()), json.loads((C06R / f"run_{row}.json").read_text())
        x, r = stats(d, t1), stats(ref, t1)
        c = {"no_overlap": all(o == 0 for o in x["overlaps"]), "peak_200a": max(x["ipk_a"]) <= 200.0,
             "locked": all(abs(q - x["period_ns"][0]) <= 0.1 for q in x["period_ns"][1:]),
             "gaps": max(abs(x["gaps_ns"][0] - x["t16_ns"]), abs(x["gaps_ns"][1] - x["t16_ns"])) <= 0.1,
             "join": x["join_max_v"] <= 1e-4, "vo": abs(x["vo_mean_v"] - 1.0) <= 1e-3}
        dv = max(abs(a - b) for m, n in zip(x["valleys_a"], r["valleys_a"]) for a, b in zip(m, n))
        if name == "cs20_n0":
            c["currents_0p5pct"] = all(abs(q / 250 - 1) <= 0.005 for q in x["currents_a"])
            c["valleys_0p35A"] = dv <= 0.35
        if name.startswith("r30"):
            c["currents_-1.2/+1.3pct_pm0.5"] = (abs(x["currents_a"][1] / 250 - 1 + 0.012) <= 0.005 and abs(x["currents_a"][3] / 250 - 1 - 0.013) <= 0.005)
        if name.startswith("all_n0"):
            nom = (x["currents_a"][0] + x["currents_a"][2]) / 2
            c["module1_m5"] = abs((x["currents_a"][1] / nom - 1) + 0.05) <= 0.015
            c["module3_p5"] = abs((x["currents_a"][3] / nom - 1) - 0.05) <= 0.015
            c["valleys_pm3A"] = dv <= 3.0
        if name.endswith("_nf") or name in ("r30_n0", "all_n0"):
            pair = name[:-3] if name.endswith("_nf") else name
            on, off = (res.get(pair), res.get(pair + "_nf")) if pair in res else (None, None)
        if name.endswith("_nf") and name[:-3] in res:
            on = res[name[:-3]]
            dvv = max(abs(a - b) for m, n in zip(x["valleys_a"], on["valleys_a"]) for a, b in zip(m, n))
            dg = max(abs(x["gaps_ns"][i] - on["gaps_ns"][i]) for i in (0, 1))
            x["floor_on_vs_off"] = {"valley_diff_a": dvv, "gap_diff_ns": dg}
            on["criteria"]["floor_inactive_steady"] = dvv <= 0.05 and dg <= 0.05
            on["floor_on_vs_off"] = x["floor_on_vs_off"]
            print(f"   floor on vs off: valley diff {dvv:.3f} A, gap diff {dg:.3f} ns")
        if t1:
            x["step"], r["step"] = step_stats(d), step_stats(ref)
            c["step_10pct"] = abs(x["step"]["extreme_mv"] / r["step"]["extreme_mv"] - 1) <= 0.1
        x["criteria"] = c; x["c06"] = r; x["valley_change_max_a"] = dv
        res[name] = x
        print(f"{name}: overlaps {x['overlaps']}, ipk {[round(v) for v in x['ipk_a']]} A, gaps {x['gaps_ns'][0]:.2f}-{x['gaps_ns'][1]:.2f} ns, "
              f"join {x['join_max_v'] * 1e6:.0f} uV, Vo {x['vo_mean_v']:.5f}, late {x['late_fires']}")
        print("   currents " + "/".join(f"{v:.1f}" for v in x["currents_a"]) + " A (C06 " + "/".join(f"{v:.1f}" for v in r["currents_a"])
              + f"); largest valley change {dv:.2f} A")
        for m in range(4):
            print(f"   module {m}: valleys " + "/".join(f"{v:+.2f}" for v in x["valleys_a"][m]) + ", HS on " + "/".join(f"{v:.2f}" for v in x["hs_on_vds_v"][m])
                  + ", LS max " + "/".join(f"{v:+.2f}" for v in x["ls_on_vds_max_v"][m]))
        if t1:
            print(f"   step {x['step']['extreme_mv']:+.2f} mV (C06 {r['step']['extreme_mv']:+.2f}), back {x['step']['back_within_1pct_us']:.2f} us")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "c07_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote c07_summary.json")


if __name__ == "__main__":
    main()
