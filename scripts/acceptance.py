"""Acceptance gate over the experiments' registered criteria (the 2026-10-03 review: an analysis script that runs is
not an experiment that passes).

    python3 scripts/acceptance.py [--reanalyse] [EXPERIMENT ...]      # default: every experiment below

For each experiment:
- MISSING: a configuration in its cosim/ folder whose run output is absent, or a run absent from the analysis
  summary (the summary is older than the runs: --reanalyse regenerates it with the experiment's own script);
- each registered criterion in the summary is PASS, DOCUMENTED (false, and listed below with the RESULTS section that
  explains it: a known exception or a prediction that missed) or FAIL (false and not listed);
- a listed exception whose criterion now passes is reported as OUTDATED (the list needs updating).
Exit 1 on any FAIL, MISSING or OUTDATED; 0 otherwise. The exceptions are the record of what each RESULTS says missed;
adding one means writing its explanation into that RESULTS first.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
TC = PROJECT / "experiments" / "track_C_multi_module"

EXPERIMENTS = {   # name: (folder, analysis script, summary)
    "C01": (TC / "C01_four_modules_baseline", "c01_analyze.py", "c01_summary.json"),
    "C02": (TC / "C02_uniform_interleave", "c02_analyze.py", "c02_summary.json"),
    "C03": (TC / "C03_four_module_standard_matrix", "c03_analyze.py", "c03_summary.json"),
    "C04": (TC / "C04_module_spread", "c04_analyze.py", "c04_summary.json"),
    "A108": (TA / "A108_p24_line_slew_tolerance", "a108_analyze.py", "a108_summary.json"),
    "A109": (TA / "A109_p24_slot_valley_trim", "a109_analyze.py", "a109_summary.json"),
    "A110": (TA / "A110_p24_high_side_zvs", "a110_analyze.py", "a110_summary.json"),
    "A111": (TA / "A111_p24_zero_voltage_valley", "a111_analyze.py", "a111_summary.json"),
    "A112": (TA / "A112_p24_zvs_designs_matrix", "a112_analyze.py", "a112_summary.json"),
    "A113": (TA / "A113_p24_zvs_turn_off_following", "a113_analyze.py", "a113_summary.json"),
    "A114": (TA / "A114_p24_zvs_comparator_matrix", "a114_analyze.py", "a114_summary.json"),
    "A115": (TA / "A115_p24_one_mhz_design_point", "a115_analyze.py", "a115_summary.json"),
    "A116": (TA / "A116_p24_one_mhz_transients", "a116_analyze.py", "a116_summary.json"),
    "A117": (TA / "A117_p24_one_mhz_line_slew_cs", "a117_analyze.py", "a117_summary.json"),
    "A118": (TA / "A118_p24_floor_turn_off", "a118_analyze.py", "a118_summary.json"),
    "A119": (TA / "A119_p24_one_mhz_candidate_matrix", "a119_analyze.py", "a119_summary.json"),
    "A123": (TA / "A123_p24_candidate_last_amps", "a123_analyze.py", "a123_summary.json"),
    "A124": (TA / "A124_p24_two_point_five_mhz", "a124_analyze.py", "a124_summary.json"),
}

LATE_C03 = "late fires: slave 1 by C02's reference latency, phase 1 with slot_lo in line steps; bounded (RESULTS 0.3)"
EXCEPTIONS = {    # experiment: {(row, criterion): why, where}
    "C01": {("m4_L5", "sharing_d61"): "the registered metric reads 2% high; normalised within 2.3 A (RESULTS 1)"},
    "C02": {("part_b/m4_n0", "ripple_pred"): "window pk-pk includes the Ton limit cycle; per period 31.0 A as predicted (RESULTS 0.3)",
            ("part_b/m4_j30", "late_fires_not_more"): "reference latency while the master learns, each < 0.2 ns (RESULTS 3)"},
    "C03": {**{(r, "sd_band"): "jitter-free sd only measures the Ton limit cycle; ill-posed (RESULTS 0.3)"
               for r in ("m1n", "m1p", "m3n", "m3p")},
            **{(r, "ls_on_ref_0p3V"): "phase-by-phase maxima are extreme-value noise; overall maxima agree (RESULTS 0.3)"
               for r in ("j30", "j100")},
            **{(r, "late_fires"): LATE_C03
               for r in ("m1n", "m3n", "m3p", "j100", "l_m48_1us", "l_p48_1us", "l_p48_10us", "l_m80_10us", "ls_p10")},
            ("l_p48_1us", "peak_200a"): "207 A, registered as expected: phase 1's rail takes the step (BOUNDARY 3.1, A108)"},
    "C04": {("cs20_n0", "valleys_0p3A"): "0.35 A against 0.3 A, marginal (RESULTS 2)",
            ("r30_n0", "currents_0p5pct"): "R shifts sharing +/-1.3%: slaves act as ~3.3 mOhm sources (RESULTS 0.3)",
            ("r30_n0", "valleys_0p3A"): "the same mechanism moves the valleys +/-2.2 A (RESULTS 0.3)"},
    "A108": {("criteria_p", "peak_monotone"): "run peaks tie at the start-up's 170.2 A (RESULTS 2)",
             ("criteria_p", "valley_min_monotone"): "phases 3-4 deepen at slower rising slews, the harmless side (RESULTS 2)",
             ("criteria_p", "vo_monotone"): "5 us 3.51 vs 10 us 4.07 mV (RESULTS 2)",
             ("criteria_p", "valley_5us_le_10"): "+12.0 A against <= +10 A (RESULTS 2)",
             ("criteria_m", "valley_max_monotone"): "the ladder-lag mechanism grows with the ramp's duration (RESULTS 2, erratum)"},
    "A109": {(r, c): "the hypothesis is falsified: slot timing has no authority over the valleys (RESULTS 0-2)"
             for r, c in (("s1_n0", "slotted_valleys_0p3A"), ("s1_n0", "hs_on_0p15V"), ("s1_n0", "ofs_64"),
                          ("s1_j30", "sd_band"), ("m4_n0", "slotted_valleys_0p3A"), ("m4_n0", "ofs_64"),
                          ("m4_n0", "gaps_2ns"), ("m4_ls_p10", "slave1_valleys_0p3A"),
                          ("m4_ls_p10", "slave1_current_d61"), ("s1_m48_1us", "slotted_max_le_25A"),
                          ("s1_m48_10us", "valleys_le_m2A"), ("s1_m48_50us", "valleys_le_m2A"),
                          ("s1_p48_1us", "phase1_unchanged"), ("s1_p48_1us", "slotted_min_ge_m15A"),
                          ("s1_p48_10us", "slotted_min_ge_m15A"), ("m4_l_m48_10us", "all_valleys_negative"))},
    "A110": {**{(r, "ton_4pct"): "the registered Ton relation ignores the transitions; the period is within 4% (RESULTS 1)"
                for r in ("n10", "n15", "n20", "n25", "n30")},
             ("n20", "hs_d57_0p6V"): "phase 4 at 2.26 V, 0.63 V from D57 (RESULTS 1)",
             ("n25", "hs_d57_0p6V"): "phase 4 reached zero voltage (-0.16 V) before the others (RESULTS 1)",
             ("n25", "peak_200a"): "204 A after the handover at 77 us (RESULTS 1)",
             **{(r, c): "at 30% the valley-based turn-on timing breaks down once the node clamps (RESULTS 0.2; A111)"
                for r, c in (("n30", "peak_200a"), ("n30", "ls_zvs"), ("n30", "peak_5A"), ("n30", "hs_zvs_0p3V"),
                             ("n30_s_p62", "peak_200a"), ("n30_s_m62", "peak_200a"), ("n30_s_m62", "step_25pct"),
                             ("n30_j30", "peak_200a"), ("n30_j30", "sd_band"), ("n30_j30", "hs_zvs_0p5V"))}},
    "A111": {**{(r, "identical"): "the handover transient reaches V_DS <= 0 at 5% and 20% too; steady states agree (RESULTS 0.2)"
                for r in ("z5", "z20")},
             **{(r, c): "the zero-arrival valley destabilises 25-30%: falsified (RESULTS 0.1)"
                for r, c in (("z25", "peak_200a"), ("z25", "hs_mean_0p9V"), ("z30", "peak_200a"), ("z30", "hs_mean_0p3V"),
                             ("z30", "hs_max_1V"), ("z30", "ls_zvs"), ("z30", "sd_0p5A"), ("z30", "late_5"),
                             ("z30", "eff_ge_a110"), ("z30", "eff_pred"), ("z30_s_p62", "peak_200a"),
                             ("z30_s_p62", "step_25pct"), ("z30_s_p62", "back_15us"), ("z30_s_m62", "peak_200a"),
                             ("z30_s_m62", "step_25pct"), ("z30_s_m62", "back_15us"), ("z30_j30", "peak_200a"),
                             ("z30_j30", "sd_band"), ("z30_j30", "hs_0p5V"))}},
    "A112": {**{(r, "run_peak_200a"): "20% line-step peaks at the 200 A limit, 201-204 A (RESULTS 0.2)"
                for r in ("p20_l_m48_1us", "p20_l_p48_1us", "p20_l_p48_10us")},
             **{(r, "line_peak_pred"): "the +17 / +24 A shift predicted the 1 us peaks too high, the 10 us ones too low (RESULTS 1)"
                for r in ("p20_l_p48_1us", "p20_l_p48_10us", "p25_l_p48_1us", "p25_l_p48_10us")},
             **{(r, "step_30pct"): "line-step Vo extremes change sign or grow with a large negative current (RESULTS 1)"
                for r in ("p20_l_m48_1us", "p20_l_m80_10us", "p20_l_p48_1us", "p20_l_p48_10us", "p25_l_m48_1us",
                          "p25_l_m48_10us", "p25_l_m80_10us", "p25_l_p48_1us", "p25_l_p48_10us")},
             ("p25_s_m62", "step_30pct"): "25%: phase 1's turn-off does not follow Ton; a slow oscillation (RESULTS 0.3; A113)"},
    "A113": {("ff_s_m62", "overshoot_30pct"): "+16.9 mV against +11.65 mV, recovered in 8.9 us (RESULTS 0.3)",
             ("cmp_s_m62", "overshoot_30pct"): "+16.9 mV against +11.65 mV, recovered in 8.9 us (RESULTS 0.3)",
             ("ff_l_m48_1us", "back"): "the dlo feed-forward is falsified for line steps (RESULTS 0.1)",
             ("ff_l_m48_1us", "peak_le_a112"): "the dlo feed-forward is falsified for line steps (RESULTS 0.1)",
             ("ff_l_m80_10us", "back"): "the dlo feed-forward is falsified for line steps (RESULTS 0.1)",
             ("ff_l_m80_10us", "peak_le_a112"): "the dlo feed-forward is falsified for line steps (RESULTS 0.1)",
             ("cmp_l_m80_10us", "back"): "-8 V / 10 us still settles in 175 us: another mechanism (RESULTS 0.2)",
             ("cmp_l_m80_10us", "peak_le_a112"): "197.9 against 193.6 A (RESULTS 1)"},
    "A114": {**{(r, "sd_bound"): "the comparator's timing noise at 30 ps, x1.4 against x1.3 (RESULTS 0.4)" for r in ("c20_j30", "c25_j30")},
             ("c20_l_m80_10us", "slow_as_registered"): "registered slow, it is fast at 20% (RESULTS 0.5)",
             **{(r, c): "rising line steps run away with the comparator: phase 1 stretches, the slots follow (RESULTS 0.3)"
                for r, c in (("c20_l_p48_10us", "back_20us"), ("c20_l_p48_10us", "peak_a112_5A"), ("c20_l_p48_1us", "peak_a112_5A"),
                             ("c25_l_p48_10us", "back_20us"), ("c25_l_p48_10us", "peak_a112_5A"), ("c25_l_p48_1us", "peak_a112_5A"))}},
    "A115": {**{(r, "step_30pct"): "D59 over-predicts the load-step extreme by ~30% at 1 MHz; the measured dip is smaller (RESULTS 1)"
                for r in ("n5_s_p62", "n10_s_p62")},
             **{("n10_s_m62", c): "the load decrease runs away: phase 1's timed turn-off lags Ton, the 60 kHz loop is ~3x "
                "faster per period than at 5 MHz (RESULTS 0.3, 3.1)" for c in ("peak_200a", "step_30pct", "back_60us")}},
    "A116": {**{(r, "extreme_band"): "the bands scaled D59 by A115's timed 0.7; with the comparator D59 is exact, within 4% "
                "(RESULTS 0.3)" for r in ("c60_s_m62", "c30_s_m62", "c60_s_p62", "c30_s_p62")},
             ("t30_s_m62", "extreme_band"): "H1: the valleys still pass the threshold (-54 A); a slow oscillation, a dip "
                                            "(RESULTS 0.1)",
             ("t30_s_m62", "back_60us"): "H1: 200 us, as A112's 25% at 5 MHz (RESULTS 0.1)",
             **{(r, c): "1 MHz line steps over 1 us: the ladder lags (Cs x5) and the slotted valleys pass the threshold "
                "(RESULTS 0.4)" for r, c in (("t60_l_m48_1us", "peak_200a"), ("t60_l_m48_1us", "back_60us"),
                                             ("t30_l_m48_1us", "peak_200a"), ("c60_l_m48_1us", "peak_200a"),
                                             ("c30_l_m48_1us", "peak_200a"), ("c30_l_m48_1us", "back_60us"))},
             ("t30_l_m48_1us", "back_60us"): "at 43.2 V the margin is 0.95 A: the timed design's +-18 mV limit cycle "
                                             "(RESULTS 0.5)"},
    "A117": {**{(r, "outcome_as_d63"): "D63's registered outcome rule is falsified (8 A too low; class edges at 60 us / "
                "200 A); its peaks hold (RESULTS 0.1)" for r in ("c3_cmp_l_m48_1us", "c3_tim_l_m48_10us", "c15_tim_l_m48_50us",
                                                                 "c15_cmp_l_p48_20us", "c15_cmp_l_p48_50us", "c15_cmp_l_m48_5us")},
             ("c3_cmp_s_m62", "extreme_10pct"): "+25.4 against +28.9 mV (-12%) (RESULTS 1)",
             **{(r, "peak_200a"): "the 3 uF handover oscillates ~1.1 ms to 517 A (RESULTS 0.2)" for r in ("c3_tim_n0", "c3_cmp_n0")},
             **{(r, "hs_up_0p5_1p5V"): "the in-cycle Cs ripple moves phases 1/4 +1.1 V and phases 2/3 -0.8 V (RESULTS 0.2)"
                for r in ("c3_tim_n0", "c3_cmp_n0")}},
    "A118": {**{(r, "back_30us"): "the floor's load-decrease recovery is slower than D63's (31.8 / 46.8 against 17.6 us) (RESULTS 0.1)"
                for r in ("f6_s_m62", "f15_s_m62")},
             ("f15_l_m48_5us", "peak_10pct_d63"): "211 against D63's 187 A (+13%) at 15 uF (RESULTS 0.4)"},
    "A119": {("j30", "sd_0.16A"): "0.17 against 0.16 A (RESULTS 0.1)",
             ("l_m80_10us", "peak_200a"): "205 A on the step to 40 V; no limit cycle (RESULTS 0.1, 0.2)"},
    "A123": {(f"{v}_closes", "closes_all_le_200a"): "no single lever closes all three steps; each moves 1-11 A (RESULTS 0)"
             for v in ("c45", "f3", "k66")},
    "A124": {**{(r, "floor_holds"): "registration error: the front end's 11 ns delay overshoots ~3.75 A at 2.5 MHz, not 1 A "
                "(RESULTS 0.4)" for r in ("p125_s_m62", "p125_l_m48_5us", "p125_l_m80_10us", "p125_l_p48_5us")},
             ("p125_l_p48_5us", "peak_200a"): "210 A: the rising-step limit common to every frequency (RESULTS 0.3)"},
}


def criteria_sets(d, prefix=""):
    """(row, {criterion: bool}) for every criteria block of a summary."""
    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        if isinstance(v.get("criteria"), dict):
            yield prefix + k, v["criteria"]
        elif k.startswith("criteria"):
            yield prefix + k, v
        elif k in ("part_a", "part_b"):
            yield from criteria_sets(v, prefix + k + "/")


def summary_rows(d):
    rows = set()
    for k, v in d.items():
        if k in ("part_a", "part_b") and isinstance(v, dict):
            rows |= set(v)
        elif not k.startswith("criteria"):
            rows.add(k)
    return rows


def check(name, reanalyse):
    folder, script, summary = EXPERIMENTS[name]
    out = {"MISSING": [], "FAIL": [], "DOCUMENTED": [], "OUTDATED": [], "PASS": 0}
    runs = []
    for cfg in sorted((folder / "cosim").glob("cfg_*.json")):
        run = folder / "cosim" / json.loads(cfg.read_text())["out"]
        runs.append(run.stem[4:])
        if not run.exists():
            out["MISSING"].append(f"run {run.name}")
    if reanalyse:
        r = subprocess.run([sys.executable, str(folder / script)], cwd=PROJECT, capture_output=True, text=True)
        if r.returncode:
            out["FAIL"].append(f"analysis script exited {r.returncode}: {r.stderr.strip()[-300:]}")
    path = folder / summary
    if not path.exists():
        out["MISSING"].append(f"summary {summary}")
        return out
    d = json.loads(path.read_text())
    have = summary_rows(d)
    out["MISSING"] += [f"row {r} not in {summary}" for r in runs if r not in have]
    exc = EXCEPTIONS.get(name, {})
    seen = set()
    for row, crit in criteria_sets(d):
        for c, ok in crit.items():
            key = (row, c)
            if ok:
                out["PASS"] += 1
                if key in exc:
                    out["OUTDATED"].append(f"{row}: {c} passes but is listed as an exception")
            elif key in exc:
                out["DOCUMENTED"].append(f"{row}: {c} - {exc[key]}")
            else:
                out["FAIL"].append(f"{row}: {c}")
            seen.add(key)
    out["OUTDATED"] += [f"{r}: {c} listed but not in the summary" for r, c in exc if (r, c) not in seen]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("experiments", nargs="*", default=list(EXPERIMENTS))
    ap.add_argument("--reanalyse", action="store_true")
    a = ap.parse_args(argv)
    bad = False
    for name in a.experiments:
        r = check(name, a.reanalyse)
        verdict = "FAIL" if (r["FAIL"] or r["MISSING"] or r["OUTDATED"]) else "ACCEPTED"
        bad |= verdict == "FAIL"
        print(f"{name}: {verdict} - {r['PASS']} pass, {len(r['DOCUMENTED'])} documented, {len(r['FAIL'])} fail, "
              f"{len(r['MISSING'])} missing, {len(r['OUTDATED'])} outdated")
        for k in ("FAIL", "MISSING", "OUTDATED", "DOCUMENTED"):
            for line in r[k]:
                print(f"   {k:10s} {line}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
