"""Reference hybrid-DAE integrator for the ideal Track-B zero-start model.

The solver deliberately favors auditability over speed:

* backward Euler advances the singular MNA descriptor system;
* every step is clipped to the next PWM/input-ramp boundary;
* all eight precharge-diode combinations are tested;
* only complementarity-admissible diode states may be accepted.

It is a theoretical reference solver.  A full startup result requires a
time-step refinement study and does not become a P24 hardware claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import floor

import numpy as np
from numpy.typing import NDArray

from scb_ivr.zero_start_descriptor import (
    Mode,
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
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
    period = boundary.period_s
    candidates: list[float] = []
    epsilon = max(1e-18, 1e-12 * period)
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        cycle = floor((time_s - start0) / period)
        for index in (cycle, cycle + 1, cycle + 2):
            start = start0 + index * period
            end = start + boundary.on_time_s
            if start > time_s + epsilon:
                candidates.append(start)
            if end > time_s + epsilon:
                candidates.append(end)
    if not candidates:
        raise RuntimeError("failed to locate the next PWM edge")
    return min(candidates)


def _candidate_step(
    previous_state: NDArray[np.float64],
    time_s: float,
    next_time_s: float,
    boundary: ZeroStartBoundary,
    high_side_on: tuple[bool, bool, bool, bool],
    diode_state: tuple[bool, bool, bool],
) -> HybridStep:
    mode = Mode(high_side_on, diode_state)
    system = assemble_descriptor(boundary, mode, next_time_s)
    dt = next_time_s - time_s
    matrix = system.e / dt + system.a
    vector = system.e @ previous_state / dt + system.rhs
    try:
        state = np.linalg.solve(matrix, vector)
    except np.linalg.LinAlgError as error:
        raise ComplementarityFailure("singular descriptor step") from error
    residual = matrix @ state - vector
    return HybridStep(
        time_s=next_time_s,
        state=state,
        mode=mode,
        diode_observation=diode_observation(state, boundary, mode),
        descriptor_residual_inf=float(np.linalg.norm(residual, ord=np.inf)),
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
    high = commanded_pwm_mode(midpoint, boundary).high_side_on
    candidates: list[HybridStep] = []
    for diode_state in product((False, True), repeat=3):
        candidate = _candidate_step(
            previous.state,
            previous.time_s,
            next_time_s,
            boundary,
            high,
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
    )
