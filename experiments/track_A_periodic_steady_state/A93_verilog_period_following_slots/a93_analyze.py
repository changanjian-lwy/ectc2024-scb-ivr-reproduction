"""A93 analysis: the gate g1 against A92 m3n, the slot rules in the m3n case, and the A92 matrix with both rules.

Uses A89's gate() and A92's row_of() (read-only imports, which bring A89's summarize and A91's measures) and adds
the transient measures of BOUNDARY Section 4: peak current and Vds over the run, the largest section current in
mode P, Vo at the handover, the shortest period after the handover cycle, late fires per phase, and the A92 run
of the same case. Writes a93_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A89_verilog_predicted_low_side"))
sys.path.insert(0, str(HERE.parent / "A92_verilog_error_based_correctors"))
from a89_analyze import gate  # noqa: E402
from a92_analyze import row_of  # noqa: E402

A92 = HERE.parent / "A92_verilog_error_based_correctors" / "cosim"
SAME = {"g1_gate_a92m3n": "m3n_mismatch_minus3p4ns", "m3n_guard": "m3n_mismatch_minus3p4ns",
        "m3n_follow": "m3n_mismatch_minus3p4ns", "m3n_both": "m3n_mismatch_minus3p4ns", "n0_both": "n0_nominal",
        "m1p_both": "m1p_mismatch_plus1ns", "m1n_both": "m1n_mismatch_minus1ns", "m3p_both": "m3p_mismatch_plus3p4ns",
        "j30_both": "j30_jitter_30ps", "j100_both": "j100_jitter_100ps"}


def transient(p):
    d = json.loads(p.read_text())
    s = [x for x in d["sections"] if x["mode_p"]]
    t = np.array([x["t_s"] for x in s])
    per = np.diff(t) * 1e9
    return {"ipk_a": d["ipk_a"], "vds_max_v": max(d["vds_max_v"]), "vo_at_handover_v": s[0]["vo"],
            "max_section_abs_i_mode_p_a": float(max(max(abs(v) for v in x["i"]) for x in s)),
            "handover_period_ns": float(per[0]), "min_period_after_handover_ns": float(per[1:].min()),
            "late_fires": d["late_fires"], "vcs_last_v": s[-1]["vcs_v"]}


def main():
    out = {"gates": {}, "runs": {}, "a92_same_case": {}}
    g1 = HERE / "cosim" / "run_g1_gate_a92m3n.json"
    if g1.exists():
        out["gates"]["g1_vs_A92_m3n"] = gate((A92 / "run_m3n_mismatch_minus3p4ns.json").resolve(), g1.resolve())
        print("GATE g1_vs_A92_m3n", out["gates"]["g1_vs_A92_m3n"])
    for p in sorted((HERE / "cosim").glob("run_*.json")):
        name = p.stem[4:]
        r = row_of(p); r.update(transient(p))
        out["runs"][name] = r
        q = A92 / f"run_{SAME[name]}.json"
        a = row_of(q); a.update(transient(q))
        keep = ("last20_max_di_a", "p_rev_w", "ton_final_ns", "period_ns", "ipk_a", "vds_max_v", "vo_at_handover_v",
                "min_period_after_handover_ns", "max_section_abs_i_mode_p_a", "settle_1pct_us_after_handover", "vcs_last_v",
                "phase4_turnoff_i_mean_min_max", "dtl_final_ns", "dt_pred_final_ns")
        out["a92_same_case"][name] = {k: a.get(k) for k in keep}
        print(f"{name:16s} {r['status']} overlaps {r['overlaps']} ipk {r['ipk_a']:.0f} A Vdsmax {r['vds_max_v']:.1f} V "
              f"max|i| sec {r['max_section_abs_i_mode_p_a']:.0f} | Vo@hand {r['vo_at_handover_v']:.3f} T_hand "
              f"{r['handover_period_ns']:.1f} Tmin {r['min_period_after_handover_ns']:.1f} late {r['late_fires']}")
        if "ton_final_ns" in r:
            print(f"   Ton {r['ton_final_ns']:.3f} T {r['period_ns']:.2f} Vo {r['vo_v']:.4f} soft {r['all_soft_once_per_cycle']} "
                  f"dither {r['last20_max_di_a']:.3f} P_rev {r.get('p_rev_w', 0):.3f} settle {r['settle_1pct_us_after_handover']:.1f} "
                  f"VCs {np.round(r['vcs_last_v'], 3).tolist()} ph4 {np.round(r['phase4_turnoff_i_mean_min_max'], 2).tolist()}")
            print(f"   A92: Ton {a['ton_final_ns']:.3f} T {a['period_ns']:.2f} dither {a['last20_max_di_a']:.3f} "
                  f"P_rev {a.get('p_rev_w', 0):.3f} ipk {a['ipk_a']:.0f} Tmin {a['min_period_after_handover_ns']:.1f} "
                  f"settle {a['settle_1pct_us_after_handover']:.1f} VCs {np.round(a['vcs_last_v'], 3).tolist()} "
                  f"ph4 {np.round(a['phase4_turnoff_i_mean_min_max'], 2).tolist()}")
    (HERE / "a93_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
