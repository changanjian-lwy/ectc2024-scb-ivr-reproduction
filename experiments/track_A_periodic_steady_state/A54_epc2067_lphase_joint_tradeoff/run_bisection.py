"""A54 step 3 -- bisect `LPHASE` at `module_power_w=250` to find the CRITICAL
inductance at which all four phases first achieve natural ZVS, under
EPC2067's own device parameters (`CH=3720 pF`, `CL=5580 pF`).

`BOUNDARY.md` Section 3 step 3. Structurally identical to `A53`'s own
`run_bisection.py` (same continuation/homotopy method, same diagnostic-probe
discipline, same sub-step-ladder ZVS-verdict rigor) -- this is a NEW file in
this experiment's own directory, not an edit to A53's file. `a53_solve.py`'s
`solve_fixed_point`/generic search machinery is device-agnostic (verified: it
takes a `boundary` object and never references any device parameter by name),
so it is imported READ-ONLY via `sys.path` from A53's own directory, exactly
the same discipline already used for A51's `a51_period_map.py`. Only the
boundary construction (`a54_boundary.build_boundary`, EPC2067's own device
parameters) differs from A53.

Two empirical facts, checked before committing to an algorithm (recorded in
`bisection_search.json["diagnostic_probe"]` and repeated in `RESULTS.md`):

1.  A raw, ONE-SHOT evaluation of A37's own fixed seed state (calibrated for
    the NOMINAL `L`) already exceeds the `+/-250 A` safety bound once `L`
    drops below roughly `0.6-0.7 nH` -- close to A53's own GS61008T finding
    (`~0.6-0.65 nH`), confirming this raw-seed instability is driven by the
    INDUCTANCE dynamics, not by the switch capacitance, so the same
    continuation strategy applies here.
2.  Warm-starting from the PREVIOUS, nearby candidate's own converged `z*`
    (continuation / homotopy) is therefore required below that point, exactly
    as A53 already established.

Given `BOUNDARY.md`'s own `~3x`-higher-threshold estimate from the
capacitance increase, `FLOOR_LPHASE_H` is set well below A53's own `0.4 nH`
floor -- the actual crossing point is not known in advance and must be
searched for, widening the bracket as needed (this script's own ladder loop
already does this automatically, printing a note when it passes the
originally-proposed starting candidate, per `BOUNDARY.md` Section 3 step 3's
explicit allowance).

Run:  python3 run_bisection.py --output bisection_search.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A53_DIR = HERE.parent / "A53_lphase_zvs_load_tradeoff"
if str(A53_DIR) not in sys.path:
    sys.path.insert(0, str(A53_DIR))

import a54_boundary as B  # noqa: E402
import a53_solve as S  # noqa: E402  (A53's own generic, device-agnostic solve machinery, read-only)
import a51_period_map as M  # noqa: E402

COARSE_STEP_S = 0.0625e-9
DEFAULT_SUB_STEP_S = 5e-12
DISCIPLINE_SUB_STEPS_S = (5e-12, 1e-12)  # + 2e-12 fallback rung, see below
FLOOR_LPHASE_H = 0.08e-9  # abandon the ladder below this -- see module docstring


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
    ZVS verdict at every other rung. If any rung disagrees with the first,
    add the missing `2 ps` rung and take the FINEST rung's verdict as
    authoritative, exactly as A53's own `run_bisection.py` does.
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

    # --- diagnostic probe: raw one-shot evaluation of A37's fixed seed
    # across a range of L, WITHOUT any Newton iteration, at EPC2067's own
    # device parameters. ---
    probe_rows = []
    for l_nh in (1.4666667, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5, 0.4, 0.3, 0.2):
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
            "solved, at each L, under EPC2067's own device parameters -- "
            "shows the seed itself becomes unsafe near the same 0.6-0.7 nH "
            "region A53 already found with GS61008T (confirming this is "
            "driven by the inductance dynamics, not the switch capacitance), "
            "and motivates continuation seeding below"
        ),
        "rows": probe_rows,
    }

    # --- nominal point: cold-started from A37's own seed ---
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
            "unexpected: nominal L already shows all-four ZVS with EPC2067's "
            "own device parameters -- BOUNDARY.md Section 3 step 2's own "
            "'confirm, not assume' hard-switch check failed"
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
                f"widening the bracket downward per BOUNDARY.md Section 3 "
                f"step 3's own explicit allowance, continuing to the "
                f"{FLOOR_LPHASE_H*1e9:.4f} nH floor"
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
    # crossing_low (all-4 ZVS True), continuation-seeded from the known-safe
    # ZVS-side endpoint. ---
    bisection: list[dict] = []
    low_h, low_z = crossing_low, crossing_low_z
    high_h = crossing_high
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
            low_h = mid_h
            low_z = outcome["primary_solve"]["z_star"]
        else:
            high_h = mid_h

    critical_h = low_h  # smallest L confirmed all-4 ZVS at converged tolerance
    critical_z = low_z

    # --- margin point: 10% further below critical, continuation-seeded from
    # critical's own converged z*.
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
        "floor_lphase_h": FLOOR_LPHASE_H,
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
