"""A51 - assemble `results.json` from the five run artifacts.

This script performs no simulation of its own; it only collects the key numbers
already written by

    run_cfly_reverification.py -> cfly_reverification.json
    run_map_selftests.py       -> map_selftests.json
    run_fixed_point_search.py  -> fixed_point_search.json
    run_final_verification.py  -> final_verification.json
    run_robustness_sweeps.py   -> robustness_sweeps.json

so that `RESULTS.md` and `results.json` cannot drift from what was actually run.

Run:  python3 build_results.py --output results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(name: str) -> dict:
    return json.loads(Path(name).read_text())


def load_optional(name: str) -> dict | None:
    path = Path(name)
    return json.loads(path.read_text()) if path.exists() else None


def phase_summary(verification: dict | None) -> list | None:
    """Condense one `run_final_verification.py` artifact to its verdict rows."""
    if verification is None:
        return None
    rows = []
    for entry in verification["phases"]:
        ladder = entry["sub_step_ladder"]
        rows.append(
            {
                "phase": entry["phase"],
                "natural_zvs": entry["natural_zvs"],
                "phase_current_at_window_entry_a": entry[
                    "phase_current_at_window_entry_a"
                ],
                "phase_current_minimum_over_orbit_a": entry[
                    "phase_current_minimum_over_orbit_a"
                ],
                "initial_vds_v": ladder[0]["initial_vds_v"],
                "minimum_abs_vds_v_finest": ladder[-1]["minimum_abs_vds_v"],
                "minimum_abs_vds_v_richardson": entry["richardson"][
                    "minimum_abs_vds_v"
                ],
                "vds_at_window_end_v_finest": ladder[-1][
                    "vds_at_commanded_window_end_v"
                ],
                "crossed_1mv_at_every_rung": [
                    row["crossed_1mv"] for row in ladder
                ],
                "sub_step_ladder_ps": [row["sub_step_ps"] for row in ladder],
                "sub_step_ladder_minimum_abs_vds_v": [
                    row["minimum_abs_vds_v"] for row in ladder
                ],
                "sign_change_time_s_finest": ladder[-1]["sign_change_time_s"],
                "measured_node_capacitance_f": entry["measured_node_capacitance_f"],
                "free_resonance_probe": entry["free_resonance_probe"],
                "threshold_current": entry["threshold_current"],
                "state_sensitivity": entry["state_sensitivity"],
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results.json")
    args = parser.parse_args()

    cfly = load("cfly_reverification.json")
    selftests = load("map_selftests.json")
    search = load("fixed_point_search.json")
    final = load("final_verification.json")
    sweeps = load("robustness_sweeps.json")
    loads = load_optional("load_sweep.json")
    stability = load_optional("stability_and_divider.json")
    stability_190 = load_optional("stability_and_divider_190w.json")
    verification_190 = load_optional("final_verification_190w.json")
    verification_10ns = load_optional("final_verification_deadtime_10ns.json")

    names = search["variable_names"]
    z = search["newton"]["final_state"]

    verdict_all_hard = not any(search["newton"]["final_natural_zvs_flags"])
    if search["newton"]["converged"] and verdict_all_hard:
        outcome = "FIXED_POINT_FOUND_NO_PHASE_ACHIEVES_NATURAL_ZVS"
    elif search["newton"]["converged"] and all(
        search["newton"]["final_natural_zvs_flags"]
    ):
        outcome = "FULL_FOUR_PHASE_JOINT_ZVS_PERIODIC_STATE_FOUND"
    elif search["newton"]["converged"]:
        outcome = "FIXED_POINT_FOUND_SOME_PHASES_HARD_SWITCH"
    else:
        outcome = "NO_FIXED_POINT_FOUND_WITHIN_BUDGET"

    payload = {
        "experiment": "A51_four_phase_joint_zvs_solve",
        "boundary_section_6_outcome": outcome,
        "step_2_cfly_reverification": {
            "summary": cfly["summary"],
            "cross_cfly_comparison": cfly["cross_cfly_comparison"],
            "sub_steps_s": cfly["sub_steps_s"],
        },
        "map_selftests": {
            "all_passed": selftests["all_passed"],
            "tests": [
                {"test": item["test"], "passed": item["passed"],
                 "detail": item.get("detail", "")}
                for item in selftests["tests"]
            ],
            "sub_step_ladder": selftests["tests"][-1]["sub_step_ladder"],
            "coarse_step_ladder": selftests["tests"][-1]["coarse_step_ladder"],
        },
        "step_4_seed_conversion": {
            "a37_best_candidate": {
                row["variable"]: row["value"] for row in search["seed_conversion"]
            },
            "conversion_table": search["seed_conversion"],
            "seed_state": search["seed_state"],
            "variable_names": names,
        },
        "step_3_4_search": {
            "boundary": search["boundary"],
            "numerics": search["numerics"],
            "newton_history": [
                {
                    "iteration": record["iteration"],
                    "relative_residual": record["relative_residual"],
                    "absolute_residual_inf": record["absolute_residual_inf"],
                    "natural_zvs_flags": record["natural_zvs_flags"],
                    "jacobian_rank": record.get("jacobian_rank"),
                    "jacobian_nullity": record.get("jacobian_nullity"),
                    "unreachable_residual_inf": record.get("unreachable_residual_inf"),
                    "accepted_damping": record.get("accepted_damping"),
                    "jacobian_rebuilt": record.get("jacobian_rebuilt"),
                }
                for record in search["newton"]["history"]
            ],
            "converged": search["newton"]["converged"],
            "final_relative_residual": search["newton"]["final_relative_residual"],
            "final_absolute_residual_inf": search["newton"][
                "final_absolute_residual_inf"
            ],
            "final_state": z,
            "final_state_by_variable": dict(zip(names, z)),
            "final_orbit_metrics": search["newton"]["final_orbit_metrics"],
            "final_verdicts": search["newton"]["final_verdicts"],
            "tap_degeneracy": search["tap_degeneracy"],
            "precharge_diode_audit": search["precharge_diode_audit"],
            "picard_history": search["picard"]["history"],
            "picard_damping": search["picard"]["damping"],
        },
        "step_5_per_phase_verification": {
            "relative_residual_at_final_state": final[
                "relative_residual_at_final_state"
            ],
            "natural_zvs_flags": final["natural_zvs_flags"],
            "phases": phase_summary(final),
        },
        "load_sweep": None
        if loads is None
        else {
            "classification": loads["classification"],
            "rated_module_power_w": loads["rated_module_power_w"],
            "highest_power_with_all_four_phases_zvs_w": loads[
                "highest_power_with_all_four_phases_zvs_w"
            ],
            "highest_power_with_any_phase_zvs_w": loads[
                "highest_power_with_any_phase_zvs_w"
            ],
            "rows": [
                {
                    key: row[key]
                    for key in (
                        "module_power_w",
                        "failed",
                        "converged",
                        "final_relative_residual",
                        "natural_zvs_flags",
                        "average_output_v",
                        "average_load_power_w",
                        "phase_current_minima_a",
                        "phase_current_maxima_a",
                        "phase_current_ripple_a",
                        "minimum_abs_vds_v",
                        "flying_capacitor_v",
                        "maximum_abs_phase_current_a",
                        "safety_within_limit",
                    )
                    if key in row
                }
                for row in loads["rows"]
            ],
        },
        "four_phase_zvs_state_at_190w": None
        if verification_190 is None
        else {
            "note": "SENSITIVITY_ONLY. 190 W is NOT a P24 operating point; "
            "P24's rated point is 250 W per module. Not a P24/P25 reproduction.",
            "relative_residual": verification_190[
                "relative_residual_at_final_state"
            ],
            "natural_zvs_flags": verification_190["natural_zvs_flags"],
            "final_state": verification_190["final_state"],
            "final_state_by_variable": dict(
                zip(verification_190["variable_names"], verification_190["final_state"])
            ),
            "phases": phase_summary(verification_190),
            "safety": verification_190["safety"],
        },
        "four_phase_zvs_state_at_dead_time_10ns": None
        if verification_10ns is None
        else {
            "note": "SENSITIVITY_ONLY. d=10 ns is 4.65x A48's own bracket; this "
            "state is de-rated (0.706 V, 124.7 W) and its flying-capacitor "
            "ladder is unbalanced (39.23/17.19/8.53 V).",
            "relative_residual": verification_10ns[
                "relative_residual_at_final_state"
            ],
            "natural_zvs_flags": verification_10ns["natural_zvs_flags"],
            "phases": phase_summary(verification_10ns),
            "safety": verification_10ns["safety"],
        },
        "stability_and_divider_checks": {
            "baseline_and_dead_time_cases": None
            if stability is None
            else [
                {
                    "label": case["label"],
                    "dead_time_s": case["stability"]["dead_time_s"],
                    "module_power_w": case["stability"]["module_power_w"],
                    "relative_residual": case["stability"]["relative_residual"],
                    "natural_zvs_flags": case["stability"]["natural_zvs_flags"],
                    "spectral_radius": case["stability"]["spectral_radius"],
                    "locally_stable": case["stability"]["locally_stable"],
                    "five_largest_eigenvalue_magnitudes": case["stability"][
                        "eigenvalue_magnitudes"
                    ][:5],
                    "divider": case["divider"],
                }
                for case in stability["cases"]
            ],
            "load_190w_case": None
            if stability_190 is None
            else [
                {
                    "label": case["label"],
                    "spectral_radius": case["stability"]["spectral_radius"],
                    "locally_stable": case["stability"]["locally_stable"],
                    "natural_zvs_flags": case["stability"]["natural_zvs_flags"],
                    "five_largest_eigenvalue_magnitudes": case["stability"][
                        "eigenvalue_magnitudes"
                    ][:5],
                    "divider": case["divider"],
                }
                for case in stability_190["cases"]
            ],
        },
        "robustness_sweeps": {
            "any_natural_zvs_anywhere": sweeps["any_natural_zvs_anywhere"],
            "rows": [
                {
                    key: row[key]
                    for key in (
                        "label",
                        "failed",
                        "dead_time_s",
                        "sub_step_s",
                        "switch_on_resistance_ohm",
                        "converged",
                        "final_relative_residual",
                        "natural_zvs_flags",
                        "minimum_abs_vds_v",
                        "phase_current_minima_a",
                        "phase_current_maxima_a",
                        "average_output_v",
                        "flying_capacitor_v",
                        "maximum_abs_phase_current_a",
                        "safety_within_limit",
                        "stage_state_inf_difference_from_reference",
                    )
                    if key in row
                }
                for row in sweeps["rows"]
            ],
        },
        "step_6_safety": {
            "limit_a": search["safety"]["limit_a"],
            "search_maximum_abs_phase_current_a": search["safety"][
                "maximum_abs_phase_current_a"
            ],
            "search_evaluations": search["safety"]["evaluations"],
            "search_within_limit": search["safety"]["within_limit"],
            "final_verification_maximum_abs_phase_current_a": final["safety"][
                "maximum_abs_phase_current_a"
            ],
            "sweeps_maximum_abs_phase_current_a": max(
                row["maximum_abs_phase_current_a"]
                for row in sweeps["rows"]
                if not row["failed"]
            ),
            "all_within_limit": bool(
                search["safety"]["within_limit"]
                and final["safety"]["within_limit"]
                and all(
                    row["safety_within_limit"]
                    for row in sweeps["rows"]
                    if not row["failed"]
                )
            ),
        },
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.output}")
    print(f"outcome = {outcome}")
    print(f"safety all within limit = {payload['step_6_safety']['all_within_limit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
