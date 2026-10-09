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
import re
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
    "C05": (TC / "C05_four_module_final_design", "c05_analyze.py", "c05_summary.json"),
    "C06": (TC / "C06_slave_floor", "c06_analyze.py", "c06_summary.json"),
    "C07": (TC / "C07_module_spread_final", "c07_analyze.py", "c07_summary.json"),
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
    "A132": (TA / "A132_p24_neg_current_autotune", "a132_analyze.py", "a132_summary.json"),
    "A133": (TA / "A133_p24_inductance_tolerance", "a133_analyze.py", "a133_summary.json"),
    "A134": (TA / "A134_p24_inductance_cap_lock", "a134_analyze.py", "a134_summary.json"),
    "A135": (TA / "A135_p24_relative_cap", "a135_analyze.py", "a135_summary.json"),
    "A136": (TA / "A136_p24_relative_cap_lowpass", "a136_analyze.py", "a136_summary.json"),
    "A137": (TA / "A137_p24_vff_restart_at_handover", "a137_analyze.py", "a137_summary.json"),
    "A141": (TA / "A141_p24_floor_late_report", "a141_analyze.py", "a141_summary.json"),
    "A143": (TA / "A143_p24_short_comparator_phase", "a143_analyze.py", "a143_summary.json"),
    "C08": (TC / "C08_relative_cap_four_modules", "c08_analyze.py", "c08_summary.json"),
    "C09": (TC / "C09_seed_four_modules", "c09_analyze.py", "c09_summary.json"),
    "C10": (TC / "C10_seed_before_entry", "c10_analyze.py", "c10_summary.json"),
    "C11": (TC / "C11_seed2_inductance", "c11_analyze.py", "c11_summary.json"),
    "C12": (TC / "C12_floor_late_four_modules", "c12_analyze.py", "c12_summary.json"),
    "A142": (TA / "A142_p24_random_stimulus", "a142_analyze.py", "a142_summary.json"),
    "C13": (TC / "C13_random_stimulus_four_modules", "c13_analyze.py", "c13_summary.json"),
    "C14": (TC / "C14_sharing_spread_check", "c14_analyze.py", "c14_summary.json"),
    "A144": (TA / "A144_p24_commutation_loop_inductance", "a144_analyze.py", "a144_summary.json"),
    "A145": (TA / "A145_p24_finite_switching_edges", "a145_analyze.py", "a145_summary.json"),
    "A151": (TA / "A151_p24_slow_hard_turn_on", "a151_analyze.py", "a151_summary.json"),
    "A152": (TA / "A152_p24_drive_spec_robustness", "a152_analyze.py", "a152_summary.json"),
    "A153": (TA / "A153_p24_slow_turn_on_laws", "a153_analyze.py", "a153_summary.json"),
    "A154": (TA / "A154_p24_turn_off_large_loops", "a154_analyze.py", "a154_summary.json"),
    "A155": (TA / "A155_p24_startup_ton_law", "a155_analyze.py", "a155_summary.json"),
    "A156": (TA / "A156_p24_formula_spec_at_the_limit", "a156_analyze.py", "a156_summary.json"),
    "A157": (TA / "A157_p24_loop_damping", "a157_analyze.py", "a157_summary.json"),
    "A158": (TA / "A158_p24_damping_boundary", "a158_analyze.py", "a158_summary.json"),
    "A159": (TA / "A159_p24_spec_at_150ph", "a159_analyze.py", "a159_summary.json"),
    "A161": (TA / "A161_p24_150ph_faster_turn_on", "a161_analyze.py", "a161_summary.json"),
    "A162": (TA / "A162_p24_late_fire_timing", "a162_analyze.py", "a162_summary.json"),
    "A163": (TA / "A163_p24_gate_driven_edges", "a163_analyze.py", "a163_summary.json"),
    "A164": (TA / "A164_p24_gate_drive_spread", "a164_analyze.py", "a164_summary.json"),
    "A165": (TA / "A165_p24_gate_lead_pulse", "a165_analyze.py", "a165_summary.json"),
    "A166": (TA / "A166_p24_gate_lead_per_board", "a166_analyze.py", "a166_summary.json"),
    "A167": (TA / "A167_p24_gate_lead_ramp", "a167_analyze.py", "a167_summary.json"),
    "A168": (TA / "A168_p24_gate_loop_bound", "a168_analyze.py", "a168_summary.json"),
    "A169": (TA / "A169_p24_gate_low_sides", "a169_analyze.py", "a169_summary.json"),
    "A170": (TA / "A170_p24_gate_interlock", "a170_analyze.py", "a170_summary.json"),
    "A171": (TA / "A171_p24_gate_interlock_threshold", "a171_analyze.py", "a171_summary.json"),
    "A172": (TA / "A172_p24_final_gate_plant", "a172_analyze.py", "a172_summary.json"),
    "A173": (TA / "A173_p24_final_plant_coverage", "a173_analyze.py", "a173_summary.json"),
    "A174": (TA / "A174_p24_final_plant_margins", "a174_analyze.py", "a174_summary.json"),
    "A175": (TA / "A175_p24_final_plant_a152_matrix", "a175_analyze.py", "a175_summary.json"),
    "A177": (TA / "A177_p24_per_board_interlock_reference", "a177_analyze.py", "a177_summary.json"),
    "A178": (TA / "A178_p24_inductance_tolerance_final", "a178_analyze.py", "a178_summary.json"),
    "A179": (TA / "A179_p24_interlock_release_threshold", "a179_analyze.py", "a179_summary.json"),
    "A181": (TA / "A181_p24_locked_trim_joint_corner", "a181_analyze.py", "a181_summary.json"),
    "A183": (TA / "A183_p24_startup_period_ladder", "a183_analyze.py", "a183_summary.json"),
    "A184": (TA / "A184_p24_startup_own_ton", "a184_analyze.py", "a184_summary.json"),
    "A185": (TA / "A185_p24_bumpless_loop_seed", "a185_analyze.py", "a185_summary.json"),
    "A186": (TA / "A186_p24_vo_triggered_handover", "a186_analyze.py", "a186_summary.json"),
    "A187": (TA / "A187_p24_slow_corner_inductance_hot", "a187_analyze.py", "a187_summary.json"),
    "A188": (TA / "A188_p24_handover_request_level", "a188_analyze.py", "a188_summary.json"),
}
ROW_PREFIX = {"A137": "s"}                # run file stem -> summary row: the run name carries this leading letter
NOT_ROWS = {                              # runs the summary does not list as rows (checked another way)
    "C09": r"c06al9_",                    # contingency rerun, read by the post-step comparison
    "C10": r"s\d+_|c06al10_|c10al6_",     # single-module records (identity criteria S_*) and the trace reruns
    "A141": r"I\d_",                     # identity replays, read by criterion 1
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
    "C05": {**{(r, c): "slave phase-1 valley runaway after the handover, the finding; fixed in C06 (RESULTS 0, 0b)"
               for r, cs in (("m1n", ("peak_200a", "late_fires")), ("m3n", ("peak_200a", "late_fires", "sd_band")),
                             ("j100", ("peak_200a", "late_fires", "sd_band", "no_overlap", "locked", "valleys_0p5A",
                                       "hs_on_0p2V", "ls_on_ref_0p3V"))) for c in cs},
            ("j30", "ls_on_ref_0p3V"): "one phase's LS turn-on V_DS above single + 0.3 V; module maxima agree (RESULTS 0)",
            **{(r, "late_fires"): "1 late fire in a line step where the single module has 0 (RESULTS 0)"
               for r in ("l_p48_1us", "l_p48_5us", "l_m48_1us", "l_m80_10us")},
            ("l_p48_5us", "step_10pct"): "Vo extreme 12.04 vs 10.85 mV, +11% (RESULTS 0)",
            ("l_m80_10us", "step_10pct"): "Vo extreme sign flip, equal magnitude (RESULTS 0)"},
    "C06": {**{(r, "late_fires"): "late fires in the post-handover transient only (all before 260 us); adopted with "
               "this residual (RESULTS 0, 0b)" for r in ("m1n", "m3n")},
            **{(r, "late_fires"): "1-2 late fires in a line step where the single module has 0 (RESULTS 1)"
               for r in ("l_p48_1us", "l_p48_5us", "l_m48_1us", "l_m80_10us")},
            **{(r, "ls_on_ref_0p3V"): "phase-by-phase maxima; module maxima at the single module's (RESULTS 1)"
               for r in ("j30", "j100")},
            ("l_p48_5us", "step_10pct"): "Vo extreme sign flip, equal magnitude (RESULTS 1)",
            ("l_m80_10us", "step_10pct"): "Vo extreme sign flip, equal magnitude (RESULTS 1)",
            ("l_m48_1us", "step_10pct"): "+17.9 vs +15.7 mV: the floor fired in the step (RESULTS 0)",
            ("l_m48_1us", "back_2us"): "11.1 vs 5.9 us: the floor fired in the step (RESULTS 0)"},
    "C07": {("cs20_n0", "currents_0p5pct"): "251.3 A = +0.52% against 0.5% (RESULTS 1)",
            ("cs20_n0", "valleys_0p35A"): "0.48 A against 0.35 A (RESULTS 1)",
            **{(r, "join"): "106-118 uV against 100 uV; C06 n0 83 uV (RESULTS 1)"
               for r in ("r30_n0", "all_n0", "all_s_p62", "r30_n0_nf", "all_n0_nf")},
            ("all_n0", "floor_inactive_steady"): "0.0526 A against 0.05 A, valley gap 0.011 ns ok (RESULTS 1)",
            **{(r, "peak_200a"): "control with slave_floor 0: 263-265 A, the finding that the floor is needed (RESULTS 0)"
               for r in ("r30_n0_nf", "all_n0_nf")}},
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


def _ex(rows, crit, why):
    return {(r, crit): why for r in rows}


_STEP_FREE = ("n0", "m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25", "s_m62", "s_p62", "l_p48_1us", "l_p48_5us",
              "l_m48_1us", "l_m48_5us", "l_m80_10us", "ls_p5", "ls_p10")
_ROW = lambda rows: [f"rows/{r}" for r in rows]
_ADC = "m3n's end-window sd is the voltage loop's ADC limit cycle (one code = 5.69 Ton LSB, Vo at a +-0.25 mV level; C09 RESULTS 0)"
_JIT = "phase-by-phase maxima; module maxima at the single module's (C06 RESULTS 1)"
EXCEPTIONS.update({   # A132-A137, C08-C10 (2026-10-05): each reason is the one the experiment's RESULTS gives
    "A132": {("criteria", k): "A132 not adopted: the depth loop misses at the L / C corners (c1.3_l0.7 start-up peaks, c0.7_l1.3 "
                             "never quasi-steady, late fires > 100) and re-tunes the line-step operating point (RESULTS 0, 1)"
             for k in ("2_convergence", "3_valley_kept", "4_matrix_on", "5_step_rows_on", "6_inert_nominal")},
    "A133": {("criteria", k): "L x 0.7-1.3 corners fail as registered; the 'limit cycle' read here is the absolute cap's lock "
                              "(A134), A133's floor on phases 2-4 invalid (RESULTS 0, 1)"
             for k in ("3_nominal_disturbances", "4_l13_balanced", "5_other_corners_balanced", "6_corners", "7_c07l13")},
    "A134": {("criteria", "1_mechanism"): "fails as registered on the threshold (s_p62 1.04-1.22 % vs 1 %, L0's own 0.93 %); passes "
                                          "post hoc at +0.5 points (RESULTS 1 row 1)",
             **{("criteria", f"3_tolerance/{m}/{k}"): "absolute cap: functional L x 0.7-1.0, 200 A spec only at L0, cap-bound at "
                "1.05 and locked above; the L x 1.2 / 1.3 arms are partial (RESULTS 0, 1 row 3)"
                for m, ks in {"0.7": ("spec", "spec_ph"), "0.85": ("spec", "spec_ph"), "0.9": ("spec", "spec_ph"),
                              "1.05": ("func", "spec", "func_ph", "spec_ph"), "1.1": ("func", "spec", "func_ph", "spec_ph"),
                              "1.2": ("complete", "func", "spec", "func_ph", "spec_ph"),
                              "1.3": ("complete", "func", "spec", "func_ph", "spec_ph")}.items() for k in ks}},
    "A135": {("criteria", "2_l0_unchanged"): "relative cap on ton follows the loop's transient rise: rising rows +20 A (RESULTS 1 row 2)",
             ("criteria", "4_peaks"): "rising rows 201-212 A: A135 not adopted (RESULTS 1 row 4)"},
    "A136": {("criteria", "3c_peaks"): "A124 rows pass (<= 189 A); the matrix's m3n misses on start-up late fires (RESULTS 1 row 3c)"},
    "A137": {("criteria", "2_handover"): "fails at L x 0.7 only, where the handover is mode S's fixed Ton; adopted by user "
                                         "decision 2026-10-04 (RESULTS 0)"},
    "C08": {**_ex(_ROW(_STEP_FREE), "late_fires", "handover late fires from A136's start-up regression, equal across rows (RESULTS 0)"),
            ("rows/m3n", "sd_band"): "m3n end-window sd 0.11-0.12 A (RESULTS 0); traced to the ADC limit cycle in C09 (RESULTS 0)",
            **_ex(("rows/j30", "rows/j100"), "ls_on_ref_0p3V", _JIT),
            **_ex(("rows/s_m25", "rows/l_m48_1us"), "step_10pct", "s_m25: step offset +7.3 A (C09 RESULTS 0); l_m48_1us: C06's residual (C06 RESULTS 0)"),
            ("rows/s_m25", "c06_within_7a"): "+7.3 A is the step's offset: C06's design at that offset gives 152.7 A (C09 RESULTS 0)",
            ("rows/l_m48_1us", "back_2us"): "C06's residual: the floor fired in the step (C06 RESULTS 0)",
            ("criteria", "1_no_new_fail"): "late fires, m3n sd, s_m25 (RESULTS 0, 1 row 1)",
            ("criteria", "2_c06_within_7a"): "s_m25 +7.3 A, the step offset (RESULTS 1 row 2; C09 RESULTS 0)"},
    "C09": {**_ex(_ROW([r for r in _STEP_FREE if r != "m3p"]), "late_fires", "slaves seed after the master's first ADC sample: handover lock, not adopted (RESULTS 0)"),
            **_ex(_ROW([r for r in _STEP_FREE if r not in ("m1p", "m3p")]), "late_c06", "handover lock: late fires above 1.5 x C06 + 6 (RESULTS 1 row 2)"),
            **_ex(("rows/m1n", "rows/m3n"), "peak_200a", "handover lock: whole-run peaks 201.8 / 203.5 A (RESULTS 0, 1 row 1)"),
            ("rows/m3n", "sd_band"): _ADC,
            **_ex(("rows/j30", "rows/j100"), "ls_on_ref_0p3V", _JIT),
            ("rows/l_p48_5us", "c06_within_7a"): "one period on slave 1's phase 1: 184.6 A, not traced (RESULTS 0, 1 row 3)",
            **_ex(("rows/l_m48_1us", "rows/l_m80_10us"), "step_10pct", "C06's residuals (C06 RESULTS 0, 1)"),
            **{("criteria", k): "C09 not adopted: the restart fixes the master only (RESULTS 0, 1)"
               for k in ("1_hard", "1_no_new_fail", "2_late_c06", "3_c06_within_7a")}},
    "C10": {**_ex(_ROW(("m1n", "m3n", "l_p48_1us", "l_p48_5us")), "late_fires", "handover and line-step late fires, 25 / 90 vs C06's 19 / 68 "
                  "and 1-2 in line steps (RESULTS 0; C06 RESULTS 1)"),
            ("rows/s_m62", "late_fires"): "one late fire after the step (slave 3, phase 4); 0 in C06 at C10's offset and in C10 at C06's: "
                                          "adopted by user decision 2026-10-05 (RESULTS 0)",
            ("rows/m3n", "sd_band"): _ADC,
            **_ex(("rows/j30", "rows/j100"), "ls_on_ref_0p3V", _JIT),
            ("rows/l_m48_1us", "step_10pct"): "C06's residual (+17.9 vs +15.7 mV, C06 RESULTS 0)",
            ("criteria", "1_no_new_fail"): "s_m62's late fire; adopted by user decision 2026-10-05 (RESULTS 0, 1)"},
})
NOT_ROWS["A134"] = ".*"     # its summary is per arm (f / z / c) and L, not per run
NOT_ROWS.update({
    "A142": r"I0$|P\d|Q_|R_",            # identity replay (criterion 5) and the post hoc traces (RESULTS 3)
    "C13": r"s1_",                        # single-module replays of three draws (RESULTS 2)
    "A151": r"s5_",                       # 5 us bus-slew rows, read by the summary's slew5
    "A152": r"m4_",                       # four-module rows, read by criterion 5
})
_PKG = "a hard turn-on of phase k-1 rings SH_k to 24 + 1.7 dV at every L; solved by the drive in A151 / A152 (RESULTS 0, 1 row 2)"
EXCEPTIONS.update({   # A142, C13, C14, A144, A145, A151, A152 (added 2026-10-06 when the package line closed)
    "A142": {("criteria", "3_new_0"): "z104: 27 spikes and 8 order events, the mode-P comparator-phase oscillation this test "
                                      "found; fixed by A143 (RESULTS 0, 1 row 3)"},
    "C13": {("criteria", "1_floor_first_0"): "y08: one floor-first duplicate, a 0.36 LSB rounding tie (oracle class K5), "
                                             "peak normal (RESULTS 0, 1 row 1, 2)"},
    "C14": {("criteria", "w10/all_rows_le_200"): "+-10 % worst case reaches 207.9 A: the 200 A crossing is near +-7 %, the "
                                                 "spread limit this experiment measures (RESULTS 0, 1 row 5)"},
    "A144": {("criteria", f"per_l/{l}/voltage"): _PKG for l in (50, 100, 150, 300)},
    "A145": {**{("criteria", f"2_voltage/{d}"): "V_DS > 40 V at every L with 1-2 ns edges (best 50 pH / 2 ns 41.8 V after "
                "+4.8 V / 1 us); solved by the slow turn-on in A151 (RESULTS 0, 1 row 2)" for d in ("72", "144")},
             ("criteria", "5_cost"): "wall time x1.6-2.5 vs A144 (Python edge steps under 10 parallel jobs); edge steps "
                                     "1.3 / 2.4 % pass (RESULTS 1 row 5)"},
    "A151": {("criteria", "1_harness"): "the single-edge harness underpredicts the cosim reduction at 100 / 150 pH, as "
                                        "predicted (RESULTS 1 row 1)"},
    "A152": {("criteria", "S100/c3"): "l_m80_10us: 6 late fires (ref 2), no peak, V_DS or oracle consequence (RESULTS 0, 1 row 3)",
             ("criteria", "6_300pH"): "300 pH fails at any turn-on rate: the 72 A/ns turn-off ring alone is 48.8 V steady "
                                      "(RESULTS 0, 1 row 6)"},
})
_K4T = ("the second peak of phase 1's post-step period swing, 0.09-0.16 us after the K4 window (ramp + 1 us): the slow "
        "turn-on delays it; inside the window in f300_off32 (RESULTS 0)")
EXCEPTIONS["A154"] = {
    ("criteria", "1_vds_band/f300_off24"): "35.9 against 37.6 V: 0.2 V beyond the band on the safe side (RESULTS 1 row 1)",
    ("criteria", "4_controller/f200_off48"): _K4T,
    ("criteria", "4_controller/f300_off24"): _K4T,
    ("criteria", "4_controller/f300_off48"): "control row: start-up 190 A (<= 200 A); D68's start-up ton has no L term above "
                                             "150 pH (RESULTS 0; A155)",
}
EXCEPTIONS["A156"] = {("criteria", "c3"): "late fires l_m80_10us 16 (grow with the loop: 0 / 6 / 16 at 50 / 100 / 125 pH), "
                                           "L07 rows 5, two dup_other ties at a clock-window boundary; no consequence; the "
                                           "adopted drive stays at x_on <= 1.8 V by the registered rule (RESULTS 0)"}
NOT_ROWS["A156"] = r"m4_|s125_"                  # the summary lists rows by name (run file stem s125_<row>, m4)
_UND = "undamped loop: valley tracking lost from start-up (8600-8960 late fires, 58-69 V); the spec adds ring Q <= 30 (RESULTS 0)"
EXCEPTIONS["A157"] = {("criteria", f"{c}/{r}"): _UND for c, rows in (("1_vds_band", ("q0_s50", "q0_s100", "q0_s125")),
                       ("2_vds_40", ("q0_s50", "q0_s100")), ("3_controller", ("q0_s50", "q0_s100", "q0_s125"))) for r in rows}
_K4T158 = "phase 1's post-step swing peak at 1002.05 us, 0.05 us after the oracle's K4 window (slow turn-on, as A154); 0 late fires (RESULTS 0)"
EXCEPTIONS["A158"] = {("criteria", "1_h1_q_only/q15_s100"): _K4T158, ("criteria", "1_h1_q_only/q30_s100"): _K4T158,
                      ("criteria", "2_q30_at_100ph/q30_s100"): _K4T158}
EXCEPTIONS["A159"] = {
    ("criteria", "c3"): "l_m80_10us late 33 (trend 0 / 6 / 16 / 33 at 50-150 pH) and two post-step swing peaks just after the "
                        "oracle's K4 window (RESULTS 0)",
    ("criteria", "c4"): "12 A/ns turn-on at 150 pH: load-step dip -16.1 mV (0.2 mV over), +4.8 V / 10 us back 46.2 us (1.1 us "
                        "over): the recommended loop bound comes down to 125 pH (RESULTS 0)",
    ("criteria", "c5"): "four modules: one K4-timing swing peak per module, 36.4 V, late 0 (RESULTS 0)"}
NOT_ROWS["A159"] = r"m4_|s150_"
EXCEPTIONS["A161"] = {("criteria", "c3"): "l_m80_10us late 28 (they follow the loop: 0 / 6 / 16 / 33 / 28 at 50-150 pH), 0 NEW, "
                                           "no consequence; bound 150 pH at 20 A/ns by the registered rule (RESULTS 0)"}
NOT_ROWS["A161"] = r"m4_|s150_"
_DEF163 = "physical peak against A152's command-time peak; physical vs physical -1.9..+1.8 A, command vs command lower (RESULTS 0)"
_LATE163 = "the valley-timing limit (gate delay vs dt_pred >= 0), mechanism 2 (RESULTS 0)"
EXCEPTIONS["A163"] = {
    **{("criteria", f"{r}/c3"): _DEF163 for r in ("s50_l_p48_1us", "s50_s_p62", "s50_slew10", "s50_slew3", "s50_slew5",
                                                    "s50_L07_l_p48_1us", "s50_L07_s_p62", "s50vthmin_l_p48_1us",
                                                    "s50vthmin_s_p62", "s50r07_l_p48_1us", "s50r07_s_p62", "s75_s_p62")},
    **{("criteria", f"s50_L07_{r}/c2"): "L x 0.7 start-up 215.6 A physical in mode S: the ton calibrated at L0 gives Vo 1.147 "
       "V there (A152 physical 205.6 A); the per-board trim is A164's fix (RESULTS 0)" for r in ("l_p48_1us", "s_p62")},
    ("criteria", "s50_slew4/c3"): "late 5 on phase 4: " + _LATE163 + "; peak " + _DEF163,
    ("criteria", "m4_s50_l_p48_1us/c3"): "late 38, module 4 phase 4: " + _LATE163 + "; peak " + _DEF163,
    **{("criteria", f"s75_{r}/c3"): "late fires after the line steps at 3.5 ohm: " + _LATE163
       for r in ("l_p48_1us", "l_m80_10us", "slew2")},
    ("criteria", "s50r07_l_p48_1us/c1"): "40.6 V: driver -30 % (1.75 ohm), mechanism 3 (RESULTS 0)",
    **{("criteria", f"s50cissmax_{r}/c3"): "late 179 / 44 (+3 NEW): the handover at Vo 0.980 V (mechanism 1) and the line "
       "step; C_ISS x 1.5 is outside the datasheet's Q_G max (RESULTS 0)" for r in ("l_p48_1us", "s_p62")},
    **{("criteria", f"s50vthmax_{r}/c{c}"): "threshold +1.5 V, outside the datasheet's R_DS(on) / V_GS(TH) max: start-up "
       "on-time (Vo 0.833 V, 368 A, 46.6 V) and the valley-timing limit (1407 late on phase 4), mechanisms 1-2 (RESULTS 0)"
       for r in ("l_p48_1us", "s_p62") for c in (1, 2, 3)},
}
EXCEPTIONS["A164"] = {
    ("criteria", "nom_L07_l_p48_1us/c2"): "218.6 A 2.4 us into mode P: the turn-on-only lead widens every mode-P pulse by 8 ns "
    "(an on-time step at the handover); mode S itself 202.5 A, the frozen design's open-loop start at L x 0.7 (RESULTS 0)",
    ("criteria", "ff_l_m80_10us/c4"): "Vo +28.5 mV against 27.9 allowed (nominal -20.9 mV) (RESULTS 0)",
    **{("criteria", f"ss_{r}/c3"): "slow corner: late fires in the handover (65) and after rising line steps (~160), NEW spikes "
       "10-13 A after the steps, no peak or V_DS consequence (RESULTS 0)" for r in ("l_p48_1us", "s_p62", "l_m80_10us", "slew4")},
    ("criteria", "nom_lead0_l_p48_1us/c3"): "control without the lead: 48 late fires after +4.8 V / 1 us, the reason for "
    "the lead (RESULTS 0)",
}
EXCEPTIONS["A165"] = {
    ("criteria", "nom_L07_l_p48_1us/c2"): "mode S 202.5 A, the frozen design's open-loop start at L x 0.7 (predicted); the "
    "handover itself 191.5 A (RESULTS 0)",
    ("criteria", "nom_L07_l_p48_1us/c3"): "211.0 A physical after +4.8 V / 1 us: the bridge-level pulse shift leaves the RTL's "
    "phase-1 timeline unmoved and slows the recovery from the ZVS loss (A164: 192.1 A) - why it is not adopted (RESULTS 0)",
    ("criteria", "ff_l_m80_10us/c4"): "Vo +28.7 mV against 27.9 allowed, as A164 (RESULTS 0)",
    ("criteria", "nom_L07_l_p48_1us/c4"): "Vo +12.8 mV against 11.7 allowed, back within 1 % in 35.4 us: the same slow recovery as its c3 (RESULTS 0)",
    **{("criteria", f"ss_{r}/c3"): "slow corner: late fires in the handover and after rising steps, NEW spikes after the "
       "steps, no peak or V_DS consequence, as A164 (RESULTS 0)" for r in ("l_p48_1us", "s_p62", "l_m80_10us", "slew4")},
}
_LATE166 = "the per-board lead (shortest delay - 1 ns) is too small for hard turn-ons after rising steps: late fires, no peak or V_DS consequence - why it is not adopted (RESULTS 0)"
EXCEPTIONS["A166"] = {
    ("criteria", "nom_L07_l_p48_1us/c2"): "mode S 202.5 A, the frozen design's open-loop start at L x 0.7 (RESULTS 0)",
    ("criteria", "nom_L07_l_p48_1us/c3"): "207.8 A physical (192.0 command-time) after +4.8 V / 1 us, 71 late fires, 2 NEW: " + _LATE166,
    ("criteria", "ff_l_m80_10us/c3"): "command-time 170.5 A against 170.3 allowed (RESULTS 0)",
    ("criteria", "ff_l_m80_10us/c4"): "Vo +29.1 mV, as A164 / A165 (RESULTS 0)",
    **{("criteria", f"{r}/c3"): _LATE166 for r in ("nom_l_p48_1us", "nom_slew4", "hot_l_p48_1us", "m4_nom_l_p48_1us",
                                                    "ss_l_p48_1us", "ss_s_p62", "ss_l_m80_10us", "ss_slew4")},
}
EXCEPTIONS["A167"] = {
    ("criteria", "nom_L07_l_p48_1us/c2"): "mode S 202.5 A, the frozen design's open-loop start at L x 0.7 (predicted); the "
    "handover 191.5 A (A164 218.6 A) (RESULTS 0)",
    **{("criteria", f"ss_{r}/c3"): "slow corner: late fires in the handover (102, more than A164's 65 while the lead ramps "
       "in) and after rising steps, NEW spikes after the steps, no peak or V_DS consequence (RESULTS 0)"
       for r in ("l_p48_1us", "s_p62")},
}
_SHOOT = ("shoot-through after the L x 0.7 handover: phase-4 dt_pred fell below the ramped lead (A164's mechanism); "
          "closed by A171's threshold interlock (RESULTS 0)")
_TRIM = "Vo(143.5 us) off the trim window: A164's trim was set without low-side gates; A172 re-trims (RESULTS 2)"
_GATE = "gate-form interlock serialises the low side's turn-off and the high side's gate delay (RESULTS 0)"
EXCEPTIONS["A168"] = {
    ("criteria", "P60_ff_l_p48_1us/c1"): "60 pH at 3.0 ohm: fast corner 40.3 V after +4.8 V / 1 us (predicted 40.0) - the "
    "reason the loop bound is 50 pH (RESULTS 0)",
    ("criteria", "Q60_nom_L07_l_p48_1us/c3"): _SHOOT,
    ("criteria", "Q75_nom_L07_l_p48_1us/c3"): _SHOOT,
    ("criteria", "Q60_ss_l_p48_1us/c3"): "slow corner at 4.2 ohm: 19 NEW one-period spikes, 376 late fires - why 60 pH is "
    "marginal (RESULTS 0)",
    ("criteria", "Q75_nom_l_p48_1us/c4"): "4.0 ohm: line-step Vo 12.6 mV / 46.1 us - why 75 pH does not work (RESULTS 0)",
    **{("criteria", f"Q75_ss_{r}/c3"): "slow corner at 4.8 ohm: late fires and NEW spikes - why 75 pH does not work "
       "(RESULTS 0)" for r in ("l_p48_1us", "s_p62")},
}
EXCEPTIONS["A169"] = {("criteria", f"{r}/c3"): "with gate-driven low sides the adopted drive shoots through where "
                      "dt_pred collapses; fixed by A171's interlock (RESULTS 0)" for r in ("nom_L07_l_p48_1us", "ss_l_p48_1us")}
EXCEPTIONS["A170"] = {
    **{("criteria", f"{s}/c{c}"): _GATE for s, cs in (("S50_nom_l_p48_1us", (3, 4)), ("S50_ss_l_p48_1us", (3,)),
                                                       ("S50_nom_L07_l_p48_1us", (3, 4)), ("S50t1_nom_L07_l_p48_1us", (3, 4)),
                                                       ("Q60_nom_L07_l_p48_1us", (3, 4)), ("Q75_nom_L07_l_p48_1us", (3, 4)))
       for c in cs},
    **{("criteria", f"{s}/c2"): _TRIM + "; Q60 / Q75 also carry their mode-S start-up peak (A168)"
       for s in ("S50_nom_L07_l_p48_1us", "S50t1_nom_L07_l_p48_1us", "Q60_nom_L07_l_p48_1us", "Q75_nom_L07_l_p48_1us")},
}
EXCEPTIONS["A171"] = {
    **{("criteria", f"{s}/c2"): _TRIM + "; Q60 / Q75 also carry their mode-S start-up peak (A168)"
       for s in ("S50_nom_L07_l_p48_1us", "S50t1_nom_L07_l_p48_1us", "Q60_nom_L07_l_p48_1us", "Q75_nom_L07_l_p48_1us")},
    ("criteria", "Q60_nom_L07_l_p48_1us/c4"): "60 pH / 3.5 ohm L x 0.7: Vo 11.5 mV / 35.6 us, as A168's margin (RESULTS 0)",
    ("criteria", "Q75_nom_L07_l_p48_1us/c3"): "75 pH / 4.0 ohm: NEW 48, late 15, as A168's slow timing (RESULTS 0)",
    ("criteria", "Q75_nom_L07_l_p48_1us/c4"): "75 pH / 4.0 ohm: Vo -11.2 mV (RESULTS 0)",
}
EXCEPTIONS["A173"] = {
    ("criteria", "ff_l_m80_10us/c3"): "one phase-2 restart (K3) and a 153 A spike 14.5 us after the falling ramp: A148's "
    "valley loss, one period deeper than on V2; step positions in A174 (RESULTS 0)",
    ("criteria", "ff_l_m80_10us/c4"): "Vo 31.1 mV and back 24.9 us, each 0.6 over the limit (RESULTS 0)",
    ("criteria", "ss_l_m80_10us/c4"): "slow corner: post-ramp Vo dip 2.9 mV deeper than V2 (low-side turn-off delay plus "
    "holds), -25.2 mV (RESULTS 0)",
    ("criteria", "ss_slew4/c4"): "slow corner: post-ramp Vo dip -13.5 mV (V2 -8.6), outside 1 % for 7.6 us (RESULTS 0)",
    ("criteria", "m4_ss_l_p48_1us/c3"): "8 NEW 10-16 A spikes: 4 = A160's K4-window artefact, 3 slow-corner ladder spikes as "
    "on V2, 1 duplicate turn-on 0.1 ns apart; peaks 193.0 / 181.4 A (RESULTS 0)",
}
_FFPH = "ff -8 V / 10 us at another step phase: Vo 30.6-31.8 mV at every phase (limit 30.5), post-step +5-6 A over V2 " \
        "from the gate-driven low sides (A176); the spike only at 2 of 5 phases (RESULTS 0)"
_FIXREF = "fixed 1.0 V interlock reference (8.3 ns) at the slow corner: peaks hold, timing does not - the slow corner " \
          "needs the per-board reference (RESULTS 0)"
EXCEPTIONS["A174"] = {
    ("criteria", "sh4_nom_L07_l_p48_1us/c3"): "L x 0.7 at +4 T/5: 201.5 A - the board exceeds 200 A at one of five step "
    "phases; the spec names it (RESULTS 0)",
    ("criteria", "sh4_nom_L07_l_p48_1us/c4"): "L x 0.7 at +4 T/5: Vo 11.0 mV, back 37.9 us (RESULTS 0)",
    **{("criteria", f"sh{k}_ff_l_m80_10us/c{c}"): _FFPH for k, cs in ((1, (3, 4)), (2, (3, 4)), (3, (4,)), (4, (3, 4)))
       for c in cs},
    **{("criteria", f"fr_{r}/c4"): _FIXREF for r in ("ss_l_m80_10us", "ss_s_p62", "ss_slew4", "m4_ss_l_p48_1us")},
}
_PB = "per-board interlock reference (1.4 ns) at the slow corner: small timing excess over the 0.5 ns run (late fires " \
      "rise monotonically with the release delay; NEW / Vo scatter near the tolerance); no peak or V_DS change - the " \
      "slow corner wants a release below 1.4 ns (RESULTS 0)"
EXCEPTIONS["A177"] = {("criteria", f"pb_{r}/c4"): _PB for r in ("ss_l_m80_10us", "ss_s_p62", "m4_ss_l_p48_1us")}
_R2NEW = "ss load step: one-period 10-18 A spikes after the step scatter 7-27 at >= 1.0 ns (means 18 / 19 / 14 at " \
         "0.5 / 1.0 / 1.4 ns) against the +2 tolerance; no late fires, peaks unchanged - named open (RESULTS 0, 2)"
EXCEPTIONS["A179"] = {
    ("criteria", "3_release/ss_l_m80_10us 1.4"): "-8 V / 10 us at 1.4 ns: 51 post-step late fires at one of three positions "
    "(47 in A177) against 36.5 - the slow corner's release time is <= 1.0 ns (RESULTS 0)",
    ("criteria", "3_release/ss_s_p62 1.4"): _R2NEW,
    ("criteria", "3_release/ss_s_p62 1.0"): _R2NEW,
}
_S75 = "slow devices with L x 0.75, trimmed once at 25 C: open-loop start-up 202-207 A (any trim near the target is " \
       "above 200 A) and a 278 A handover runaway at 25 C - L x 0.75 holds with nominal devices only (RESULTS 0, 2)"
EXCEPTIONS["A181"] = {
    **{(f"runs/S75_{t}_p{k}", "c1_startup"): _S75 for t in ("25", "hot") for k in range(3)},
    ("runs/S75_hot_p1", "c2_post"): "slow devices, L x 0.75, 125 C: 202.8 A after +4.8 V / 1 us at one of three step "
    "positions (RESULTS 0)",
}
EXCEPTIONS["A183"] = {
    ("S75_hot_p0", "c5"): "250-300 us against the 25 C record listed in the BOUNDARY: 2.59 A; the t0 400 references "
    "were still settling there - at 400-495 us every full run is within 1.4 A of its own t0 400 record (RESULTS 0)",
}
_DIP = "handover Vo minimum below the t0 400 record - 5 mV: mode S at 200 ns ends with valleys at +25..+47 A against " \
       "mode P's -15.6 A, which turns the loop's first-Ton shortfall below steady state into a dip; peaks unaffected " \
       "(RESULTS 0)"
_HOT = "hot, trim locked at 25 C: mode S's Vo drifts +15..+95 mV (every turn-on hard), kp drives Ton to the 0.5x clamp " \
       "at entry and Vo undershoots (RESULTS 0)"
EXCEPTIONS["A184"] = {
    **{(r, "c6"): _DIP for r in ("N0_25_p0", "F0_25_p0", "N13_25_p0", "M4_25_p0")},
    **{(r, "c6"): _HOT for r in ("N0_hot_p0", "S0_hot_p0", "S75_hot_p0")},
    ("S75_hot_p0", "c2"): "slow devices, L x 0.75, 125 C: 206.7 A after +4.8 V / 1 us with the step at phase 0.86 of the "
    "period - a mode-P property (A181 at t0 400: 202.8 A at phase 0.81); 25 C <= 198.7 A (RESULTS 0)",
}
EXCEPTIONS["A185"] = {(r, "c6"): "L0 board, 25 C: handover Vo minimum 1-4 mV below the t0 400 record - 5 mV; the seed puts "
                     "the first Ton on its steady value, the rest is the mode-S 200 ns -> mode-P ~520 ns period jump "
                     "(phase 4's valley to -71 A while the slots catch up) (RESULTS 0)" for r in ("N0_25_p0", "F0_25_p0", "M4_25_p0")}
_A186 = "request at 1.03 V: at 25 C it fires while Vo is still rising (N13 +5.3 mV/us, valleys 57 / 52 / 44 / 41 A), " \
        "so mode P closes a larger current gap; superseded by A188's 1.045 V (RESULTS 0)"
EXCEPTIONS["A186"] = {
    ("N13_25_p0", "c4"): "Vo(143.5 us) 0.982 V lies inside mode P after the 140.4 us handover; " + _A186,
    ("S75_25_p0", "c5"): "2.34 A: the controller's learned valley settles at -13.5 / -13.8 / -15.1 / -16.3 A across A181 / "
    "A184-A186 (A143's history-dependent floor spread), Vo 1.000 V and Ton 32.3-32.5 ns in all (RESULTS 0)",
    **{(r, "c6"): "handover minimum <= 2 mV below the t0 400 record - 5 mV; " + _A186
       for r in ("F0_25_p0", "M4_25_p0", "N0_hot_p0")},
}
_A187 = "slow devices at 125 C after +4.8 V / 1 us: phases 3-4 lose their valley for ~25 us (valley-timing limit), Vo " \
        "dips, the loop raises Ton ~20 % and a recovering valley meets it; above 200 A at 2 of 6 step positions on both " \
        "boards - the slow corner's limit lies above 0.8 L0 at 125 C (RESULTS 0)"
EXCEPTIONS["A187"] = {(r, "c2"): _A187 for r in ("S75_hot_p3", "S75_hot_p5", "S80_hot_p3", "S80_hot_p5")}
EXCEPTIONS["A175"] = {
    ("criteria", "nom_l_m48_1us/c3"): "-4.8 V / 1 us: 3 K3 restarts and 6 NEW 10-20 A spikes 27-41 us after the step - "
    "A148's falling-step valley loss turned into restarts by the lead plus the gate-driven low sides (A176); post-step "
    "172.4 A (RESULTS 0)",
}
ADAPT = {   # summaries written before this gate's format: map their registered criteria to a "criteria" block
    "A151": lambda d: {"1_harness": d["c1"], "2_l50": d["c2"], "3_l100": d["c3"], "4_controller_l50": d["c2"]["c4"],
                       "4_controller_l100": d["c3"]["c4"], "5_edge_power_l50": d["c2"]["c5"],
                       "5_edge_power_l100": d["c3"]["c5"]},
    "A145": lambda d: {**d["criteria"], "2_voltage": {k: bool(v) for k, v in d["criteria"]["2_voltage"].items()}},
    # (A145 lists the inductances that pass per di/dt; the criterion passes for a di/dt with any)
    "A152": lambda d: {"S50": d["points"]["50"], "S100": d["points"]["100"], "6_300pH": d["c6"]},
    # A163 lists misses per run; part C (s50cmd_) is a diagnostic, not judged (BOUNDARY 1)
    "A163": lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items() if "cmd" not in s},
    "A164": lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items()},
    "A165": lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items()},
    "A166": lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items()},
    "A167": lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items()},
    **{e: (lambda d: {s: {f"c{k}": not v for k, v in c.items()} for s, c in d["verdict"].items()})
       for e in ("A168", "A169", "A170", "A171", "A172", "A173", "A174", "A175", "A177", "A178")},
}


def flat(c, prefix=""):
    """{criterion: bool}: a criterion that is {"pass": bool, ...} counts as its pass; one that is a dict of corners
    contributes its boolean entries as <criterion>/<corner>/<entry>."""
    out = {}
    for k, v in c.items():
        if isinstance(v, bool):
            out[prefix + k] = v
        elif isinstance(v, dict) and isinstance(v.get("pass"), bool):
            out[prefix + k] = v["pass"]
        elif isinstance(v, dict):
            out.update(flat(v, prefix + k + "/"))
    return out


def criteria_sets(d, prefix=""):
    """(row, {criterion: bool}) for every criteria block of a summary."""
    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        if isinstance(v.get("criteria"), dict):
            yield prefix + k, flat(v["criteria"])
        elif k.startswith("criteria"):
            yield prefix + k, flat(v)
        elif k in ("part_a", "part_b"):
            yield from criteria_sets(v, prefix + k + "/")
        elif k in ("runs", "rows"):                                  # one entry per run, each possibly with its criteria
            yield from criteria_sets(v, prefix + k + "/")


def summary_rows(d):
    rows = set()
    for k, v in d.items():
        if k in ("part_a", "part_b") and isinstance(v, dict):
            rows |= set(v)
        elif k in ("runs", "rows") and isinstance(v, dict):
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
    if name in ADAPT:
        d["criteria"] = ADAPT[name](d)
    have = summary_rows(d)
    pre, skip = ROW_PREFIX.get(name, ""), re.compile(NOT_ROWS.get(name, "(?!)"))
    out["MISSING"] += [f"row {r} not in {summary}" for r in runs
                       if r.removeprefix(pre) not in have and not skip.match(r)]
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
