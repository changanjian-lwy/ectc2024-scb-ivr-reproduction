"""A100 analysis: the timed phase-1 turn-off under load steps (adaptive dlo step, ADM32; A99's +-1 rule, S) and under
jitter, against the comparator design's reference runs and D55's registered predictions (d55_predictions.json,
BOUNDARY Section 5.3).

Step runs: phase 1's turn-off current from 380 us; its largest deviation after the step (400 us) from its mean over
380-400 us; Vo's extreme after the step against the reference run's; peaks, overlaps, status. Jitter runs: A98's
statistics (a98_analyze.cosim_stats) and A99's extra measures. Writes a100_summary.json.
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
sys.path.insert(0, str(TA / "A99_timed_phase1_turn_off"))
from a98_analyze import cosim_stats  # noqa: E402
from a99_analyze import extra  # noqa: E402

T_STEP = 400e-6


def step_measures(d):
    lo = np.array([(o["t_s"], o["i_a"]) for o in d["lowoffs_last"] if o["phase"] == 1 and o["t_s"] >= 380e-6])
    pre = lo[lo[:, 0] < T_STEP, 1].mean() if len(lo) and (lo[:, 0] < T_STEP).any() else float("nan")
    post = lo[lo[:, 0] >= T_STEP]
    dev = post[:, 1] - pre if len(post) else np.array([np.nan])
    sec = [s for s in d["sections"] if s["t_s"] >= T_STEP]
    vo = np.array([s["vo"] for s in sec]) if sec else np.array([np.nan])
    return {"status": d["status"], "t_end_us": d["t_end_s"] * 1e6, "overlaps": d["overlaps"], "first_overlap": d["first_overlap"],
            "ipk_a": d["ipk_a"], "vds_max_v": max(d["vds_max_v"]), "phase1_pre_mean_a": float(pre),
            "phase1_max_abs_dev_a": float(np.nanmax(np.abs(dev))), "phase1_dev_min_max_a": [float(np.nanmin(dev)), float(np.nanmax(dev))],
            "vo_min_v": float(vo.min()), "vo_max_v": float(vo.max()), "vo_final_v": float(vo[-20:].mean()),
            "t_lo_timed_us": None if d.get("t_lo_timed_s") is None else d["t_lo_timed_s"] * 1e6}


def main():
    pred = json.loads((HERE / "d55_predictions.json").read_text())
    out = {"steps": {}, "jitter": {}, "against_d55": {}}
    for step in ("p25", "m25", "p62", "m62"):
        ref = json.loads((HERE / "cosim" / f"run_ref_{step}.json").read_text())
        r = step_measures(ref)
        out["steps"][f"ref_{step}"] = r
        exc_ref = max(1.0 - r["vo_min_v"], r["vo_max_v"] - 1.0)
        print(f"\nstep {step}: reference (comparator): Vo {r['vo_min_v']:.4f}..{r['vo_max_v']:.4f} V, ipk {r['ipk_a']:.0f} A, "
              f"phase 1 dev {r['phase1_max_abs_dev_a']:.2f} A")
        for rule in ("adm", "s"):
            p = HERE / "cosim" / f"run_{rule}_{step}.json"
            if not p.exists():
                continue
            m = step_measures(json.loads(p.read_text()))
            out["steps"][f"{rule}_{step}"] = m
            exc = max(1.0 - m["vo_min_v"], m["vo_max_v"] - 1.0)
            pr = pred.get(f"{rule}_{step}", {}).get("max_abs_phase1_current_error_a")
            line = (f"  {rule.upper():3s}: {m['status']} to {m['t_end_us']:.1f} us, overlaps {m['overlaps']}, ipk {m['ipk_a']:.0f} A, "
                    f"Vds {m['vds_max_v']:.1f} V | phase 1 largest dev {m['phase1_max_abs_dev_a']:.2f} A "
                    f"({m['phase1_dev_min_max_a'][0]:+.2f}..{m['phase1_dev_min_max_a'][1]:+.2f}), predicted {pr} | "
                    f"Vo {m['vo_min_v']:.4f}..{m['vo_max_v']:.4f} V (excursion {exc * 1e3:.1f} mV, reference {exc_ref * 1e3:.1f} mV)")
            if rule == "adm":
                ok = (pr is not None and abs(m["phase1_max_abs_dev_a"] - pr) <= 0.5 * pr and m["overlaps"] == 0
                      and m["ipk_a"] <= 200 and exc <= 1.10 * exc_ref)
                out["against_d55"][f"adm_{step}"] = {"dev_a": m["phase1_max_abs_dev_a"], "predicted_a": pr,
                                                      "vo_excursion_ratio": exc / exc_ref, "agree": ok}
                line += f" | {'MEETS' if ok else 'MISSES'} the criteria"
            else:
                out["against_d55"][f"s_{step}"] = {"dev_a": m["phase1_max_abs_dev_a"], "agree": m["phase1_max_abs_dev_a"] > 10}
                line += f" | S prediction (> 10 A): {'confirmed' if m['phase1_max_abs_dev_a'] > 10 else 'not confirmed'}"
            print(line)
    for name in ("adm_j30", "adm_j100"):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        r = {**cosim_stats(p), **extra(d, p)}
        out["jitter"][name] = r
        pr = pred[name]
        med = pr["ilo_sd_ph1_4_p5_p50_p95"][1]
        sd_rel = [r["ilo_sd_a"][k] / med[k] - 1 for k in range(4)]
        eh_dif = [r["early_high_frac"][k + 1] - pr["early_high_ph2_4_p5_p50_p95"][1][k] for k in range(3)]
        t_rel = r["period_sd_ns"] / pr["period_sd_ns_p5_p50_p95"][1] - 1
        i1 = r["phase1_turnoff_mean_a"] - pr["ilo1_mean_a_p5_p50_p95"][1]
        ok = all(abs(x) <= 0.2 for x in sd_rel) and all(abs(x) <= 0.08 for x in eh_dif) and abs(t_rel) <= 0.3 and abs(i1) <= 0.15
        out["against_d55"][name] = {"spread_rel": sd_rel, "early_dif": eh_dif, "period_sd_rel": t_rel, "phase1_mean_dif": i1, "agree": ok}
        print(f"\n{name}: ilo sd {[round(x, 3) for x in r['ilo_sd_a']]} | early_h {[round(x, 3) for x in r['early_high_frac'][1:]]} | "
              f"T sd {r['period_sd_ns']:.3f} | dither {r['dither_window_mean_sd_a'][0]:.2f} | ph1 mean {r['phase1_turnoff_mean_a']:.3f} | "
              f"P_rev {r['p_rev_w']:.3f} W | ipk {r['ipk_a']:.0f} A overlaps {r['overlaps']}")
        print(f"  vs D55: spread {[f'{x:+.0%}' for x in sd_rel]} | early {[f'{x * 100:+.1f}' for x in eh_dif]} pt | period {t_rel:+.0%} | "
              f"ph1 mean {i1:+.3f} A | {'AGREES' if ok else 'OUTSIDE'}")
    (HERE / "a100_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
