"""A51 steps 3, 4 and 6 - search for `z* = F(z*)` from A37's own best candidate.

`BOUNDARY.md` Section 4.3 leaves the choice of iteration to engineering
judgment.  The method used here is a **semi-smooth (policy) Newton** iteration,
chosen for one concrete reason: with the event structure held fixed (which phase
admits its high side at which sub-step, and likewise each low side), the model is
linear and time-invariant, so `F` is EXACTLY affine on that branch.  A single
Newton step with a finite-difference Jacobian therefore lands exactly on that
branch's own fixed point; the only thing that can go wrong is the event
structure changing, which is detected and the Jacobian rebuilt.  Damped Picard
is also run, from the same seed and reported alongside, as an independent check
that the Newton answer is not an artifact of the linear solve.

The Jacobian is rank-deficient (A50's own gate 1 already reported rank 17 of 20
for the ideal affine period map), so `(J - I) d = -(F(z) - z)` is solved in the
least-squares / minimum-norm sense, and the part of the residual that lies
OUTSIDE the range of `(J - I)` -- i.e. the part no Newton step can remove -- is
reported separately rather than hidden.

Safety (`BOUNDARY.md` Section 6, last bullet): every phase current is checked
against +/-250 A at EVERY sub-step of EVERY `F` evaluation, including the
finite-difference probes and the line search, not only at the accepted iterates.

Run:  python3 run_fixed_point_search.py --output fixed_point_search.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import a51_period_map as M

#: The three precharge-divider tap voltages.  See the Newton loop for why they
#: are held fixed rather than solved for.
PINNED = ("tap3", "tap2", "tap1")


def _safety(result: M.PeriodResult, label: str, log: list[dict]) -> None:
    monitor = result.monitor
    assert monitor is not None
    log.append(
        {
            "label": label,
            "maximum_abs_phase_current_a": monitor.maximum_abs_phase_current_a,
            "argmax_phase": monitor.argmax_phase,
            "argmax_time_s": monitor.argmax_time_s,
            "maximum_abs_input_current_a": monitor.maximum_abs_input_current_a,
            "maximum_off_diode_forward_voltage_v": (
                monitor.maximum_off_diode_forward_voltage_v
            ),
            "maximum_relative_backward_error": monitor.maximum_relative_backward_error,
        }
    )
    if monitor.maximum_abs_phase_current_a > M.PHASE_CURRENT_LIMIT_A:
        raise RuntimeError(
            f"SAFETY BOUND VIOLATED at {label}: "
            f"|iL| = {monitor.maximum_abs_phase_current_a:.4f} A > "
            f"{M.PHASE_CURRENT_LIMIT_A} A"
        )


def event_signature(result: M.PeriodResult) -> tuple:
    """A hashable summary of which branch of the piecewise-affine map was taken."""
    return (
        tuple(
            (verdict.phase_index, verdict.natural_zvs, round(verdict.switch_on_delay_s, 13))
            for verdict in result.turn_on
        ),
        tuple(
            (verdict.phase_index, verdict.natural, round(verdict.switch_on_time_s, 13))
            for verdict in result.turn_off
        ),
    )


def verdict_records(result: M.PeriodResult) -> dict:
    return {
        "turn_on": [
            {
                "phase": verdict.phase_index + 1,
                "natural_zvs": verdict.natural_zvs,
                "minimum_abs_vds_v": verdict.minimum_abs_vds_v,
                "minimum_signed_vds_v": verdict.minimum_signed_vds_v,
                "initial_vds_v": verdict.initial_vds_v,
                "free_resonance_vds_at_window_end_v": verdict.vds_at_window_end_v,
                "hard_switch_residual_v": verdict.hard_switch_residual_v,
                "sign_change_time_s": verdict.sign_change_time_s,
                "switch_on_delay_s": verdict.switch_on_delay_s,
                "phase_current_at_crossing_a": verdict.phase_current_at_crossing_a,
            }
            for verdict in result.turn_on
        ],
        "turn_off": [
            {
                "phase": verdict.phase_index + 1,
                "natural": verdict.natural,
                "minimum_signed_switch_node_v": verdict.minimum_signed_switch_node_v,
                "sign_change_time_s": verdict.sign_change_time_s,
                "hard_switch_residual_v": verdict.hard_switch_residual_v,
            }
            for verdict in result.turn_off
        ],
    }


def run_picard(
    boundary,
    z0,
    *,
    coarse_step_s: float,
    sub_step_s: float,
    damping: float,
    iterations: int,
    safety_log: list[dict],
) -> dict:
    z = z0.copy()
    history = []
    for iteration in range(1, iterations + 1):
        result = M.evaluate_period_map(
            boundary, z, coarse_step_s=coarse_step_s, sub_step_s=sub_step_s
        )
        _safety(result, f"picard[{iteration}]", safety_log)
        residual = result.z_next - z
        history.append(
            {
                "iteration": iteration,
                "relative_residual": M.relative_residual(z, result.z_next),
                "absolute_residual_inf": float(np.linalg.norm(residual, ord=np.inf)),
                "natural_zvs_flags": list(result.natural_zvs_flags),
                "maximum_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
            }
        )
        z = z + damping * residual
    return {"damping": damping, "iterations": iterations, "history": history, "final_state": z.tolist()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="fixed_point_search.json")
    parser.add_argument("--max-iterations", type=int, default=50)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--coarse-step-ns", type=float, default=0.0625)
    parser.add_argument("--sub-step-ps", type=float, default=5.0)
    parser.add_argument("--dead-time-ns", type=float, default=M.DEAD_TIME_S * 1e9)
    parser.add_argument("--picard-iterations", type=int, default=25)
    parser.add_argument("--picard-damping", type=float, default=0.5)
    parser.add_argument(
        "--rcond",
        type=float,
        default=1e-10,
        help="least-squares singular-value cutoff, relative to the largest",
    )
    parser.add_argument(
        "--module-power-w",
        type=float,
        default=250.0,
        help="one module's nominal load power; sets `load_resistance = Vout^2/P`",
    )
    parser.add_argument(
        "--switch-on-resistance-ohm",
        type=float,
        default=1e-6,
        help="single global switch on-resistance (the framework cannot split "
        "A42's RHS=7mOhm / RLS=3.5mOhm)",
    )
    parser.add_argument(
        "--tap-voltages",
        default="",
        help="comma-separated tap3,tap2,tap1 override (default: equal-series 36/24/12)",
    )
    args = parser.parse_args()

    coarse_step_s = args.coarse_step_ns * 1e-9
    sub_step_s = args.sub_step_ps * 1e-12
    boundary = M.build_boundary(
        dead_time_s=args.dead_time_ns * 1e-9,
        switch_on_resistance_ohm=args.switch_on_resistance_ohm,
        module_power_w=args.module_power_w,
    )
    names = M.variable_names(boundary)
    z0, seed_rows = M.a37_seed_state(boundary)
    if args.tap_voltages:
        override = [float(value) for value in args.tap_voltages.split(",")]
        for name, value in zip(PINNED, override):
            z0[names.index(name)] = value
    started = time.time()
    safety_log: list[dict] = []
    evaluations = 0

    def evaluate(state, label):
        nonlocal evaluations
        evaluations += 1
        result = M.evaluate_period_map(
            boundary, state, coarse_step_s=coarse_step_s, sub_step_s=sub_step_s
        )
        _safety(result, label, safety_log)
        return result

    # ---------------- semi-smooth Newton ----------------
    z = z0.copy()
    result = evaluate(z, "newton[0]")
    residual = result.z_next - z
    signature = event_signature(result)
    jacobian = None
    jacobian_signature = None
    jacobian_rebuilds = 0
    history: list[dict] = []
    converged = False
    stalled_reason = None

    # Finite-difference increments, one scale per variable class.
    increment = np.empty(len(names), dtype=float)
    for position, name in enumerate(names):
        increment[position] = 1e-4 if name.startswith("L") or name == "I_VSTEP" else 1e-4
    increment[names.index("LPAR_IN")] = 1e-4

    for iteration in range(1, args.max_iterations + 1):
        relative = M.relative_residual(z, result.z_next)
        absolute = float(np.linalg.norm(residual, ord=np.inf))
        record = {
            "iteration": iteration,
            "relative_residual": relative,
            "absolute_residual_inf": absolute,
            "absolute_residual_by_variable": {
                name: float(value) for name, value in zip(names, residual)
            },
            "natural_zvs_flags": list(result.natural_zvs_flags),
            "maximum_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
            "event_signature_changed": signature != jacobian_signature,
        }
        if relative <= args.tolerance:
            record["status"] = "converged"
            history.append(record)
            converged = True
            break

        if jacobian is None or signature != jacobian_signature:
            jacobian = np.empty((len(names), len(names)), dtype=float)
            for column in range(len(names)):
                probe = z.copy()
                probe[column] += increment[column]
                probe_result = evaluate(probe, f"jacobian[{iteration}][{column}]")
                jacobian[:, column] = (probe_result.z_next - result.z_next) / increment[column]
            jacobian_signature = signature
            jacobian_rebuilds += 1
            record["jacobian_rebuilt"] = True
        else:
            record["jacobian_rebuilt"] = False

        full_matrix = jacobian - np.eye(len(names))
        record["full_singular_values"] = [
            float(value) for value in np.linalg.svd(full_matrix, compute_uv=False)
        ]
        # `BOUNDARY.md` Section 4.3 / A50 gate 1's own "nullity 3": the three
        # precharge-divider tap voltages are a genuine three-dimensional
        # continuum of fixed points (`F` is the identity on them to ~1e-9 per
        # period, measured -- see `--report-tap-degeneracy`).  Leaving them in
        # the least-squares solve divides the residual by those ~1e-9 singular
        # values and throws the taps to physically meaningless voltages while
        # changing nothing electrically.  They are therefore held at their
        # seeded equal-series values and excluded from the unknowns; the
        # resulting precharge-diode margin is audited afterwards.
        free = [position for position, name in enumerate(names) if name not in PINNED]
        matrix = full_matrix[:, free]
        step_free, _, rank, singular_values = np.linalg.lstsq(
            matrix, -residual, rcond=args.rcond
        )
        step = np.zeros(len(names), dtype=float)
        step[free] = step_free
        unreachable = matrix @ step_free + residual
        record["pinned_variables"] = sorted(PINNED)
        record["jacobian_rank"] = int(rank)
        record["jacobian_nullity"] = int(len(free) - rank)
        record["unreachable_residual_inf"] = float(
            np.linalg.norm(unreachable, ord=np.inf)
        )
        record["newton_step_inf"] = float(np.linalg.norm(step, ord=np.inf))
        record["singular_value_extremes"] = [
            float(singular_values.max()),
            float(singular_values.min()),
        ]

        best = None
        for damping in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125):
            trial_z = z + damping * step
            trial_result = evaluate(trial_z, f"linesearch[{iteration}][{damping}]")
            trial_relative = M.relative_residual(trial_z, trial_result.z_next)
            if best is None or trial_relative < best[1]:
                best = (damping, trial_relative, trial_z, trial_result)
            if trial_relative < relative:
                break
        damping, trial_relative, trial_z, trial_result = best  # type: ignore[misc]
        record["accepted_damping"] = damping
        record["next_relative_residual"] = trial_relative
        history.append(record)

        if trial_relative >= relative and damping <= 0.03125:
            stalled_reason = (
                "no damping factor down to 1/32 reduced the residual; the "
                "iteration is at a non-smooth point of F or at its numerical floor"
            )
            z, result = trial_z, trial_result
            residual = result.z_next - z
            signature = event_signature(result)
            break

        z, result = trial_z, trial_result
        residual = result.z_next - z
        signature = event_signature(result)
    else:
        stalled_reason = "iteration budget exhausted"

    final_relative = M.relative_residual(z, result.z_next)
    if not converged and final_relative <= args.tolerance:
        converged = True

    # --------- measured identification of A50's own "nullity 3" ---------
    # Perturbing each tap by 1 V and propagating one period quantifies directly
    # how close `F` is to the identity on the tap subspace, and how little the
    # taps touch the stage -- i.e. whether pinning them was justified.
    stage_positions = [
        position for position, name in enumerate(names) if name not in PINNED
    ]
    tap_degeneracy = {"perturbation_v": 1.0, "rows": []}
    for name in PINNED:
        probe = z.copy()
        probe[names.index(name)] += 1.0
        probe_result = evaluate(probe, f"tap_degeneracy[{name}]")
        delta = probe_result.z_next - result.z_next
        tap_degeneracy["rows"].append(
            {
                "tap": name,
                "d_same_tap_per_period_v": float(delta[names.index(name)]),
                "identity_defect_v": float(delta[names.index(name)] - 1.0),
                "maximum_effect_on_stage_variables_v": float(
                    np.max(np.abs(delta[stage_positions]))
                ),
            }
        )

    diode_audit = {
        "frozen_diode_state": [False, False, False],
        "diode_off_resistance_ohm": boundary.diode_off_resistance_ohm,
        "maximum_off_diode_forward_voltage_v": (
            result.monitor.maximum_off_diode_forward_voltage_v
        ),
        "implied_maximum_branch_current_a": (
            result.monitor.maximum_off_diode_forward_voltage_v
            / boundary.diode_off_resistance_ohm
        ),
        "implied_maximum_charge_per_period_c": (
            result.monitor.maximum_off_diode_forward_voltage_v
            / boundary.diode_off_resistance_ohm
            * boundary.period_s
        ),
        "tap_voltages_v": [float(z[names.index(name)]) for name in PINNED],
    }

    orbit = {
        "minimum_phase_currents_a": list(result.monitor.phase_minimum_a),
        "maximum_phase_currents_a": list(result.monitor.phase_maximum_a),
        "average_output_v": (
            result.monitor.weighted_sum["out"] / result.monitor.weighted_duration_s
        ),
        "average_input_inductor_current_a": (
            result.monitor.weighted_sum["LPAR_IN"] / result.monitor.weighted_duration_s
        ),
        "average_flying_capacitor_v": [
            (
                result.monitor.weighted_sum[f"a{number}"]
                - result.monitor.weighted_sum[f"x{number}"]
            )
            / result.monitor.weighted_duration_s
            for number in (1, 2, 3)
        ],
        "flying_capacitor_v_at_z_star": [
            float(z[names.index(f"a{number}")] - z[names.index(f"x{number}")])
            for number in (1, 2, 3)
        ],
        "average_load_power_w": (
            (result.monitor.weighted_sum["out"] / result.monitor.weighted_duration_s) ** 2
            / boundary.load_resistance_ohm
        ),
    }

    # ---------------- damped Picard, same seed, independent check ----------------
    picard = run_picard(
        boundary,
        z0,
        coarse_step_s=coarse_step_s,
        sub_step_s=sub_step_s,
        damping=args.picard_damping,
        iterations=args.picard_iterations,
        safety_log=safety_log,
    )

    maximum_current = max(entry["maximum_abs_phase_current_a"] for entry in safety_log)
    worst = max(safety_log, key=lambda entry: entry["maximum_abs_phase_current_a"])

    payload = {
        "script": Path(__file__).name,
        "boundary": {
            "vin_v": boundary.vin_target_v,
            "vout_v": boundary.vout_target_v,
            "module_power_w": boundary.module_power_w,
            "switching_frequency_hz": boundary.switching_frequency_hz,
            "period_s": boundary.period_s,
            "on_time_s": boundary.on_time_s,
            "phase_inductance_h": boundary.phase_inductance_h,
            "flying_capacitances_f": list(boundary.flying_capacitances_f),
            "dead_time_s": boundary.dead_time_s,
            "switch_on_resistance_ohm": boundary.switch_on_resistance_ohm,
            "switch_high_total_f": boundary.switch_capacitance.high_total_f,
            "switch_low_total_f": boundary.switch_capacitance.low_total_f,
            "divider_enabled": boundary.divider_enabled,
            "period_start_s": M.period_start_s(boundary),
            "base_period_index": M.BASE_PERIOD_INDEX,
        },
        "numerics": {
            "coarse_step_s": coarse_step_s,
            "sub_step_s": sub_step_s,
            "tolerance_relative": args.tolerance,
            "max_iterations": args.max_iterations,
        },
        "variable_names": list(names),
        "seed_conversion": seed_rows,
        "seed_state": z0.tolist(),
        "newton": {
            "history": history,
            "iterations_used": len(history),
            "jacobian_rebuilds": jacobian_rebuilds,
            "converged": converged,
            "stalled_reason": stalled_reason,
            "final_state": z.tolist(),
            "final_image": result.z_next.tolist(),
            "final_relative_residual": final_relative,
            "final_absolute_residual_inf": float(
                np.linalg.norm(result.z_next - z, ord=np.inf)
            ),
            "final_verdicts": verdict_records(result),
            "final_natural_zvs_flags": list(result.natural_zvs_flags),
            "final_orbit_metrics": orbit,
        },
        "tap_degeneracy": tap_degeneracy,
        "precharge_diode_audit": diode_audit,
        "picard": picard,
        "safety": {
            "limit_a": M.PHASE_CURRENT_LIMIT_A,
            "evaluations": evaluations + args.picard_iterations,
            "maximum_abs_phase_current_a": maximum_current,
            "worst_evaluation": worst,
            "within_limit": bool(maximum_current <= M.PHASE_CURRENT_LIMIT_A),
        },
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {args.output}  ({payload['wall_clock_s']:.1f} s, {evaluations} F-evals)")
    print("\nNewton residual history (relative |F(z)-z|_inf / max(|z|_inf,1)):")
    for record in history:
        print(
            f"  it {record['iteration']:>3}  rel={record['relative_residual']:.6e}"
            f"  abs={record['absolute_residual_inf']:.6e}"
            f"  zvs={record['natural_zvs_flags']}"
            f"  rank={record.get('jacobian_rank', '-')}"
            f"  unreach={record.get('unreachable_residual_inf', float('nan')):.3e}"
            f"  alpha={record.get('accepted_damping', '-')}"
        )
    print(f"\nconverged = {converged}   reason = {stalled_reason}")
    print(f"final relative residual = {final_relative:.6e}")
    print(f"final natural-ZVS flags = {list(result.natural_zvs_flags)}")
    print("\nPicard (damping %.2f):" % args.picard_damping)
    for record in picard["history"][:: max(1, len(picard["history"]) // 10 or 1)]:
        print(
            f"  it {record['iteration']:>3}  rel={record['relative_residual']:.6e}"
            f"  zvs={record['natural_zvs_flags']}"
        )
    print("\ntap degeneracy (1 V perturbation propagated one period):")
    for row in tap_degeneracy["rows"]:
        print(
            f"  {row['tap']}: identity defect = {row['identity_defect_v']:+.3e} V,"
            f"  max effect on any stage variable = "
            f"{row['maximum_effect_on_stage_variables_v']:.3e} V"
        )
    print(
        f"precharge diodes (frozen off): max forward = "
        f"{diode_audit['maximum_off_diode_forward_voltage_v']:.6f} V"
        f"  -> {diode_audit['implied_maximum_branch_current_a']:.3e} A,"
        f" {diode_audit['implied_maximum_charge_per_period_c']:.3e} C per period"
    )
    print("\nfinal orbit metrics:")
    print(f"  phase current minima = {orbit['minimum_phase_currents_a']}")
    print(f"  phase current maxima = {orbit['maximum_phase_currents_a']}")
    print(f"  average output = {orbit['average_output_v']:.6f} V,"
          f" load power = {orbit['average_load_power_w']:.4f} W")
    print(f"  flying-capacitor voltages at z* = {orbit['flying_capacitor_v_at_z_star']}")
    print(
        f"\nsafety: max |iL| = {maximum_current:.4f} A over "
        f"{payload['safety']['evaluations']} evaluations "
        f"(limit {M.PHASE_CURRENT_LIMIT_A} A) -> within = {payload['safety']['within_limit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
