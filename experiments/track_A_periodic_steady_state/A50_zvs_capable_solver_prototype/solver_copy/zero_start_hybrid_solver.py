"""Reference hybrid-DAE integrator for the ideal Track-B zero-start model.

The solver deliberately favors auditability over speed:

* backward Euler advances the singular MNA descriptor system;
* every step is clipped to the next PWM/input-ramp boundary;
* all eight precharge-diode combinations are tested;
* only complementarity-admissible diode states may be accepted.

It is a theoretical reference solver.  A full startup result requires a
time-step refinement study and does not become a P24 hardware claim.

A50 LOCAL COPY -- see `../BOUNDARY.md` Section 0 and Section 3.  Changes made
here and only here: every `Mode` construction now carries an independent
low-side state, `next_pwm_edge_s` additionally reports the dead-time edges when
`boundary.dead_time_s > 0`, and one new function `resolve_deadtime_window`
resolves a commanded dead-time interval at a fine fixed sub-step.  The
backward-Euler machinery (`_candidate_step`, `advance_fixed_diode_step`) is
otherwise untouched.  `src/scb_ivr/` is not modified and is not imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import floor
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from .zero_start_descriptor import (
    HIGH_SIDE_BRANCHES,
    Mode,
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
    complementary_mode,
    true_zero_initial_vector,
)


class ComplementarityFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class DiodeObservation:
    anode_minus_cathode_v: tuple[float, float, float]
    branch_current_a: tuple[float, float, float]


@dataclass(frozen=True)
class HybridStep:
    time_s: float
    state: NDArray[np.float64]
    mode: Mode
    diode_observation: DiodeObservation
    descriptor_residual_inf: float
    descriptor_relative_backward_error: float = 0.0


@dataclass(frozen=True)
class HybridTrajectory:
    boundary: ZeroStartBoundary
    steps: tuple[HybridStep, ...]
    maximum_step_s: float

    @property
    def final(self) -> HybridStep:
        return self.steps[-1]

    @property
    def diode_transition_count(self) -> int:
        return sum(
            left.mode.precharge_diode_on != right.mode.precharge_diode_on
            for left, right in zip(self.steps, self.steps[1:])
        )


@dataclass(frozen=True)
class PeriodCheckpoint:
    time_s: float
    completed_periods: int
    input_command_v: float
    flying_capacitor_v: tuple[float, float, float]
    output_v: float
    phase_currents_a: tuple[float, float, float, float]
    input_inductor_current_a: float
    cumulative_diode_transitions: int


@dataclass(frozen=True)
class DiodeTransition:
    time_s: float
    previous_state: tuple[bool, bool, bool]
    next_state: tuple[bool, bool, bool]


@dataclass(frozen=True)
class ZeroStartSummary:
    boundary: ZeroStartBoundary
    checkpoints: tuple[PeriodCheckpoint, ...]
    final_step: HybridStep
    maximum_step_s: float
    maximum_abs_phase_current_a: float
    maximum_abs_input_inductor_current_a: float
    maximum_output_v: float
    diode_transition_count: int
    diode_transitions: tuple[DiodeTransition, ...]
    maximum_descriptor_residual_inf: float
    maximum_descriptor_relative_backward_error: float


@dataclass(frozen=True)
class PoincareSample:
    """Left-limit state sampled immediately before one phase-1 PWM rising edge."""

    sample_index: int
    checkpoint: PeriodCheckpoint
    diode_state: tuple[bool, bool, bool]
    full_state: NDArray[np.float64]


@dataclass(frozen=True)
class PoincareSummary:
    boundary: ZeroStartBoundary
    initial_step: HybridStep
    samples: tuple[PoincareSample, ...]
    final_step: HybridStep
    maximum_step_s: float
    diode_transition_count: int
    maximum_descriptor_residual_inf: float
    maximum_descriptor_relative_backward_error: float


def named_hybrid_state(
    step: HybridStep,
    boundary: ZeroStartBoundary,
) -> dict[str, float]:
    """Serialize all MNA variables without discarding algebraic state."""
    system = assemble_descriptor(boundary, step.mode, step.time_s)
    return {
        name: float(value)
        for name, value in zip(system.variable_names, step.state, strict=True)
    }


def hybrid_step_from_named_state(
    boundary: ZeroStartBoundary,
    *,
    time_s: float,
    state_by_variable: Mapping[str, float],
    high_side_on: tuple[bool, bool, bool, bool],
    precharge_diode_on: tuple[bool, bool, bool],
    low_side_on: tuple[bool, bool, bool, bool] | None = None,
) -> HybridStep:
    """Restore a checkpoint only when its complete variable set is present.

    ``low_side_on`` defaults to the strict complement of ``high_side_on``,
    which is the only state the pre-A50 checkpoint format could express.
    """
    mode = (
        complementary_mode(high_side_on, precharge_diode_on)
        if low_side_on is None
        else Mode(high_side_on, low_side_on, precharge_diode_on)
    )
    system = assemble_descriptor(boundary, mode, time_s)
    expected = set(system.variable_names)
    supplied = set(state_by_variable)
    if supplied != expected:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise ValueError(f"checkpoint variables differ: missing={missing}, extra={extra}")
    state = np.array(
        [state_by_variable[name] for name in system.variable_names], dtype=float
    )
    if not np.isfinite(state).all():
        raise ValueError("checkpoint state must be finite")
    return HybridStep(
        time_s=time_s,
        state=state,
        mode=mode,
        diode_observation=diode_observation(state, boundary, mode),
        descriptor_residual_inf=0.0,
    )


def diode_observation(
    state: NDArray[np.float64],
    boundary: ZeroStartBoundary,
    mode: Mode,
) -> DiodeObservation:
    if not boundary.divider_enabled:
        return DiodeObservation((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    system = assemble_descriptor(boundary, mode, 0.0)
    index = {name: position for position, name in enumerate(system.node_names)}
    pairs = (("tap3", "a1"), ("tap2", "a2"), ("tap1", "a3"))
    voltages = tuple(state[index[a]] - state[index[k]] for a, k in pairs)
    currents = tuple(
        voltage
        / (
            boundary.diode_on_resistance_ohm
            if enabled
            else boundary.diode_off_resistance_ohm
        )
        for voltage, enabled in zip(voltages, mode.precharge_diode_on)
    )
    return DiodeObservation(voltages, currents)


def complementarity_admissible(
    observation: DiodeObservation,
    diode_state: tuple[bool, bool, bool],
    *,
    voltage_tolerance_v: float,
    current_tolerance_a: float,
) -> bool:
    """Finite-Ron active-set form of ideal-diode complementarity."""
    for enabled, voltage, current in zip(
        diode_state,
        observation.anode_minus_cathode_v,
        observation.branch_current_a,
    ):
        if enabled:
            if current < -current_tolerance_a:
                return False
        elif voltage > voltage_tolerance_v:
            return False
    return True


def next_pwm_edge_s(time_s: float, boundary: ZeroStartBoundary) -> float:
    """Return the next commanded gate transition strictly after ``time_s``.

    A50 change: with ``dead_time_s > 0`` the real gate transitions are the four
    dead-time boundaries ``start -/+ d/2`` and ``end -/+ d/2``, not the nominal
    ``start``/``end`` instants, so those are reported instead.  With
    ``dead_time_s == 0`` the original candidate set is reproduced exactly.
    """
    period = boundary.period_s
    dead_time = boundary.dead_time_s
    half = 0.5 * dead_time
    candidates: list[float] = []
    epsilon = max(1e-18, 1e-12 * period)
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        cycle = floor((time_s - start0) / period)
        for index in (cycle, cycle + 1, cycle + 2):
            start = start0 + index * period
            end = start + boundary.on_time_s
            edges = (
                (start, end)
                if dead_time <= 0.0
                else (start - half, start + half, end - half, end + half)
            )
            for edge in edges:
                if edge > time_s + epsilon:
                    candidates.append(edge)
    if not candidates:
        raise RuntimeError("failed to locate the next PWM edge")
    return min(candidates)


def _candidate_step(
    previous_state: NDArray[np.float64],
    time_s: float,
    next_time_s: float,
    boundary: ZeroStartBoundary,
    high_side_on: tuple[bool, bool, bool, bool],
    low_side_on: tuple[bool, bool, bool, bool],
    diode_state: tuple[bool, bool, bool],
) -> HybridStep:
    mode = Mode(high_side_on, low_side_on, diode_state)
    system = assemble_descriptor(boundary, mode, next_time_s)
    dt = next_time_s - time_s
    matrix = system.e / dt + system.a
    vector = system.e @ previous_state / dt + system.rhs
    try:
        state = np.linalg.solve(matrix, vector)
    except np.linalg.LinAlgError as error:
        raise ComplementarityFailure("singular descriptor step") from error
    residual = matrix @ state - vector
    residual_inf = float(np.linalg.norm(residual, ord=np.inf))
    scale = float(
        np.linalg.norm(matrix, ord=np.inf) * np.linalg.norm(state, ord=np.inf)
        + np.linalg.norm(vector, ord=np.inf)
    )
    return HybridStep(
        time_s=next_time_s,
        state=state,
        mode=mode,
        diode_observation=diode_observation(state, boundary, mode),
        descriptor_residual_inf=residual_inf,
        descriptor_relative_backward_error=residual_inf / max(scale, np.finfo(float).tiny),
    )


def advance_complementarity_step(
    previous: HybridStep,
    next_time_s: float,
    boundary: ZeroStartBoundary,
    *,
    voltage_tolerance_v: float = 1e-9,
    current_tolerance_a: float = 1e-9,
) -> HybridStep:
    if next_time_s <= previous.time_s:
        raise ValueError("time must advance strictly")
    midpoint = 0.5 * (previous.time_s + next_time_s)
    commanded = commanded_pwm_mode(midpoint, boundary)
    high = commanded.high_side_on
    low = commanded.low_side_on
    candidates: list[HybridStep] = []
    for diode_state in product((False, True), repeat=3):
        candidate = _candidate_step(
            previous.state,
            previous.time_s,
            next_time_s,
            boundary,
            high,
            low,
            diode_state,
        )
        if complementarity_admissible(
            candidate.diode_observation,
            diode_state,
            voltage_tolerance_v=voltage_tolerance_v,
            current_tolerance_a=current_tolerance_a,
        ):
            candidates.append(candidate)
    if not candidates:
        raise ComplementarityFailure(
            f"no admissible diode active set at t={next_time_s:.9e} s"
        )

    previous_diodes = previous.mode.precharge_diode_on

    def score(candidate: HybridStep) -> tuple[int, float]:
        switching_distance = sum(
            left != right
            for left, right in zip(
                previous_diodes, candidate.mode.precharge_diode_on
            )
        )
        complementarity_margin = sum(
            abs(value)
            for value in candidate.diode_observation.anode_minus_cathode_v
        )
        return switching_distance, complementarity_margin

    return min(candidates, key=score)


def advance_fixed_diode_step(
    previous: HybridStep,
    next_time_s: float,
    boundary: ZeroStartBoundary,
    diode_state: tuple[bool, bool, bool],
) -> HybridStep:
    """Advance one linear mode step without changing the selected diodes.

    This is used only to construct and audit a candidate affine period map.
    Physical validity must subsequently be checked with diode complementarity.
    """
    if next_time_s <= previous.time_s:
        raise ValueError("time must advance strictly")
    midpoint = 0.5 * (previous.time_s + next_time_s)
    commanded = commanded_pwm_mode(midpoint, boundary)
    return _candidate_step(
        previous.state,
        previous.time_s,
        next_time_s,
        boundary,
        commanded.high_side_on,
        commanded.low_side_on,
        diode_state,
    )


@dataclass(frozen=True)
class DeadTimeWindowResolution:
    """Outcome of one commanded dead-time interval on one phase.

    ``minimum_abs_switch_voltage_v`` is the ZVS/no-ZVS observable: the smallest
    ``|V(high-side node, next node)|`` seen anywhere in the window, i.e. the
    residual high-side drain-source voltage that a forced turn-on at that
    instant would have to absorb.  This reuses A37/A48's own SPICE-side
    diagnostic convention rather than inventing a new metric.
    """

    phase_index: int
    high_side_branch: tuple[str, str | None]
    start_time_s: float
    commanded_end_time_s: float
    sub_step_s: float
    step_count: int
    commanded_dead_time_confirmed: bool
    initial_switch_voltage_v: float
    minimum_abs_switch_voltage_v: float
    minimum_abs_switch_voltage_time_s: float
    minimum_signed_switch_voltage_v: float
    final_switch_voltage_v: float
    crossing_tolerance_v: float
    crossed_tolerance: bool
    crossed_tolerance_time_s: float | None
    sign_change_time_s: float | None
    switch_current_at_crossing_a: float | None
    maximum_descriptor_relative_backward_error: float
    steps: tuple[HybridStep, ...]

    @property
    def final(self) -> HybridStep:
        return self.steps[-1]


def resolve_deadtime_window(
    boundary: ZeroStartBoundary,
    initial: HybridStep,
    *,
    phase_index: int,
    window_end_s: float | None = None,
    sub_step_s: float = 50e-12,
    crossing_tolerance_v: float = 1e-3,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
    store_steps: bool = True,
) -> DeadTimeWindowResolution:
    """Step one commanded dead-time interval at a fine fixed sub-step.

    `../BOUNDARY.md` Section 3.5.  The integration is `advance_fixed_diode_step`
    UNCHANGED -- the same backward-Euler descriptor step the rest of this module
    already uses -- called on a uniform grid of ``sub_step_s`` (default 50 ps,
    this project's own established SPICE ``TMAX`` convention from R04E16-R04E26)
    with the final step clipped to the commanded window end.

    ``window_end_s`` defaults to ``initial.time_s + boundary.dead_time_s``, the
    full commanded dead time starting at ``initial``.  The function does not
    decide when the high side is allowed to turn on; it only reports what the
    high-side switch voltage did inside the commanded window, so the caller
    keeps the ZVS verdict explicit.

    A ``crossed_tolerance`` of True means ``|Vds|`` fell below
    ``crossing_tolerance_v`` (default 1 mV, A42's own published precision)
    strictly before the commanded window end.  ``sign_change_time_s`` is the
    linearly interpolated instant of the first actual sign change of the signed
    switch voltage, which is the quantity comparable with a SPICE
    ``.meas ... WHEN V(vin,a1)=0`` crossing time.
    """
    if not 0 <= phase_index < boundary.phases:
        raise ValueError("phase index outside the four-phase boundary")
    if sub_step_s <= 0:
        raise ValueError("dead-time sub-step must be positive")
    if crossing_tolerance_v < 0:
        raise ValueError("crossing tolerance must be non-negative")
    end_time_s = (
        initial.time_s + boundary.dead_time_s
        if window_end_s is None
        else window_end_s
    )
    if end_time_s <= initial.time_s:
        raise ValueError("dead-time window must have positive duration")

    branch = HIGH_SIDE_BRANCHES[phase_index]
    system = assemble_descriptor(boundary, initial.mode, initial.time_s)
    index = {name: position for position, name in enumerate(system.variable_names)}
    inductor_name = f"L{phase_index + 1}"

    def switch_voltage(state: NDArray[np.float64]) -> float:
        first, second = branch
        value = float(state[index[first]])
        if second is not None:
            value -= float(state[index[second]])
        return value

    def phase_current(state: NDArray[np.float64]) -> float:
        return float(state[index[inductor_name]])

    tolerance = max(1e-21, (end_time_s - initial.time_s) * 1e-12)
    current = initial
    steps: list[HybridStep] = [initial]
    confirmed = True
    minimum_abs = abs(switch_voltage(initial.state))
    minimum_abs_time = initial.time_s
    minimum_signed = switch_voltage(initial.state)
    maximum_backward_error = initial.descriptor_relative_backward_error
    crossed_time: float | None = None
    sign_change_time: float | None = None
    current_at_crossing: float | None = None
    step_count = 0

    while current.time_s < end_time_s - tolerance:
        next_time_s = min(current.time_s + sub_step_s, end_time_s)
        following = advance_fixed_diode_step(
            current, next_time_s, boundary, diode_state
        )
        step_count += 1
        if not (
            not following.mode.high_side_on[phase_index]
            and not following.mode.low_side_on[phase_index]
        ):
            confirmed = False
        previous_voltage = switch_voltage(current.state)
        voltage = switch_voltage(following.state)
        maximum_backward_error = max(
            maximum_backward_error, following.descriptor_relative_backward_error
        )
        if abs(voltage) < minimum_abs:
            minimum_abs = abs(voltage)
            minimum_abs_time = following.time_s
        minimum_signed = min(minimum_signed, voltage)
        if crossed_time is None and abs(voltage) < crossing_tolerance_v:
            crossed_time = following.time_s
            current_at_crossing = phase_current(following.state)
        if sign_change_time is None and previous_voltage * voltage < 0.0:
            span = voltage - previous_voltage
            fraction = 0.0 if span == 0.0 else -previous_voltage / span
            sign_change_time = current.time_s + fraction * (
                following.time_s - current.time_s
            )
            if current_at_crossing is None:
                current_at_crossing = phase_current(following.state)
        if store_steps:
            steps.append(following)
        else:
            steps[-1] = following
        current = following

    return DeadTimeWindowResolution(
        phase_index=phase_index,
        high_side_branch=branch,
        start_time_s=initial.time_s,
        commanded_end_time_s=end_time_s,
        sub_step_s=sub_step_s,
        step_count=step_count,
        commanded_dead_time_confirmed=confirmed,
        initial_switch_voltage_v=switch_voltage(initial.state),
        minimum_abs_switch_voltage_v=minimum_abs,
        minimum_abs_switch_voltage_time_s=minimum_abs_time,
        minimum_signed_switch_voltage_v=minimum_signed,
        final_switch_voltage_v=switch_voltage(current.state),
        crossing_tolerance_v=crossing_tolerance_v,
        crossed_tolerance=crossed_time is not None,
        crossed_tolerance_time_s=crossed_time,
        sign_change_time_s=sign_change_time,
        switch_current_at_crossing_a=current_at_crossing,
        maximum_descriptor_relative_backward_error=maximum_backward_error,
        steps=tuple(steps),
    )


def simulate_zero_start(
    boundary: ZeroStartBoundary,
    stop_time_s: float,
    maximum_step_s: float,
    *,
    initial_diode_state: tuple[bool, bool, bool] = (False, False, False),
    voltage_tolerance_v: float = 1e-9,
    current_tolerance_a: float = 1e-9,
) -> HybridTrajectory:
    """Integrate the ideal mathematical boundary without fitting outcomes."""
    if stop_time_s <= 0 or maximum_step_s <= 0:
        raise ValueError("stop time and maximum step must be positive")
    if maximum_step_s > boundary.on_time_s:
        raise ValueError("maximum step must not exceed the shortest on interval")
    initial_mode = commanded_pwm_mode(
        0.0, boundary, precharge_diode_on=initial_diode_state
    )
    initial_state = true_zero_initial_vector(boundary)
    initial = HybridStep(
        time_s=0.0,
        state=initial_state,
        mode=initial_mode,
        diode_observation=diode_observation(initial_state, boundary, initial_mode),
        descriptor_residual_inf=0.0,
    )
    steps = [initial]
    time_s = 0.0
    tolerance = max(1e-18, stop_time_s * 1e-14)
    while time_s < stop_time_s - tolerance:
        boundary_times = [stop_time_s, time_s + maximum_step_s, next_pwm_edge_s(time_s, boundary)]
        if boundary.input_ramp_s > time_s + tolerance:
            boundary_times.append(boundary.input_ramp_s)
        next_time = min(value for value in boundary_times if value > time_s + tolerance)
        step = advance_complementarity_step(
            steps[-1],
            next_time,
            boundary,
            voltage_tolerance_v=voltage_tolerance_v,
            current_tolerance_a=current_tolerance_a,
        )
        steps.append(step)
        time_s = next_time
    return HybridTrajectory(boundary, tuple(steps), maximum_step_s)


def _checkpoint(
    step: HybridStep,
    boundary: ZeroStartBoundary,
    cumulative_diode_transitions: int,
) -> PeriodCheckpoint:
    system = assemble_descriptor(boundary, step.mode, step.time_s)
    index = {name: position for position, name in enumerate(system.variable_names)}
    state = step.state
    return PeriodCheckpoint(
        time_s=step.time_s,
        completed_periods=int(round(step.time_s / boundary.period_s)),
        input_command_v=min(
            boundary.vin_target_v * step.time_s / boundary.input_ramp_s,
            boundary.vin_target_v,
        ),
        flying_capacitor_v=(
            float(state[index["a1"]] - state[index["x1"]]),
            float(state[index["a2"]] - state[index["x2"]]),
            float(state[index["a3"]] - state[index["x3"]]),
        ),
        output_v=float(state[index["out"]]),
        phase_currents_a=tuple(
            float(state[index[f"L{phase}"]]) for phase in range(1, 5)
        ),  # type: ignore[arg-type]
        input_inductor_current_a=float(state[index["LPAR_IN"]]),
        cumulative_diode_transitions=cumulative_diode_transitions,
    )


def simulate_zero_start_checkpoints(
    boundary: ZeroStartBoundary,
    stop_time_s: float,
    maximum_step_s: float,
    *,
    checkpoint_every_periods: int = 1,
    initial_diode_state: tuple[bool, bool, bool] = (False, False, False),
    voltage_tolerance_v: float = 1e-9,
    current_tolerance_a: float = 1e-9,
) -> ZeroStartSummary:
    """Memory-bounded period map for ramp and post-ramp reachability studies."""
    if checkpoint_every_periods <= 0:
        raise ValueError("checkpoint period interval must be positive")
    if stop_time_s <= 0 or maximum_step_s <= 0:
        raise ValueError("stop time and maximum step must be positive")
    if maximum_step_s > boundary.on_time_s:
        raise ValueError("maximum step must not exceed the shortest on interval")

    mode = commanded_pwm_mode(0.0, boundary, precharge_diode_on=initial_diode_state)
    state = true_zero_initial_vector(boundary)
    current = HybridStep(
        0.0,
        state,
        mode,
        diode_observation(state, boundary, mode),
        0.0,
    )
    checkpoints = [_checkpoint(current, boundary, 0)]
    transitions = 0
    transition_records: list[DiodeTransition] = []
    maximum_abs_phase_current = 0.0
    maximum_abs_input_current = 0.0
    maximum_output = 0.0
    maximum_residual = 0.0
    maximum_relative_error = 0.0
    tolerance = max(1e-18, stop_time_s * 1e-14)
    next_checkpoint_period = checkpoint_every_periods

    while current.time_s < stop_time_s - tolerance:
        boundary_times = [
            stop_time_s,
            current.time_s + maximum_step_s,
            next_pwm_edge_s(current.time_s, boundary),
            next_checkpoint_period * boundary.period_s,
        ]
        if boundary.input_ramp_s > current.time_s + tolerance:
            boundary_times.append(boundary.input_ramp_s)
        next_time = min(
            value for value in boundary_times if value > current.time_s + tolerance
        )
        following = advance_complementarity_step(
            current,
            next_time,
            boundary,
            voltage_tolerance_v=voltage_tolerance_v,
            current_tolerance_a=current_tolerance_a,
        )
        if following.mode.precharge_diode_on != current.mode.precharge_diode_on:
            transitions += 1
            transition_records.append(
                DiodeTransition(
                    following.time_s,
                    current.mode.precharge_diode_on,
                    following.mode.precharge_diode_on,
                )
            )
        system = assemble_descriptor(boundary, following.mode, following.time_s)
        index = {name: position for position, name in enumerate(system.variable_names)}
        maximum_abs_phase_current = max(
            maximum_abs_phase_current,
            *(abs(float(following.state[index[f"L{phase}"]])) for phase in range(1, 5)),
        )
        maximum_abs_input_current = max(
            maximum_abs_input_current,
            abs(float(following.state[index["LPAR_IN"]])),
        )
        maximum_output = max(maximum_output, float(following.state[index["out"]]))
        maximum_residual = max(maximum_residual, following.descriptor_residual_inf)
        maximum_relative_error = max(
            maximum_relative_error,
            following.descriptor_relative_backward_error,
        )
        current = following

        checkpoint_time = next_checkpoint_period * boundary.period_s
        if abs(current.time_s - checkpoint_time) <= tolerance:
            checkpoints.append(_checkpoint(current, boundary, transitions))
            next_checkpoint_period += checkpoint_every_periods

    if abs(checkpoints[-1].time_s - current.time_s) > tolerance:
        checkpoints.append(_checkpoint(current, boundary, transitions))
    return ZeroStartSummary(
        boundary=boundary,
        checkpoints=tuple(checkpoints),
        final_step=current,
        maximum_step_s=maximum_step_s,
        maximum_abs_phase_current_a=maximum_abs_phase_current,
        maximum_abs_input_inductor_current_a=maximum_abs_input_current,
        maximum_output_v=maximum_output,
        diode_transition_count=transitions,
        diode_transitions=tuple(transition_records),
        maximum_descriptor_residual_inf=maximum_residual,
        maximum_descriptor_relative_backward_error=maximum_relative_error,
    )


def next_periodic_sample_s(
    time_s: float,
    period_s: float,
    *,
    phase_s: float = 0.0,
) -> float:
    """Return the first periodic sampling event strictly after ``time_s``."""
    if period_s <= 0:
        raise ValueError("sampling period must be positive")
    normalized_phase = phase_s % period_s
    cycle = floor((time_s - normalized_phase) / period_s)
    candidate = normalized_phase + (cycle + 1) * period_s
    tolerance = max(1e-18, period_s * 1e-12)
    if candidate <= time_s + tolerance:
        candidate += period_s
    return candidate


def continue_zero_start_poincare(
    boundary: ZeroStartBoundary,
    initial_step: HybridStep,
    periods: int,
    maximum_step_s: float,
    *,
    sampling_phase_s: float = 0.0,
    voltage_tolerance_v: float = 1e-9,
    current_tolerance_a: float = 1e-9,
) -> PoincareSummary:
    """Continue an existing state and sample a fixed absolute PWM event.

    Samples are the left limits immediately before phase-1 rising edges by
    default.  This avoids treating the arbitrary end of an input ramp as a
    Poincare section.  Stored-energy variables remain continuous through the
    ideal switching event; algebraic node voltages must not be interpreted as
    right-limit switch-node values.
    """
    if periods <= 0:
        raise ValueError("period count must be positive")
    if maximum_step_s <= 0 or maximum_step_s > boundary.on_time_s:
        raise ValueError("maximum step must be positive and no larger than on-time")
    expected_size = assemble_descriptor(
        boundary, initial_step.mode, initial_step.time_s
    ).size
    if initial_step.state.shape != (expected_size,):
        raise ValueError("initial state dimension does not match the boundary")

    current = initial_step
    target = next_periodic_sample_s(
        current.time_s,
        boundary.period_s,
        phase_s=sampling_phase_s,
    )
    samples: list[PoincareSample] = []
    transitions = 0
    maximum_residual = initial_step.descriptor_residual_inf
    maximum_relative_error = initial_step.descriptor_relative_backward_error
    tolerance = max(1e-18, boundary.period_s * 1e-12)

    for sample_index in range(1, periods + 1):
        while current.time_s < target - tolerance:
            boundary_times = [
                target,
                current.time_s + maximum_step_s,
                next_pwm_edge_s(current.time_s, boundary),
            ]
            if boundary.input_ramp_s > current.time_s + tolerance:
                boundary_times.append(boundary.input_ramp_s)
            next_time = min(
                value
                for value in boundary_times
                if value > current.time_s + tolerance
            )
            following = advance_complementarity_step(
                current,
                next_time,
                boundary,
                voltage_tolerance_v=voltage_tolerance_v,
                current_tolerance_a=current_tolerance_a,
            )
            if following.mode.precharge_diode_on != current.mode.precharge_diode_on:
                transitions += 1
            maximum_residual = max(
                maximum_residual, following.descriptor_residual_inf
            )
            maximum_relative_error = max(
                maximum_relative_error,
                following.descriptor_relative_backward_error,
            )
            current = following
        samples.append(
            PoincareSample(
                sample_index=sample_index,
                checkpoint=_checkpoint(current, boundary, transitions),
                diode_state=current.mode.precharge_diode_on,
                full_state=current.state.copy(),
            )
        )
        target += boundary.period_s

    return PoincareSummary(
        boundary=boundary,
        initial_step=initial_step,
        samples=tuple(samples),
        final_step=current,
        maximum_step_s=maximum_step_s,
        diode_transition_count=transitions,
        maximum_descriptor_residual_inf=maximum_residual,
        maximum_descriptor_relative_backward_error=maximum_relative_error,
    )
