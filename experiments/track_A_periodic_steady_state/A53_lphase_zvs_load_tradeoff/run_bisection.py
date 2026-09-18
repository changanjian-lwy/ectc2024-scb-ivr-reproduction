"""A53 step 3 -- bisect `LPHASE` at `module_power_w=250` to find the CRITICAL
inductance at which all four phases first achieve natural ZVS.

`BOUNDARY.md` Section 2 step 3.

Two empirical facts, checked before committing to an algorithm (recorded in
`bisection_search.json["diagnostic_probe"]` and repeated in `RESULTS.md`):

1.  A raw, ONE-SHOT evaluation of A37's own fixed seed state (calibrated for
    the NOMINAL `L`) already exceeds the `+/-250 A` safety bound once `L`
    drops anywhere near `~0.6-0.65 nH` -- well before Newton ever runs -- so
    re-seeding every candidate from A37's own fixed values (the way A51's own
    load sweep re-seeds every load from the same seed) is not usable here:
    the seed itself is only valid near the `L` it was measured at.
2.  Warm-starting instead from the PREVIOUS, nearby candidate's own converged
    `z*` (continuation / homotopy) keeps the one-shot evaluation far safer at
    the same `L` (confirmed below `250` A down to `0.5 nH` in the probe).

So this script walks `LPHASE` down from the paper's own nominal value in
small multiplicative steps, each solved by Newton warm-started from the
immediately preceding, already-converged fixed point -- not from A37's raw
seed except at the very first (nominal) point, which reproduces A51's own
already-published result. If a step ever trips the safety bound the step
size is halved and retried (bounded number of times) rather than silently
proceeding; if halving cannot recover, the ladder stops there and the
reached bracket is reported, per `BOUNDARY.md` Section 4's third outcome.

Once the ladder brackets the first all-four-ZVS candidate, a plain bisection
refines it, still continuation-seeded, and applies step-size-convergence
discipline (`sub_step_s` in `{5 ps, 1 ps}`; a third, `2 ps`, rung is added
if those two disagree) to every candidate's own ZVS verdict before it is
used to decide which side of the bracket to keep -- BOUNDARY Section 2
step 3's explicit requirement.

Run:  python3 run_bisection.py --output bisection_search.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np

import a53_boundary as B
import a53_solve as S
import a51_period_map as M

COARSE_STEP_S = 0.0625e-9
DEFAULT_SUB_STEP_S = 5e-12
DISCIPLINE_SUB_STEPS_S = (5e-12, 1e-12)  # + 2e-12 fallback rung, see below
FLOOR_LPHASE_H = 0.4e-9  # abandon the ladder below this, per BOUNDARY Sec 4


def _safety_violation_current(message: str) -> float | None:
    match = re.search(r"\|iL\| = ([0-9.]+) A", message)
    return float(match.group(1)) if match else None


def solve_with_discipline(
    boundary,
    seed_z: np.ndarray,
    *,
    label: str,
    sub_steps_s: tuple[float, ...] = DISCIPLINE_SUB_STEPS_S,
    max_iterations: int = 30,
) -> dict:
    """Solve at `sub_steps_s[0]` (the working resolution), then re-verify the
    ZVS verdict at every other rung.  If any rung disagrees with the first,
    add the missing `2 ps` rung (A50/A51's own usual middle value) and take
    the FINEST rung's verdict as authoritative, exactly as A51's own
    `run_final_verification.py` sub-step ladders do.
    """
    rungs: list[dict] = []
    primary = S.solve_fixed_point(
        boundary,
        seed_z,
        coarse_step_s=COARSE_STEP_S,
        sub_step_s=sub_steps_s[0],
        max_iterations=max_iterations,
        picard_iterations=0,
    )
    rungs.append({"sub_step_s": sub_steps_s[0], "natural_zvs_flags": primary["final_natural_zvs_flags"]})
    disagreement = False
    for sub_step_s in sub_steps_s[1:]:
        check = S.solve_fixed_point(
            boundary,
            primary["z_star"],
            coarse_step_s=COARSE_STEP_S,
            sub_step_s=sub_step_s,
            max_iterations=max_iterations,
            picard_iterations=0,
        )
        rungs.append({"sub_step_s": sub_step_s, "natural_zvs_flags": check["final_natural_zvs_flags"]})
        if check["final_natural_zvs_flags"] != primary["final_natural_zvs_flags"]:
            disagreement = True
    if disagreement and 2e-12 not in sub_steps_s:
        check = S.solve_fixed_point(
            boundary,
            primary["z_star"],
            coarse_step_s=COARSE_STEP_S,
            sub_step_s=2e-12,
            max_iterations=max_iterations,
            picard_iterations=0,
        )
        rungs.append({"sub_step_s": 2e-12, "natural_zvs_flags": check["final_natural_zvs_flags"]})
    finest = min(rungs, key=lambda row: row["sub_step_s"])
    return {
        "label": label,
        "phase_inductance_h": boundary.phase_inductance_h,
        "primary_solve": primary,
        "sub_step_rungs": rungs,
        "sub_step_convergence_disagreement": disagreement,
        "natural_zvs_flags": finest["natural_zvs_flags"],
        "all_four_zvs": all(finest["natural_zvs_flags"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="bisection_search.json")
    parser.add_argument("--module-power-w", type=float, default=250.0)
    parser.add_argument("--ladder-ratio", type=float, default=0.90)
    parser.add_argument("--bisection-relative-tolerance", type=float, default=0.002)
    parser.add_argument("--start-candidate-h", type=float, default=0.5e-9)
    args = parser.parse_args()

    started = time.time()
    module_power_w = args.module_power_w
    events: list[dict] = []
    safety_log: list[dict] = []

    # --- diagnostic probe (reported plainly, Section 3's own "re-verify
    # cheaply" instruction): raw one-shot evaluation of A37's fixed seed
    # across a range of L, WITHOUT any Newton iteration. ---
    probe_rows = []
    for l_nh in (1.4666667, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5):
        l_h = l_nh * 1e-9
        boundary = B.build_boundary(phase_inductance_h=l_h, module_power_w=module_power_w)
        z0, _ = M.a37_seed_state(boundary)
        result = M.evaluate_period_map(
            boundary, z0, coarse_step_s=COARSE_STEP_S, sub_step_s=DEFAULT_SUB_STEP_S
        )
        probe_rows.append(
            {
                "phase_inductance_h": l_h,
                "raw_one_shot_max_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
                "raw_one_shot_natural_zvs_flags": list(result.natural_zvs_flags),
            }
        )
    diagnostic_probe = {
        "description": (
            "one evaluate_period_map call from A37's fixed seed, NOT Newton-"
            "solved, at each L -- shows the seed itself becomes unsafe near "
            "0.6-0.65 nH and motivates continuation seeding below"
        ),
        "rows": probe_rows,
    }

    # --- nominal point: cold-started from A37's own seed, matching A51 ---
    nominal_h = B.NOMINAL_LPHASE_H
    boundary = B.build_boundary(phase_inductance_h=nominal_h, module_power_w=module_power_w)
    z0, _ = M.a37_seed_state(boundary)
    nominal_solve = solve_with_discipline(boundary, z0, label="nominal (A37-seeded)")
    events.append(
        {
            "kind": "nominal",
            "phase_inductance_h": nominal_h,
            "converged": nominal_solve["primary_solve"]["converged"],
            "final_relative_residual": nominal_solve["primary_solve"]["final_relative_residual"],
            "natural_zvs_flags": nominal_solve["natural_zvs_flags"],
            "all_four_zvs": nominal_solve["all_four_zvs"],
            "maximum_abs_phase_current_a": nominal_solve["primary_solve"]["safety"][
                "maximum_abs_phase_current_a"
            ],
            "sub_step_convergence_disagreement": nominal_solve["sub_step_convergence_disagreement"],
        }
    )
    safety_log.append(
        {
            "phase_inductance_h": nominal_h,
            "maximum_abs_phase_current_a": nominal_solve["primary_solve"]["safety"][
                "maximum_abs_phase_current_a"
            ],
            "outcome": "solved",
        }
    )
    print(
        f"[nominal] L={nominal_h*1e9:.4f} nH  converged={events[-1]['converged']}  "
        f"residual={events[-1]['final_relative_residual']:.3e}  "
        f"zvs={events[-1]['natural_zvs_flags']}  "
        f"max|iL|={events[-1]['maximum_abs_phase_current_a']:.2f} A"
    )
    if events[-1]["all_four_zvs"]:
        raise RuntimeError(
            "unexpected: nominal L already shows all-four ZVS; A51's own "
            "published 250 W hard-switch result did not reproduce here"
        )

    # --- continuation ladder: step L down from nominal, warm-started from
    # the previous rung's own converged z*. ---
    ladder: list[dict] = []
    current_h = nominal_h
    current_z = nominal_solve["primary_solve"]["z_star"]
    ratio = args.ladder_ratio
    crossing_low = None  # first candidate (smallest L reached) with all-4 ZVS
    crossing_high = current_h  # largest L confirmed WITHOUT all-4 ZVS
    crossing_low_z = None
    widened_past_start_candidate = False
    while current_h > FLOOR_LPHASE_H:
        if current_h <= args.start_candidate_h * 1.001 and not widened_past_start_candidate:
            widened_past_start_candidate = True
            print(
                f"  [ladder] reached the proposed starting candidate "
                f"{args.start_candidate_h*1e9:.4f} nH with no crossing yet -- "
                f"widening the bracket downward per BOUNDARY.md Section 2 "
                f"step 3, continuing to the {FLOOR_LPHASE_H*1e9:.4f} nH floor"
            )
        target_h = current_h * ratio
        attempt_ratio = ratio
        attempts = 0
        solved_this_rung = False
        while attempts < 6:
            attempts += 1
            boundary = B.build_boundary(phase_inductance_h=target_h, module_power_w=module_power_w)
            try:
                outcome = solve_with_discipline(boundary, current_z, label=f"ladder h={target_h:.4e}")
            except RuntimeError as error:
                peak = _safety_violation_current(str(error))
                safety_log.append(
                    {
                        "phase_inductance_h": target_h,
                        "maximum_abs_phase_current_a": peak,
                        "outcome": "SAFETY_VIOLATION_AVOIDED",
                        "note": str(error),
                    }
                )
                print(
                    f"  [ladder] L={target_h*1e9:.4f} nH  SAFETY VIOLATION "
                    f"(|iL|~{peak} A) -- halving step and retrying"
                )
                attempt_ratio = 1 - (1 - attempt_ratio) / 2
                target_h = current_h * attempt_ratio
                continue
            solved_this_rung = True
            break
        if not solved_this_rung:
            ladder.append(
                {
                    "phase_inductance_h": target_h,
                    "outcome": "ABANDONED_AFTER_REPEATED_SAFETY_VIOLATIONS",
                }
            )
            print(
                f"  [ladder] stopping: could not find a safe step below "
                f"L={current_h*1e9:.4f} nH after 6 halvings"
            )
            break
        maxi = outcome["primary_solve"]["safety"]["maximum_abs_phase_current_a"]
        safety_log.append(
            {"phase_inductance_h": target_h, "maximum_abs_phase_current_a": maxi, "outcome": "solved"}
        )
        row = {
            "phase_inductance_h": target_h,
            "step_ratio_used": attempt_ratio,
            "attempts": attempts,
            "converged": outcome["primary_solve"]["converged"],
            "final_relative_residual": outcome["primary_solve"]["final_relative_residual"],
            "natural_zvs_flags": outcome["natural_zvs_flags"],
            "all_four_zvs": outcome["all_four_zvs"],
            "maximum_abs_phase_current_a": maxi,
            "sub_step_convergence_disagreement": outcome["sub_step_convergence_disagreement"],
        }
        ladder.append(row)
        print(
            f"  [ladder] L={target_h*1e9:.4f} nH  converged={row['converged']}  "
            f"residual={row['final_relative_residual']:.3e}  "
            f"zvs={row['natural_zvs_flags']}  max|iL|={maxi:.2f} A"
        )
        current_h = target_h
        current_z = outcome["primary_solve"]["z_star"]
        if row["all_four_zvs"]:
            crossing_low = target_h
            crossing_low_z = current_z
            break
        else:
            crossing_high = target_h

    events.append({"kind": "ladder", "rows": ladder})

    if crossing_low is None:
        payload = {
            "script": Path(__file__).name,
            "classification": "SENSITIVITY_ONLY",
            "outcome": "NO_CROSSING_FOUND_IN_BRACKET",
            "module_power_w": module_power_w,
            "proposed_start_candidate_h": args.start_candidate_h,
            "floor_lphase_h": FLOOR_LPHASE_H,
            "bracket_was_widened_past_proposed_start": widened_past_start_candidate,
            "diagnostic_probe": diagnostic_probe,
            "nominal": events[0],
            "ladder": ladder,
            "safety_log": safety_log,
            "wall_clock_s": time.time() - started,
        }
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
        print(f"\nwrote {args.output} -- NO CROSSING FOUND; reported bracket only")
        return 0

    # --- bisection refine between crossing_high (all-4 ZVS False) and
    # crossing_low (all-4 ZVS True), continuation-seeded from whichever
    # endpoint is nearer. ---
    bisection: list[dict] = []
    low_h, low_z = crossing_low, crossing_low_z
    high_h = crossing_high
    # Every bisection midpoint is warm-started from `low_z`, the nearest
    # already-converged, ALL-FOUR-ZVS (hence known-safe, per the diagnostic
    # probe) state on record -- continuation only needs *a* nearby converged
    # state to seed Newton, not specifically the opposite bracket endpoint.
    iteration = 0
    while (high_h - low_h) / nominal_h > args.bisection_relative_tolerance:
        iteration += 1
        mid_h = 0.5 * (low_h + high_h)
        boundary = B.build_boundary(phase_inductance_h=mid_h, module_power_w=module_power_w)
        seed = low_z  # warm-start from the nearer, already-safe, converged point
        try:
            outcome = solve_with_discipline(boundary, seed, label=f"bisect[{iteration}] h={mid_h:.4e}")
        except RuntimeError as error:
            peak = _safety_violation_current(str(error))
            safety_log.append(
                {
                    "phase_inductance_h": mid_h,
                    "maximum_abs_phase_current_a": peak,
                    "outcome": "SAFETY_VIOLATION_AVOIDED_BISECTION",
                }
            )
            print(f"  [bisect {iteration}] L={mid_h*1e9:.4f} nH SAFETY VIOLATION -- treating as non-ZVS side")
            high_h = mid_h
            bisection.append(
                {
                    "iteration": iteration,
                    "phase_inductance_h": mid_h,
                    "outcome": "SAFETY_VIOLATION",
                    "treated_as": "high_side (non-ZVS)",
                }
            )
            continue
        maxi = outcome["primary_solve"]["safety"]["maximum_abs_phase_current_a"]
        safety_log.append(
            {"phase_inductance_h": mid_h, "maximum_abs_phase_current_a": maxi, "outcome": "solved"}
        )
        row = {
            "iteration": iteration,
            "phase_inductance_h": mid_h,
            "converged": outcome["primary_solve"]["converged"],
            "final_relative_residual": outcome["primary_solve"]["final_relative_residual"],
            "natural_zvs_flags": outcome["natural_zvs_flags"],
            "all_four_zvs": outcome["all_four_zvs"],
            "maximum_abs_phase_current_a": maxi,
            "sub_step_convergence_disagreement": outcome["sub_step_convergence_disagreement"],
        }
        bisection.append(row)
        print(
            f"  [bisect {iteration}] L={mid_h*1e9:.4f} nH  converged={row['converged']}  "
            f"residual={row['final_relative_residual']:.3e}  zvs={row['natural_zvs_flags']}  "
            f"max|iL|={maxi:.2f} A"
        )
        if row["all_four_zvs"]:
            # `mid_h` is on the ZVS-achieving side; the still-unknown crossing
            # lies between `mid_h` and `high_h`, so raise the known-safe
            # lower bound to `mid_h` (and keep it as the next warm-start seed).
            low_h = mid_h
            low_z = outcome["primary_solve"]["z_star"]
        else:
            # `mid_h` still hard-switches; the crossing lies between `low_h`
            # and `mid_h`, so lower the known-hard-switch upper bound.
            high_h = mid_h

    critical_h = low_h  # smallest L confirmed all-4 ZVS at converged tolerance
    critical_z = low_z

    # --- margin point: 10% further below critical, continuation-seeded from
    # critical's own converged z* (BOUNDARY Sec 2 step 4's proposed margin).
    margin_h = 0.9 * critical_h
    margin_boundary = B.build_boundary(phase_inductance_h=margin_h, module_power_w=module_power_w)
    margin_outcome = solve_with_discipline(margin_boundary, critical_z, label="margin (10% below critical)")
    margin_z = margin_outcome["primary_solve"]["z_star"]
    margin_maxi = margin_outcome["primary_solve"]["safety"]["maximum_abs_phase_current_a"]
    safety_log.append(
        {"phase_inductance_h": margin_h, "maximum_abs_phase_current_a": margin_maxi, "outcome": "solved"}
    )
    print(
        f"\n[margin] L={margin_h*1e9:.4f} nH  converged={margin_outcome['primary_solve']['converged']}  "
        f"residual={margin_outcome['primary_solve']['final_relative_residual']:.3e}  "
        f"zvs={margin_outcome['natural_zvs_flags']}  max|iL|={margin_maxi:.2f} A"
    )
    if not margin_outcome["all_four_zvs"]:
        print(
            "  WARNING: the proposed 10%-below-critical margin point does NOT "
            "show all-four ZVS at this sub-step discipline -- reported plainly, "
            "not silently adjusted."
        )

    # Persist the three key converged states (nominal / critical / margin) so
    # `run_three_point_analysis.py` can warm-start from them directly instead
    # of re-deriving each from A37's own raw seed (which the diagnostic probe
    # above shows is unsafe well before reaching the critical/margin region).
    key_states = {
        "nominal": {
            "phase_inductance_h": nominal_h,
            "z_star": nominal_solve["primary_solve"]["z_star"].tolist(),
        },
        "critical": {
            "phase_inductance_h": critical_h,
            "z_star": critical_z.tolist(),
        },
        "margin": {
            "phase_inductance_h": margin_h,
            "z_star": margin_z.tolist(),
            "all_four_zvs_at_search_discipline": margin_outcome["all_four_zvs"],
        },
    }
    Path("key_states.json").write_text(json.dumps(key_states, indent=2) + "\n")

    payload = {
        "script": Path(__file__).name,
        "classification": "SENSITIVITY_ONLY",
        "outcome": "CRITICAL_LPHASE_FOUND",
        "module_power_w": module_power_w,
        "nominal_lphase_h": nominal_h,
        "diagnostic_probe": diagnostic_probe,
        "nominal": events[0],
        "ladder": ladder,
        "bisection": bisection,
        "critical_lphase_h": critical_h,
        "critical_lphase_bracket_h": [low_h, high_h],
        "reduction_from_nominal_pct": 100.0 * (1 - critical_h / nominal_h),
        "proposed_start_candidate_h": args.start_candidate_h,
        "bracket_was_widened_past_proposed_start": widened_past_start_candidate,
        "margin_lphase_h": margin_h,
        "margin_reduction_from_nominal_pct": 100.0 * (1 - margin_h / nominal_h),
        "margin_natural_zvs_flags": margin_outcome["natural_zvs_flags"],
        "margin_all_four_zvs": margin_outcome["all_four_zvs"],
        "margin_final_relative_residual": margin_outcome["primary_solve"]["final_relative_residual"],
        "key_states_file": "key_states.json",
        "safety_log": safety_log,
        "safety_limit_a": M.PHASE_CURRENT_LIMIT_A,
        "safety_maximum_over_whole_search_a": max(
            (row["maximum_abs_phase_current_a"] for row in safety_log if row["maximum_abs_phase_current_a"] is not None),
            default=None,
        ),
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nwrote {args.output}  ({payload['wall_clock_s']:.1f} s)")
    print(f"critical LPHASE ~ {critical_h*1e9:.5f} nH ({payload['reduction_from_nominal_pct']:.2f}% below nominal)")
    print(f"bracket: [{low_h*1e9:.5f}, {high_h*1e9:.5f}] nH")
    print(
        f"safety: max |iL| over whole search = "
        f"{payload['safety_maximum_over_whole_search_a']} A (limit {M.PHASE_CURRENT_LIMIT_A} A)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
