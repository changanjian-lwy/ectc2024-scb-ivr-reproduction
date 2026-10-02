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
