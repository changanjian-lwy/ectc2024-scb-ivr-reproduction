"""A99 analysis: the timed phase-1 turn-off against A97 (comparator) and D54's registered predictions.

1. Gate: every section of an A99 run before its first timed turn-off (t_lo_timed_s) is equal, field by field, to the
   A97 run of the same configuration.
2. Statistics over the last 200 cycles with A98's definitions (a98_analyze.cosim_stats), phase 1's mean turn-off
   current, its crossing reports (early fraction, turn-off - crossing), the transient and loss measures of A92's
   row_of (peak current and V_DS, P_rev, A91's hard-on estimate, turn-on V_DS), and A97's same statistics.
3. Against d54_predictions.json (BOUNDARY Section 5.3). Writes a99_summary.json.
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
sys.path.insert(0, str(TA / "A98_jitter_amplification"))
from a92_analyze import row_of  # noqa: E402
from a98_analyze import cosim_stats  # noqa: E402

A97 = TA / "A97_verilog_averaged_period_slots" / "cosim"
REF = {"n0": "n0_avg_guard", "m3n": "m3n_avg_guard", "j30": "j30_avg_guard", "j100": "j100_avg_guard"}
LAST = 200


def gate(a99, a97):
    """Sections before the switch: count compared, and whether all are equal."""
    t_sw = a99.get("t_lo_timed_s")
    s99 = [s for s in a99["sections"] if t_sw is None or s["t_s"] < t_sw]
    s97 = a97["sections"][:len(s99)]
    same = len(s97) == len(s99) and all(x == y for x, y in zip(s97, s99))
    return {"t_switch_us": None if t_sw is None else t_sw * 1e6, "sections_before_switch": len(s99), "identical": same}


def extra(d, p):
    r = row_of(p)
    lo1 = [o["i_a"] for o in d["lowoffs_last"] if o["phase"] == 1][-LAST:]
    out = {"ipk_a": d["ipk_a"], "vds_max_v": max(d["vds_max_v"]), "overlaps": d["overlaps"], "status": d["status"],
           "ton_final_ns": r["ton_final_ns"], "vo_v": r["vo_v"], "p_rev_w": r.get("p_rev_w", 0.0),
           "hard_on_estimate": r.get("hard_on_estimate_mode_p"), "turnon_vds_mean_max_last50": r.get("turnon_vds_mean_max_last50"),
           "vcs_last_v": d["sections"][-1]["vcs_v"], "phase1_turnoff_mean_a": float(np.mean(lo1)),
           "period_ns": r["period_ns"], "dither_last20_a": r["last20_max_di_a"]}
    reps = d.get("lo_reports_last")
    if reps:
        reps = reps[-LAST:]
        err = [x["err_s"] * 1e9 for x in reps if not x["early"]]
        out.update(lo_early_frac=float(np.mean([x["early"] for x in reps])),
                   lo_err_mean_sd_ns=[float(np.mean(err)), float(np.std(err))] if err else None,
                   dlo1_final_lsb=d.get("dlo1_final_lsb"))
    return out


def main():
    pred = json.loads((HERE / "d54_predictions.json").read_text())
    out = {"runs": {}, "a97": {}, "gates": {}, "against_d54": {}}
    for name, ref in REF.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d, q = json.loads(p.read_text()), A97 / f"run_{ref}.json"
        d97 = json.loads(q.read_text())
        out["gates"][name] = gate(d, d97)
        out["runs"][name] = {**cosim_stats(p), **extra(d, p)}
        out["a97"][name] = {**cosim_stats(q), **extra(d97, q)}
        r, a = out["runs"][name], out["a97"][name]
        g = out["gates"][name]
        f = lambda v: [round(x, 3) for x in v]  # noqa: E731
        print(f"\n{name}: gate {'IDENTICAL' if g['identical'] else 'DIFFERENT'} over {g['sections_before_switch']} sections "
              f"before the switch at {g['t_switch_us']:.1f} us")
        for tag, x in (("A99", r), ("A97", a)):
            print(f"  {tag}: ilo sd {f(x['ilo_sd_a'])} | early_h {f(x['early_high_frac'][1:])} | T sd {x['period_sd_ns']:.3f} | "
                  f"dither {x['dither_window_mean_sd_a'][0]:.2f} | ph1 off {x['phase1_turnoff_mean_a']:.3f} A | ipk {x['ipk_a']:.0f} A "
                  f"Vds {x['vds_max_v']:.1f} V overlaps {x['overlaps']} | P_rev {x['p_rev_w']:.3f} W | hard-on "
                  f"{[round(v * 1e3, 3) for v in (x['hard_on_estimate'] or {}).get('p_hard_on_w_low_high', [])]} mW | "
                  f"Ton {x['ton_final_ns']:.3f} Vo {x['vo_v']:.4f}"
                  + (f" | lo early {x['lo_early_frac']:.2f} err {np.round(x['lo_err_mean_sd_ns'], 3).tolist()} ns" if x.get("lo_early_frac") is not None else ""))
        pr = pred.get(name)
        if pr and pr["sigma_ps"] > 0:
            med = pr["ilo_sd_ph1_4_p5_p50_p95"][1]
            sd_rel = [r["ilo_sd_a"][k] / med[k] - 1 for k in range(4)]
            eh_dif = [r["early_high_frac"][k + 1] - pr["early_high_ph2_4_p5_p50_p95"][1][k] for k in range(3)]
            t_rel = r["period_sd_ns"] / pr["period_sd_ns_p5_p50_p95"][1] - 1
            i1_dif = r["phase1_turnoff_mean_a"] - pr["ilo1_mean_a_p5_p50_p95"][1]
            ok = (all(abs(x) <= 0.20 for x in sd_rel) and all(abs(x) <= 0.08 for x in eh_dif) and abs(t_rel) <= 0.30
                  and abs(i1_dif) <= 0.15)
            out["against_d54"][name] = {"spread_rel": sd_rel, "early_dif": eh_dif, "period_sd_rel": t_rel,
                                        "phase1_mean_dif_a": i1_dif, "agree": ok}
            print(f"  vs D54: spread {[f'{x:+.0%}' for x in sd_rel]} | early {[f'{x * 100:+.1f}' for x in eh_dif]} pt | "
                  f"period sd {t_rel:+.0%} | ph1 mean {i1_dif:+.3f} A | {'AGREES' if ok else 'OUTSIDE'}")
        elif pr:
            ok = max(r["ilo_sd_a"][1:]) <= 0.10 and r["dither_window_mean_sd_a"][0] <= 0.2
            out["against_d54"][name] = {"spread_ph2_4_max": max(r["ilo_sd_a"][1:]), "dither": r["dither_window_mean_sd_a"][0],
                                        "agree": ok}
            print(f"  vs criterion (spread <= 0.10 A, dither <= 0.2 A): {'MET' if ok else 'NOT MET'}")
    (HERE / "a99_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
