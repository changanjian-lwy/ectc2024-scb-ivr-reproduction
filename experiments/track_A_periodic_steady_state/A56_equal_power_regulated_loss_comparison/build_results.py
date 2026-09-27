"""Aggregate A56 runs into results.json and print the RESULTS.md tables.

Inputs (all produced by this experiment's own scripts):
  runs/<label>.json                 run_regulated_candidate.py, 62.5 ps / 5 ps
  runs/<label>_step*.json           same driver at refined steps
  capacitive_accounting.json        capacitive_accounting_check.py
The regulation-variable proof tests are re-run here and their outcome stored.
results.json is never overwritten.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import regulated_boundary as R  # noqa: E402

OUT = HERE / "results.json"
BASELINE = "nominal_dt_x1"
CO_ER_OVER_CO_TR = 1597.0 / 1860.0  # EPC2067_typical_params.lib, both 0-20 V
_REF = R.build_regulated_boundary(phase_inductance_h=R.L_ROWS[2][1], dead_time_s=2.15e-9,
                                  ton_cmd_s=R.NOMINAL_TON_S)
RON = dict(high=_REF.high_side_on_resistance_ohm, low=_REF.low_side_on_resistance_ohm)


def run_proof_tests() -> dict:
    suite = unittest.defaultTestLoader.loadTestsFromName("test_regulated_boundary")
    ids = [t.id().split(".", 1)[1] for t in _iter(suite)]
    result = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(suite)
    return dict(file="test_regulated_boundary.py", tests_run=result.testsRun,
                failures=len(result.failures), errors=len(result.errors),
                passed=result.wasSuccessful(), tests=ids)


def _iter(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter(item)
        else:
            yield item


def trial_summary(t: dict) -> dict:
    m = t.get("metrics", {})
    return dict(
        iteration=t["iteration"], ton_cmd_s=t["ton_cmd_s"], choice_reason=t["choice_reason"],
        seed=t["seed"], seed_ton_cmd_s=t["seed_ton_cmd_s"], outcome=t["outcome"],
        converged=t.get("converged"), relative_residual=t.get("relative_residual"),
        newton_iterations=t.get("iterations_used"),
        load_power_w=m.get("actual_load_power_w"), power_relative_error=t.get("power_relative_error"),
        channel_loss_w=m.get("actual_branch_channel_loss_w"),
        high_zvs=m.get("natural_zvs_flags"),
        low_zvs=[v["natural"] for v in m.get("low_side_turn_on_verdicts", [])] or None,
        accepted_orbit_max_abs_current_a=m.get("maximum_abs_phase_current_a"),
        probe_max_abs_current_a=(t.get("solver_probe_safety") or {}).get("maximum_abs_phase_current_a",
                                                                          t.get("tripping_probe_abs_current_a")),
        probe_evaluations=(t.get("solver_probe_safety") or {}).get("evaluations"),
        error=t.get("error"), wall_time_s=t.get("wall_time_s"))


def state_summary(reg: dict, cap: dict | None) -> dict:
    m = reg["metrics"]
    high = m["natural_zvs_flags"]
    low = [v["natural"] for v in m["low_side_turn_on_verdicts"]]
    missing = cap["missing_capacitive_power_w"] if cap else None
    out = dict(
        ton_cmd_s=reg["ton_cmd_s"], ton_cmd_deviation_from_nominal_s=m["ton_cmd_deviation_from_nominal_s"],
        ton_cmd_relative_deviation_from_nominal=m["ton_cmd_relative_deviation_from_nominal"],
        load_power_w=m["actual_load_power_w"], power_relative_error=reg["power_relative_error"],
        average_output_v=m["average_output_v"], load_resistance_ohm=m["load_resistance_ohm"],
        solver_relative_residual=reg["relative_residual"], metered_relative_closure=m["relative_closure"],
        high_side_natural_zvs=high, low_side_natural_zvs=low, all_eight_zvs=bool(all(high) and all(low)),
        high_side_hard_switch_residual_v=[v["hard_switch_residual_v"] for v in m["high_side_turn_on_verdicts"]],
        low_side_hard_switch_residual_v=[v["hard_switch_residual_v"] for v in m["low_side_turn_on_verdicts"]],
        phase_minimum_a=m["phase_minimum_a"], phase_maximum_a=m["phase_maximum_a"],
        maximum_abs_phase_current_a=m["maximum_abs_phase_current_a"],
        current_at_high_side_deadtime_entry_a=m["current_at_high_side_deadtime_entry_a"],
        negative_entry_to_positive_peak_ratio=m["negative_entry_to_positive_peak_ratio"],
        max_negative_entry_ratio=max(m["negative_entry_to_positive_peak_ratio"]),
        negative_valley_to_positive_peak_ratio=m["negative_valley_to_positive_peak_ratio"],
        modeled_high_channel_active_duration_s=m["modeled_high_channel_active_duration_s"],
        modeled_low_channel_active_duration_s=m["modeled_low_channel_active_duration_s"],
        high_side_channel_loss_w=m["high_side_channel_loss_w"],
        low_side_channel_loss_w=m["low_side_channel_loss_w"],
        a55_meter_channel_loss_w=m["actual_branch_channel_loss_w"],
        legacy_phase_current_loss_proxy_w=m["legacy_phase_current_loss_proxy_w"],
        missing_hard_switch_capacitive_w=missing,
        partial_loss_proxy_w=(m["actual_branch_channel_loss_w"] + missing) if cap else None,
        complete_total_loss=False)
    if cap:
        f_sw = 1.0 / 200e-9
        exposure = cap["dead_time_surrogate_exposure"]
        metered_in_intervals = 0.0
        for event in exposure["events"]:
            r = RON[event["side"]]
            metered_in_intervals += r * event["i2_dt_a2s"] * f_sw
        out.update(
            hard_switched_event_count=cap["hard_switched_event_count"],
            half_c_meas_v2_fsw_total_w=cap["half_c_meas_v2_fsw_total_w"],
            capacitive_captured_by_a55_meter_w=cap["orbit_captured_capacitive_w"],
            energy_balance=cap["energy_balance"],
            surrogate_dead_time_abs_current_time_per_second_a=exposure["mean_abs_current_time_per_second_a"],
            channel_loss_metered_inside_surrogate_intervals_w=metered_in_intervals,
            surrogate_admissions=exposure["events"])
    return out


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; results are never overwritten")
    proof = run_proof_tests()
    cap_doc = json.loads((HERE / "capacitive_accounting.json").read_text())
    cap_by_name = {o["name"]: o for o in cap_doc["orbits"]}

    candidates, refinements = [], []
    for row, inductance in R.L_ROWS:
        for factor, dead_time in R.DT_COLUMNS:
            label = f"{row}_dt_x{factor:g}"
            run = json.loads((HERE / "runs" / f"{label}.json").read_text())
            reg = run.get("regulated")
            trials = [trial_summary(t) for t in run["trials"]]
            probe_max = max((t["probe_max_abs_current_a"] or 0.0) for t in trials)
            accepted_max = max((t["accepted_orbit_max_abs_current_a"] or 0.0) for t in trials)
            entry = dict(label=label, phase_inductance_h=inductance, dead_time_s=dead_time,
                         status=run["status"], stop_reason=run.get("stop_reason"),
                         outer_trials=len(trials), a55_reference_metrics=run["a55_reference_metrics"],
                         replay_matches_a55=(
                             trials[0]["load_power_w"] == run["a55_reference_metrics"]["actual_load_power_w"]
                             and trials[0]["channel_loss_w"] ==
                             run["a55_reference_metrics"]["actual_branch_channel_loss_w"]),
                         max_probe_abs_current_all_trials_a=probe_max,
                         max_accepted_orbit_abs_current_all_trials_a=accepted_max,
                         trials=trials)
            if reg:
                entry["regulated"] = state_summary(reg, cap_by_name.get(label))
                entry["regulated"]["z_star"] = reg["z_star"]
                t = next(t for t in trials if t["iteration"] == reg["iteration"])
                entry["regulated"]["probe_max_abs_current_a"] = t["probe_max_abs_current_a"]
            candidates.append(entry)
    for path in sorted((HERE / "runs").glob("*_step*.json")):
        run = json.loads(path.read_text())
        reg = run.get("regulated")
        trials = [trial_summary(t) for t in run["trials"]]
        refinements.append(dict(
            name=path.stem, label=run["label"], coarse_step_s=run["coarse_step_s"],
            sub_step_s=run["sub_step_s"], status=run["status"], stop_reason=run.get("stop_reason"),
            seed=run["initial_seed_source"], outer_trials=len(trials),
            max_probe_abs_current_all_trials_a=max((t["probe_max_abs_current_a"] or 0.0) for t in trials),
            regulated=state_summary(reg, cap_by_name.get(path.stem)) if reg else None,
            trials=trials))

    by_label = {c["label"]: c for c in candidates}
    eligible = [c for c in candidates if c.get("regulated")
                and c["regulated"]["maximum_abs_phase_current_a"] <= R.CURRENT_SCREEN_A]
    base = by_label[BASELINE].get("regulated")
    comparison = []
    for c in eligible:
        s = c["regulated"]
        comparison.append(dict(
            label=c["label"], all_eight_zvs=s["all_eight_zvs"], ton_cmd_s=s["ton_cmd_s"],
            load_power_w=s["load_power_w"], a55_meter_channel_loss_w=s["a55_meter_channel_loss_w"],
            missing_hard_switch_capacitive_w=s["missing_hard_switch_capacitive_w"],
            partial_loss_proxy_w=s["partial_loss_proxy_w"],
            delta_partial_loss_vs_baseline_w=(s["partial_loss_proxy_w"] - base["partial_loss_proxy_w"]
                                              if base else None),
            delta_a55_meter_vs_baseline_w=(s["a55_meter_channel_loss_w"] - base["a55_meter_channel_loss_w"]
                                           if base else None),
            # Sensitivity only: scale the WHOLE hard-switch discharge energy
            # (part captured by the A55 meter + part it misses) by Co(er)/Co(tr).
            partial_loss_with_capacitive_scaled_by_coer_over_cotr_w=(
                s["a55_meter_channel_loss_w"] - s["capacitive_captured_by_a55_meter_w"]
                + CO_ER_OVER_CO_TR * (s["capacitive_captured_by_a55_meter_w"]
                                      + s["missing_hard_switch_capacitive_w"])),
            surrogate_dead_time_abs_current_time_per_second_a=s.get(
                "surrogate_dead_time_abs_current_time_per_second_a"),
            channel_loss_metered_inside_surrogate_intervals_w=s.get(
                "channel_loss_metered_inside_surrogate_intervals_w")))
    comparison.sort(key=lambda r: r["partial_loss_proxy_w"])
    zvs = [r for r in comparison if r["all_eight_zvs"]]
    base_row = next(r for r in comparison if r["label"] == BASELINE) if base else None
    break_even = []
    if base_row:
        for r in zvs:
            dx = (r["surrogate_dead_time_abs_current_time_per_second_a"]
                  - base_row["surrogate_dead_time_abs_current_time_per_second_a"])
            numerator = (base_row["partial_loss_proxy_w"] - r["partial_loss_proxy_w"]
                         - base_row["channel_loss_metered_inside_surrogate_intervals_w"]
                         + r["channel_loss_metered_inside_surrogate_intervals_w"])
            break_even.append(dict(label=r["label"], delta_abs_current_time_a=dx,
                                   illustrative_break_even_reverse_drop_v=(numerator / dx if dx > 0 else None)))

    # Step-refinement ladder (BOUNDARY S3.5) plus a source-side check that uses
    # no branch metering at all: P_src - P_load from the exact BE energy
    # identity, Richardson-extrapolated (first order) from the two finest steps.
    ladder = {}
    for label in {r["label"] for r in refinements}:
        rows = []
        for name in (label, f"{label}_step2p5ps", f"{label}_step1p25ps"):
            o = cap_by_name.get(name)
            if not o:
                continue
            eb = o["energy_balance"]
            rows.append(dict(name=name, coarse_step_s=o["coarse_step_s"], sub_step_s=o["sub_step_s"],
                             ton_cmd_s=o["ton_cmd_s"], load_power_w=o["load_power_w"],
                             a55_meter_channel_loss_w=o["a55_meter_channel_loss_w"],
                             missing_hard_switch_capacitive_w=o["missing_capacitive_power_w"],
                             partial_loss_proxy_w=o["channel_loss_plus_missing_capacitive_w"],
                             source_minus_load_w=eb["source_w"] - eb["load_w"],
                             integrator_removed_w=eb["numerical_w"],
                             integrator_removed_in_event_windows_w=eb["numerical_in_event_windows_w"],
                             other_resistive_w=eb["other_resistive_w"]))
        rows.sort(key=lambda r: -r["coarse_step_s"])
        entry = dict(label=label, levels=rows)
        if len(rows) >= 3:
            a, b = rows[-2]["source_minus_load_w"], rows[-1]["source_minus_load_w"]
            entry["source_minus_load_richardson_h0_w"] = 2 * b - a
            entry["source_minus_load_successive_differences_w"] = [
                rows[i]["source_minus_load_w"] - rows[i + 1]["source_minus_load_w"]
                for i in range(len(rows) - 1)]
            entry["partial_loss_proxy_spread_w"] = (max(r["partial_loss_proxy_w"] for r in rows)
                                                    - min(r["partial_loss_proxy_w"] for r in rows))
            entry["a55_meter_spread_w"] = (max(r["a55_meter_channel_loss_w"] for r in rows)
                                           - min(r["a55_meter_channel_loss_w"] for r in rows))
        ladder[label] = entry

    safety = dict(
        screen_a=R.CURRENT_SCREEN_A, note="project screen, not EPC2067 SOA",
        max_accepted_orbit_abs_current_regulated_states_a=max(
            c["regulated"]["maximum_abs_phase_current_a"] for c in candidates if c.get("regulated")),
        max_probe_abs_current_regulated_trials_a=max(
            c["regulated"]["probe_max_abs_current_a"] for c in candidates if c.get("regulated")),
        max_probe_abs_current_any_trial_a=max(c["max_probe_abs_current_all_trials_a"] for c in candidates),
        max_accepted_orbit_abs_current_any_trial_a=max(
            c["max_accepted_orbit_abs_current_all_trials_a"] for c in candidates),
        max_probe_abs_current_refinement_runs_a=max(
            (r["max_probe_abs_current_all_trials_a"] for r in refinements), default=None),
        trials_failing_probe_screen=[(c["label"], t["iteration"]) for c in candidates for t in c["trials"]
                                     if t["outcome"] == "probe_current_screen"],
        trials_failing_accepted_orbit_screen=[(c["label"], t["iteration"]) for c in candidates
                                              for t in c["trials"]
                                              if t["outcome"] == "accepted_orbit_current_screen"])

    result = dict(
        experiment="A56", classification="SENSITIVITY_ONLY",
        boundary="BOUNDARY.md (commit f0e0041)",
        objective="partial electrical-loss proxy = A55 actual enabled-branch channel dissipation "
                  "+ hard-switch capacitive discharge energy the A55 meter misses (BOUNDARY S3.4); "
                  "not total loss",
        regulation=dict(variable="Ton_cmd (D01 command on-interval), same for all phases",
                        load_resistance_ohm=R.RATED_LOAD_OHM, target_power_w=R.TARGET_POWER_W,
                        tolerance_relative=R.POWER_TOLERANCE, nominal_ton_s=R.NOMINAL_TON_S),
        regulation_variable_proof=dict(
            tests=proof,
            findings=[
                "commanded_pwm_mode, next_pwm_edge_s, A51 period_intervals/_window_mode and "
                "resolve_deadtime_window all read boundary.on_time_s; none reads duty",
                "a duty-poisoned boundary completes a full period map and A55 metering",
                "A53 solve_fixed_point passes the boundary object through unchanged",
                "A55 metered_orbit rebuilds its boundary from (L, dead time) and would silently "
                "meter at the nominal 16.6667 ns schedule; A56 uses a scoped, documented rebinding "
                "(regulated_boundary.regulated_metering) so A55's unchanged code meters the "
                "regulated boundary; the test proves both the defect and the fix",
                "load resistance is exactly 0.004 Ohm in every regulated boundary and 1/0.004 S in "
                "the assembled descriptor"]),
        candidates=candidates, step_refinement=dict(runs=refinements, ladder=ladder),
        capacitive_accounting=dict(
            source="capacitive_accounting.json",
            orbits=[{k: v for k, v in o.items() if k not in ("hard_switched_events",
                                                            "dead_time_surrogate_exposure")}
                    | dict(events=[{k: v for k, v in e.items() if k != "step_ladder"}
                                   for e in o["hard_switched_events"]])
                    for o in cap_doc["orbits"]]),
        comparison_at_250w=dict(baseline=BASELINE, ranked_by_partial_loss_proxy=comparison,
                                illustrative_reverse_conduction_break_even=break_even,
                                co_er_over_co_tr=CO_ER_OVER_CO_TR),
        safety=safety)
    OUT.write_text(json.dumps(result, indent=1, default=str) + "\n")

    # ---- console tables for RESULTS.md ----
    print(f"proof tests: {proof['tests_run']} run, passed={proof['passed']}")
    print("| L (nH) | DT (ns) | status | Ton_cmd (ns) | dTon vs 16.667 | P (W) | H1-H4 | L1-L4 | "
          "A55 meter (W) | missing C (W) | proxy (W) | peak |iL| (A) | probe max (A) | neg entry max (%) |")
    for c in candidates:
        s = c.get("regulated")
        if not s:
            print(f"| {c['phase_inductance_h']*1e9:.6f} | {c['dead_time_s']*1e9:.3f} | {c['status']} "
                  f"({c['stop_reason']}) |")
            continue
        flags = lambda v: "/".join("T" if x else "F" for x in v)
        print(f"| {c['phase_inductance_h']*1e9:.6f} | {c['dead_time_s']*1e9:.3f} | regulated | "
              f"{s['ton_cmd_s']*1e9:.4f} | {s['ton_cmd_deviation_from_nominal_s']*1e9:+.4f} "
              f"({s['ton_cmd_relative_deviation_from_nominal']*100:+.2f}%) | {s['load_power_w']:.3f} | "
              f"{flags(s['high_side_natural_zvs'])} | {flags(s['low_side_natural_zvs'])} | "
              f"{s['a55_meter_channel_loss_w']:.3f} | {s['missing_hard_switch_capacitive_w']:.3f} | "
              f"{s['partial_loss_proxy_w']:.3f} | {s['maximum_abs_phase_current_a']:.2f} | "
              f"{s['probe_max_abs_current_a']:.2f} | {s['max_negative_entry_ratio']*100:.2f} |")
    print(json.dumps(dict(comparison=comparison, break_even=break_even, safety=safety), indent=1,
                     default=str))
    for r in refinements:
        s = r["regulated"]
        print(r["name"], r["status"], s and dict(ton=s["ton_cmd_s"], P=s["load_power_w"],
              meter=s["a55_meter_channel_loss_w"], missing=s["missing_hard_switch_capacitive_w"],
              proxy=s["partial_loss_proxy_w"], H=s["high_side_natural_zvs"], L=s["low_side_natural_zvs"]))
    print(json.dumps(ladder, indent=1))


if __name__ == "__main__":
    main()
