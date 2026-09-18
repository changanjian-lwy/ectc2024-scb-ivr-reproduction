"""A53 - fixed-point search core, and RMS-current period evaluation.

`BOUNDARY.md` Section 2 steps 2-4.

Two things this file provides that A51's own `a51_period_map.py` /
`run_fixed_point_search.py` do not, and why each needs its own new code
rather than an edit to A51's files:

1. `solve_fixed_point()` -- A51's own semi-smooth Newton + damped-Picard
   search (`run_fixed_point_search.py`) is written entirely inside that
   script's own `main()`, not factored into an importable function (checked
   by reading it). This is the SAME algorithm -- finite-difference Jacobian
   on the 20-variable descriptor with the three precharge-divider taps
   pinned (A50's own measured "nullity 3"), rank-deficient least-squares
   Newton step, backtracking line search, an event-signature cache that
   rebuilds the Jacobian only when the piecewise-affine branch changes, and
   a damped-Picard cross-check from the same seed -- re-expressed here as a
   function so both the bisection driver and the three-point analysis can
   call it directly instead of shelling out. Every low-level call
   (`M.evaluate_period_map`, `M.relative_residual`, `M.a37_seed_state`) is
   A51's own, imported read-only.

2. `evaluate_period_map_with_rms()` -- A51's own `evaluate_period_map` builds
   its `Monitor` INTERNALLY (`monitor = Monitor(index=index)`, hardcoded) and
   returns only running min/max per phase, not a time-integral, so RMS
   current cannot be obtained by calling it as-is. `Monitor` cannot be
   subclassed-and-injected without also owning the loop that constructs it.
   This function is therefore A51's own `evaluate_period_map` loop, copied
   verbatim in structure, calling A51's OWN unchanged private stepping
   helpers (`_initial_step`, `_march`, `_resolve_turn_on`, `_resolve_turn_off`,
   `period_intervals`) exactly as it does, with only the `Monitor` swapped
   for `RmsMonitor` (below), which adds the same time-weighted, right-endpoint
   accumulation A51's own `Monitor.observe` already uses for `out`/`a1..a3`/
   `LPAR_IN`, applied to `L1..L4` squared. No physics, stepping order, or
   window-resolution logic is changed.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

HERE = Path(__file__).resolve().parent
A51_DIR = HERE.parent / "A51_four_phase_joint_zvs_solve"
if str(A51_DIR) not in sys.path:
    sys.path.insert(0, str(A51_DIR))

import a51_period_map as M  # noqa: E402

#: A51's own pinned precharge-divider tap names (the measured nullity-3
#: subspace) -- identical reasoning as `run_fixed_point_search.py`.
PINNED = ("tap3", "tap2", "tap1")


# ---------------------------------------------------------------------------
# RMS-capable period evaluation
# ---------------------------------------------------------------------------
@dataclass
class RmsMonitor(M.Monitor):
    """A51's own `Monitor`, extended with a time-weighted sum of `I^2` per
    phase so RMS current over one period can be recovered afterwards.

    Uses the exact same right-endpoint, time-weighted rule A51's own
    `Monitor.observe` already applies to `out`/`a1..a3`/`LPAR_IN`
    (`weighted_sum`), just applied to `L1..L4` squared. `weighted_duration_s`
    is the same accumulator A51's own monitor already exposes, so RMS is
    `sqrt(weighted_sum_sq[phase] / weighted_duration_s)`.
    """

    weighted_sum_sq: dict[int, float] = field(default_factory=dict)

    def observe(self, step: M.HybridStep) -> None:
        previous_time_s = self._previous_time_s
        super().observe(step)
        if previous_time_s is None:
            return
        dt = step.time_s - previous_time_s
        if dt <= 0:
            return
        for phase in range(4):
            current_a = float(step.state[self.index[f"L{phase + 1}"]])
            self.weighted_sum_sq[phase] = (
                self.weighted_sum_sq.get(phase, 0.0) + dt * current_a * current_a
            )


def evaluate_period_map_with_rms(
    boundary,
    z: NDArray[np.float64],
    *,
    coarse_step_s: float = 62.5e-12,
    sub_step_s: float = 2e-12,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
    t0: float | None = None,
) -> M.PeriodResult:
    """`M.evaluate_period_map`, with an `RmsMonitor` instead of `M.Monitor`.

    See module docstring point 2 for why this loop is a copy rather than a
    call: A51's own function does not accept an injected monitor.
    """
    start_s = M.period_start_s(boundary) if t0 is None else t0
    names = M.variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    if np.asarray(z).shape != (len(names),):
        raise ValueError(f"state must have {len(names)} entries")
    monitor = RmsMonitor(index=index)
    current = M._initial_step(boundary, z, start_s, diode_state)
    monitor.observe(current)
    result = M.PeriodResult(z_next=np.empty(0))
    for interval in M.period_intervals(boundary, start_s):
        if interval.kind == "normal":
            current = M._march(
                current, interval.end_s, coarse_step_s, boundary, diode_state, monitor
            )
        elif interval.kind == "turn_on":
            result.turn_on_entry[interval.phase_index] = current  # type: ignore[index]
            current, verdict = M._resolve_turn_on(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_on.append(verdict)
        else:
            current, verdict = M._resolve_turn_off(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_off.append(verdict)
    result.z_next = current.state.copy()
    result.monitor = monitor
    result.final_step = current
    result.turn_on.sort(key=lambda verdict: verdict.phase_index)
    result.turn_off.sort(key=lambda verdict: verdict.phase_index)
    return result


def rms_and_peak_currents(
    boundary,
    z_star: NDArray[np.float64],
    *,
    coarse_step_s: float,
    sub_step_s: float,
) -> dict:
    """One RMS-instrumented period evaluation FROM `z_star`, i.e. of the
    periodic orbit itself (valid once `z_star` is an accepted fixed point).
    """
    result = evaluate_period_map_with_rms(
        boundary, z_star, coarse_step_s=coarse_step_s, sub_step_s=sub_step_s
    )
    monitor: RmsMonitor = result.monitor  # type: ignore[assignment]
    per_phase = []
    for phase in range(4):
        rms_a = float(np.sqrt(monitor.weighted_sum_sq[phase] / monitor.weighted_duration_s))
        minimum_a = monitor.phase_minimum_a[phase]
        maximum_a = monitor.phase_maximum_a[phase]
        peak_a = max(abs(minimum_a), abs(maximum_a))
        per_phase.append(
            {
                "phase": phase + 1,
                "rms_a": rms_a,
                "peak_a": peak_a,
                "minimum_a": minimum_a,
                "maximum_a": maximum_a,
                "average_a": monitor.weighted_sum.get(f"L{phase + 1}", None),
            }
        )
    return {
        "weighted_duration_s": monitor.weighted_duration_s,
        "per_phase": per_phase,
        "natural_zvs_flags": list(result.natural_zvs_flags),
        "turn_on_verdicts": result.turn_on,
        "result": result,
    }


# ---------------------------------------------------------------------------
# Newton + Picard fixed-point search (adapted from A51's own
# `run_fixed_point_search.py`; that file's own logic lives entirely in its
# `main()`, so this is a re-expression as a function, not an import)
# ---------------------------------------------------------------------------
def _safety(result: M.PeriodResult, label: str, log: list[dict]) -> None:
    monitor = result.monitor
    assert monitor is not None
    entry = {
        "label": label,
        "maximum_abs_phase_current_a": monitor.maximum_abs_phase_current_a,
        "argmax_phase": monitor.argmax_phase,
        "argmax_time_s": monitor.argmax_time_s,
    }
    log.append(entry)
    if monitor.maximum_abs_phase_current_a > M.PHASE_CURRENT_LIMIT_A:
        raise RuntimeError(
            f"SAFETY BOUND VIOLATED at {label}: "
            f"|iL| = {monitor.maximum_abs_phase_current_a:.4f} A > "
            f"{M.PHASE_CURRENT_LIMIT_A} A"
        )


def event_signature(result: M.PeriodResult) -> tuple:
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


def run_picard(
    boundary,
    z0: NDArray[np.float64],
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
    return {
        "damping": damping,
        "iterations": iterations,
        "history": history,
        "final_state": z.tolist(),
    }


def solve_fixed_point(
    boundary,
    z0: NDArray[np.float64],
    *,
    coarse_step_s: float = 0.0625e-9,
    sub_step_s: float = 5e-12,
    tolerance: float = 1e-6,
    max_iterations: int = 50,
    rcond: float = 1e-10,
    picard_iterations: int = 0,
    picard_damping: float = 0.5,
) -> dict:
    """A51's own Newton+Picard search, re-expressed as a callable function.

    Returns a payload with the same essential fields as A51's own
    `run_fixed_point_search.py` JSON output (`converged`,
    `final_relative_residual`, `final_state`, `final_natural_zvs_flags`,
    safety maxima), so callers can treat it the same way A51's own script's
    JSON is treated elsewhere in this project.
    """
    names = M.variable_names(boundary)
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

    increment = np.full(len(names), 1e-4, dtype=float)

    free = [position for position, name in enumerate(names) if name not in PINNED]

    for iteration in range(1, max_iterations + 1):
        relative = M.relative_residual(z, result.z_next)
        absolute = float(np.linalg.norm(residual, ord=np.inf))
        record = {
            "iteration": iteration,
            "relative_residual": relative,
            "absolute_residual_inf": absolute,
            "natural_zvs_flags": list(result.natural_zvs_flags),
            "maximum_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
        }
        if relative <= tolerance:
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
        matrix = full_matrix[:, free]
        step_free, _, rank, singular_values = np.linalg.lstsq(matrix, -residual, rcond=rcond)
        step = np.zeros(len(names), dtype=float)
        step[free] = step_free
        record["jacobian_rank"] = int(rank)
        record["newton_step_inf"] = float(np.linalg.norm(step, ord=np.inf))

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
    if not converged and final_relative <= tolerance:
        converged = True

    picard = None
    if picard_iterations > 0:
        picard = run_picard(
            boundary,
            z0,
            coarse_step_s=coarse_step_s,
            sub_step_s=sub_step_s,
            damping=picard_damping,
            iterations=picard_iterations,
            safety_log=safety_log,
        )

    maximum_current = max((entry["maximum_abs_phase_current_a"] for entry in safety_log), default=0.0)

    return {
        "boundary": {
            "phase_inductance_h": boundary.phase_inductance_h,
            "module_power_w": boundary.module_power_w,
            "switch_on_resistance_ohm": boundary.switch_on_resistance_ohm,
            "dead_time_s": boundary.dead_time_s,
        },
        "numerics": {
            "coarse_step_s": coarse_step_s,
            "sub_step_s": sub_step_s,
            "tolerance": tolerance,
            "max_iterations": max_iterations,
        },
        "converged": converged,
        "stalled_reason": stalled_reason,
        "iterations_used": len(history),
        "jacobian_rebuilds": jacobian_rebuilds,
        "history": history,
        "final_state": z.tolist(),
        "final_image": result.z_next.tolist(),
        "final_relative_residual": final_relative,
        "final_absolute_residual_inf": float(np.linalg.norm(result.z_next - z, ord=np.inf)),
        "final_natural_zvs_flags": list(result.natural_zvs_flags),
        "final_turn_on_verdicts": [
            {
                "phase": verdict.phase_index + 1,
                "natural_zvs": verdict.natural_zvs,
                "minimum_abs_vds_v": verdict.minimum_abs_vds_v,
                "minimum_signed_vds_v": verdict.minimum_signed_vds_v,
                "vds_at_window_end_v": verdict.vds_at_window_end_v,
                "hard_switch_residual_v": verdict.hard_switch_residual_v,
                "sign_change_time_s": verdict.sign_change_time_s,
            }
            for verdict in result.turn_on
        ],
        "final_orbit_metrics": {
            "minimum_phase_currents_a": list(result.monitor.phase_minimum_a),
            "maximum_phase_currents_a": list(result.monitor.phase_maximum_a),
            "average_output_v": (
                result.monitor.weighted_sum["out"] / result.monitor.weighted_duration_s
            ),
            "average_load_power_w": (
                (result.monitor.weighted_sum["out"] / result.monitor.weighted_duration_s) ** 2
                / boundary.load_resistance_ohm
            ),
        },
        "picard": picard,
        "safety": {
            "limit_a": M.PHASE_CURRENT_LIMIT_A,
            "evaluations": evaluations,
            "maximum_abs_phase_current_a": maximum_current,
            "within_limit": bool(maximum_current <= M.PHASE_CURRENT_LIMIT_A),
        },
        "z_star": z,
        "z0": z0,
    }
