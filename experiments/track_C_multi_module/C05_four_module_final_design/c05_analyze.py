"""C05 analysis against BOUNDARY Section 3 (C03's analysis on the final design: A129's single-module g125 runs are the references), on the shared statistics (scb_ivr.cosim.matrix). Per row, over the last 200
master periods (before the step for step and line rows): hard constraints; locked periods and the 16 gaps; each module
against the row's single-module run (A105 i2_<row>, A106 pi100_<row>); the step against the single module's; for the
larger-slave rows, slave 1 against the nominal slaves (current from the piecewise-linear waveforms, valleys, V_DS);
late fires; the output current ripple. Writes c05_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import (GRID_S, lsoff_after, output_ripple, phase_waveform, ref_turnons,  # noqa: E402
                                  step_stats, window_stats)

TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
A129 = PROJECT / "extensions" / "ml_design_assist" / "experiments" / "A129_cosim_vff_slope_gate" / "cosim"
LS = {"ls_p5": (0.046, 0.015), "ls_p10": (0.09, 0.03)}
ROW_LIST = ("n0", "m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25", "s_m62", "s_p62", "l_p48_1us", "l_p48_5us",
            "l_m48_1us", "l_m48_5us", "l_m80_10us")
ZERO_DRIVER = ("n0", "s_m25", "s_p25", "s_m62", "s_p62", "l_m48_1us", "l_p48_1us", "l_m48_5us", "l_p48_5us",
               "l_m80_10us", "ls_p5", "ls_p10")
T_STEP = 800e-6


def load(p):
    return json.loads(Path(p).read_text())


def ref_path(row):
    if row.startswith("ls_"):
        return HERE / "cosim" / "run_n0.json"
    return A129 / f"run_g125_{row}.json"


def late(d):
    return int(sum(d["late_fires"]))


def gaps(offsets, period):
    t = np.sort(np.mod(np.array(offsets), period))
    return np.diff(np.append(t, t[0] + period))


def pl_currents(mods, t1):
    t_on, _ = ref_turnons(mods[0], t1)
    g = np.arange(t_on[0], t_on[-1], GRID_S)
    return [float(sum(phase_waveform(r, k, g).mean() for k in range(1, 5))) for r in mods]


def ph(w, key):
    return [p[key] for p in w["phases"]]


def analyse(row):
    d = load(HERE / "cosim" / f"run_{row}.json")
    mods = [d] + d["modules_rest"]
    stepped = row.startswith(("s_", "l_"))
    t1 = T_STEP if stepped else None
    ws = [window_stats(r, t1=t1) for r in mods]
    ref = load(ref_path(row))
    ref_mods = [ref] + ref.get("modules_rest", [])
    rw = window_stats(ref, t1=t1)
    _, per = ref_turnons(d, t1)
    g = gaps([o for r in mods for o in lsoff_after(d, r, t1)], per) * 1e9
    x = {"status": [r["status"] for r in mods], "overlaps": [r["overlaps"] for r in mods], "ipk_a": [r["ipk_a"] for r in mods],
         "period_ns": [w["period_ns"] for w in ws], "gaps_ns": [float(g.min()), float(g.max())], "t16_ns": per / 16 * 1e9,
         "valleys_a": [ph(w, "i_off_mean_a") for w in ws], "hs_on_vds_v": [ph(w, "hs_on_vds_v") for w in ws],
         "ls_on_vds_max_v": [ph(w, "ls_on_vds_max_v") for w in ws], "off_sd_a": [ph(w, "i_off_sd_a") for w in ws],
         "late_fires": [late(r) for r in mods], "ref_late_fires": sum(late(r) for r in ref_mods),
         "ripple": output_ripple(mods, t1=t1), "vo_mean_v": ws[0]["vo_mean_v"],
         "ref": {"valleys_a": ph(rw, "i_off_mean_a"), "hs_on_vds_v": ph(rw, "hs_on_vds_v"),
                 "ls_on_vds_max_v": ph(rw, "ls_on_vds_max_v"), "off_sd_a": ph(rw, "i_off_sd_a"), "ipk_a": ref["ipk_a"]}}
    c = {"no_overlap": all(o == 0 for o in x["overlaps"]), "peak_200a": max(x["ipk_a"]) <= 200.0 or stepped,
         "locked": all(abs(p - x["period_ns"][0]) <= 0.1 for p in x["period_ns"][1:])}
    if row in ZERO_DRIVER:
        c["uniform_T16"] = max(abs(x["gaps_ns"][0] - x["t16_ns"]), abs(x["gaps_ns"][1] - x["t16_ns"])) <= 0.1
    if not stepped and not row.startswith("ls_"):
        r = x["ref"]
        c["valleys_0p5A"] = all(abs(a - b) <= 0.5 for m in x["valleys_a"] for a, b in zip(m, r["valleys_a"]))
        c["hs_on_0p2V"] = all(abs(a - b) <= 0.2 for m in x["hs_on_vds_v"] for a, b in zip(m, r["hs_on_vds_v"]))
        c["ls_on_ref_0p3V"] = all(a <= b + 0.3 for m in x["ls_on_vds_max_v"] for a, b in zip(m, r["ls_on_vds_max_v"]))
        c["sd_band"] = all((abs(a / b - 1) <= 0.3) if b >= 0.17 else (abs(a - b) <= 0.05)
                           for m in x["off_sd_a"] for a, b in zip(m, r["off_sd_a"]))
    if stepped:
        x["peak_after_a"] = [max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= T_STEP) for r in mods]
        c["peak_after_200a"] = max(x["peak_after_a"]) <= 200.0
        s, rs = step_stats(d, t_step=T_STEP), step_stats(ref, t_step=T_STEP)
        x["step"], x["ref_step"] = s, rs
        c["step_10pct"] = abs(s["extreme_mv"] / rs["extreme_mv"] - 1) <= 0.1
        c["back_2us"] = s["back_within_1pct_us"] <= rs["back_within_1pct_us"] + 2.0
        c["ladder_0p01"] = s["ladder_dev_peak"] <= rs["ladder_dev_peak"] + 0.01
    if row.startswith("ls_"):
        cur = pl_currents(mods, None)
        nom = (cur[2] + cur[3]) / 2
        v1, vn = np.array(x["valleys_a"][1]), (np.array(x["valleys_a"][2]) + np.array(x["valleys_a"][3])) / 2
        h1, hn = np.array(x["hs_on_vds_v"][1]), (np.array(x["hs_on_vds_v"][2]) + np.array(x["hs_on_vds_v"][3])) / 2
        x.update(currents_a=cur, slave1_rel=cur[1] / nom - 1, valley_shift_a=list(v1 - vn), hs_shift_v=list(h1 - hn))
        rel, tol = LS[row]
        c["current_pred"] = abs(-x["slave1_rel"] - rel) <= tol
        c["slave1_ls_zvs"] = max(x["ls_on_vds_max_v"][1]) <= 0.0
        c["slave1_valley_2p5A"] = max(x["valleys_a"][1]) <= -2.5
    c["late_fires"] = sum(x["late_fires"]) <= x["ref_late_fires"] + (6 if row.startswith("j") else 0)
    x["criteria"] = c
    return x


def main():
    res = {}
    for row in list(ROW_LIST) + list(LS):
        if not (HERE / "cosim" / f"run_{row}.json").exists():
            continue
        x = res[row] = analyse(row)
        print(f"{row}: {set(x['status'])}, overlaps {x['overlaps']}, ipk {[round(v) for v in x['ipk_a']]} A (single {x['ref']['ipk_a']:.0f}), "
              f"gaps {x['gaps_ns'][0]:.2f}-{x['gaps_ns'][1]:.2f} ns (T/16 {x['t16_ns']:.2f}), ripple {x['ripple']['rms_ac_a']:.2f} A rms, "
              f"Vo {x['vo_mean_v']:.5f}, late {x['late_fires']} (ref {x['ref_late_fires']})")
        for m in range(4):
            print(f"   module {m}: valleys " + "/".join(f"{v:+.2f}" for v in x["valleys_a"][m]) + ", HS on " + "/".join(f"{v:.2f}" for v in x["hs_on_vds_v"][m])
                  + ", LS max " + "/".join(f"{v:+.2f}" for v in x["ls_on_vds_max_v"][m]) + ", sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"][m]))
        r = x["ref"]
        print("   single:   valleys " + "/".join(f"{v:+.2f}" for v in r["valleys_a"]) + ", HS on " + "/".join(f"{v:.2f}" for v in r["hs_on_vds_v"])
              + ", LS max " + "/".join(f"{v:+.2f}" for v in r["ls_on_vds_max_v"]) + ", sd " + "/".join(f"{v:.2f}" for v in r["off_sd_a"]))
        if "step" in x:
            s, rs = x["step"], x["ref_step"]
            print(f"   step {s['extreme_mv']:+.2f} mV at {s['t_extreme_us']:.2f} us, back {s['back_within_1pct_us']:.2f} us, ladder peak {s['ladder_dev_peak']:.4f} "
                  f"(single {rs['extreme_mv']:+.2f} / {rs['t_extreme_us']:.2f} / {rs['back_within_1pct_us']:.2f} / {rs['ladder_dev_peak']:.4f})")
        if "currents_a" in x:
            print("   currents " + "/".join(f"{v:.1f}" for v in x["currents_a"]) + f" A; slave 1 {x['slave1_rel'] * 100:+.2f}% of the nominal slaves; valley shift "
                  + "/".join(f"{v:+.2f}" for v in x["valley_shift_a"]) + " A; HS shift " + "/".join(f"{v:+.2f}" for v in x["hs_shift_v"]) + " V")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in x["criteria"].items()))
    (HERE / "c05_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print(f"\n{len(res)} rows; wrote c05_summary.json")


if __name__ == "__main__":
    main()
