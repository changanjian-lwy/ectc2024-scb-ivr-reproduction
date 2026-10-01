"""A97 analysis: averaged-period slots against A93 (period-following slots) and A92 (fixed slots), case by case.

Uses A92's row_of() and A93's transient() and case map (read-only imports) and adds A93 RESULTS Section 3's
two-cycle measure, here as two_cycle(): over the last 200 values, half the absolute mean of the alternating
differences. It is applied to each phase's low-side turn-off current, to the period and to each phase's high-side
error (turn-on - valley). A high-side turn-on before the valley (early) has no error reading; two_cycle() then uses
only the pairs of consecutive cycles that both have one, with the sign of the cycle's own parity, which gives the
same value as A93's when nothing is missing. Writes a97_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
sys.path.insert(0, str(TA / "A89_verilog_predicted_low_side"))
sys.path.insert(0, str(TA / "A92_verilog_error_based_correctors"))
sys.path.insert(0, str(TA / "A93_verilog_period_following_slots"))
from a92_analyze import row_of  # noqa: E402
from a93_analyze import SAME, transient  # noqa: E402

A92 = TA / "A92_verilog_error_based_correctors" / "cosim"
A93 = TA / "A93_verilog_period_following_slots" / "cosim"
A93_OF = {"m3n_avg_guard": "m3n_both", "m3n_avg": "m3n_follow", "n0_avg_guard": "n0_both", "m1p_avg_guard": "m1p_both",
          "m1n_avg_guard": "m1n_both", "m3p_avg_guard": "m3p_both", "j30_avg_guard": "j30_both",
          "j100_avg_guard": "j100_both"}
KEEP = ("status", "overlaps", "ipk_a", "vds_max_v", "max_section_abs_i_mode_p_a", "vo_at_handover_v", "handover_period_ns",
        "min_period_after_handover_ns", "late_fires", "ton_final_ns", "period_ns", "vo_v", "last20_max_di_a", "p_rev_w",
        "settle_1pct_us_after_handover", "vcs_last_v", "phase4_turnoff_i_mean_min_max", "all_soft_once_per_cycle")


def two_cycle(x, n=200):
    """Half the absolute mean of the alternating differences of the last n values (A93 RESULTS Section 3); None
    marks a cycle without a reading, and only pairs with both readings count."""
    x = list(x)[-n:]
    terms = [(b - a) * (1.0 if j % 2 == 0 else -1.0) for j, (a, b) in enumerate(zip(x, x[1:]))
             if a is not None and b is not None]
    return float(abs(np.mean(terms)) / 2)


def two_cycle_of(p):
    d = json.loads(p.read_text())
    out = {f"ph{k}_a": two_cycle([o["i_a"] for o in d["lowoffs_last"] if o["phase"] == k]) for k in (1, 2, 3, 4)}
    out["period_ns"] = two_cycle(np.diff([s["t_s"] for s in d["sections"][-201:]]) * 1e9)
    for k in (1, 2, 3, 4):
        e = [t["err_s"] for t in d["turnons_last"] if t["phase"] == k][-200:]
        out[f"eh{k}_ns"] = two_cycle([None if x is None else x * 1e9 for x in e])
        out[f"eh{k}_early_frac"] = sum(x is None for x in e) / len(e)
    return out


def measures(p):
    r = row_of(p); r.update(transient(p))
    r = {k: r.get(k) for k in KEEP}
    r["two_cycle"] = two_cycle_of(p)
    return r


def main():
    out = {"runs": {}, "a93_same_case": {}, "a92_same_case": {}}
    for p in sorted((HERE / "cosim").glob("run_*.json")):
        name = p.stem[4:]
        a93 = A93_OF[name]
        rows = {"A97": measures(p), "A93": measures(A93 / f"run_{a93}.json"),
                "A92": measures(A92 / f"run_{SAME[a93]}.json")}
        out["runs"][name], out["a93_same_case"][name], out["a92_same_case"][name] = rows["A97"], rows["A93"], rows["A92"]
        print(f"\n{name}  (A93 {a93}, A92 {SAME[a93]})")
        for tag, r in rows.items():
            tc = r["two_cycle"]
            line = (f"  {tag}: {r['status']} overlaps {r['overlaps']} ipk {r['ipk_a']:.0f} A Vds {r['vds_max_v']:.1f} V "
                    f"Tmin {r['min_period_after_handover_ns']:.1f} late {r['late_fires']}")
            if r.get("ton_final_ns") is not None:
                line += (f"\n       Ton {r['ton_final_ns']:.3f} T {r['period_ns']:.2f} Vo {r['vo_v']:.4f} "
                         f"dither {r['last20_max_di_a']:.3f} P_rev {r['p_rev_w'] or 0:.3f} "
                         f"settle {r['settle_1pct_us_after_handover']:.1f} VCs {np.round(r['vcs_last_v'], 3).tolist()}"
                         f"\n       two-cycle ph1-4 {[round(tc[f'ph{k}_a'], 3) for k in (1, 2, 3, 4)]} A, "
                         f"period {tc['period_ns']:.3f} ns, high-side error "
                         f"{[round(tc[f'eh{k}_ns'], 3) for k in (1, 2, 3, 4)]} ns, early "
                         f"{[round(tc[f'eh{k}_early_frac'], 3) for k in (1, 2, 3, 4)]}")
            print(line)
    (HERE / "a97_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
