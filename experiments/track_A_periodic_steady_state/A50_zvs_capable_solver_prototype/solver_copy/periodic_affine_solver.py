"""Direct affine-period solver for a frozen hybrid switching branch.

The method is valid only while the selected diode state remains admissible for
the entire recovered orbit.  It is a numerical fixed-point tool, not a claim
that P24 specifies this startup or steady-state controller.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .zero_start_descriptor import (
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
)
from .zero_start_hybrid_solver import (
    HybridStep,
    HybridTrajectory,
    advance_fixed_diode_step,
    complementarity_admissible,
    diode_observation,
    next_pwm_edge_s,
)


@dataclass(frozen=True)
class AffinePeriodMap:
    matrix: NDArray[np.float64]
    offset: NDArray[np.float64]
    start_time_s: float
    maximum_step_s: float
    diode_state: tuple[bool, bool, bool]


@dataclass(frozen=True)
class PeriodicFixedPoint:
    period_map: AffinePeriodMap
    state: NDArray[np.float64]
    least_squares_rank: int
    singular_values: NDArray[np.float64]
    fixed_point_residual_inf: float
    orbit: HybridTrajectory
    orbit_closure_inf: float
    maximum_off_diode_forward_voltage_v: float
    diode_complementarity_valid: bool


@dataclass(frozen=True)
class PeriodicOrbitMetrics:
    average_output_v: float
    average_load_power_w: float
    average_phase_currents_a: tuple[float, float, float, float]
    minimum_phase_currents_a: tuple[float, float, float, float]
    maximum_phase_currents_a: tuple[float, float, float, float]
    average_input_inductor_current_a: float
    average_flying_capacitor_v: tuple[float, float, float]


def propagate_fixed_diode_period(
    boundary: ZeroStartBoundary,
    state: NDArray[np.float64],
    *,
    start_time_s: float,
    maximum_step_s: float,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
) -> HybridTrajectory:
    """Propagate exactly one PWM period on one frozen diode branch."""
    if start_time_s < boundary.input_ramp_s:
        raise ValueError("affine post-ramp map requires constant input voltage")
    if maximum_step_s <= 0 or maximum_step_s > boundary.on_time_s:
        raise ValueError("maximum step must be positive and no larger than on-time")
    left_time = start_time_s - max(1e-18, boundary.period_s * 1e-12)
    left_mode = commanded_pwm_mode(
        left_time,
        boundary,
        precharge_diode_on=diode_state,
    )
    system = assemble_descriptor(boundary, left_mode, start_time_s)
    if state.shape != (system.size,):
        raise ValueError("state dimension does not match descriptor system")
    initial = HybridStep(
        time_s=start_time_s,
        state=np.asarray(state, dtype=float).copy(),
        mode=left_mode,
        diode_observation=diode_observation(state, boundary, left_mode),
        descriptor_residual_inf=0.0,
        descriptor_relative_backward_error=0.0,
    )
    steps = [initial]
    target = start_time_s + boundary.period_s
    tolerance = max(1e-18, boundary.period_s * 1e-12)
    while steps[-1].time_s < target - tolerance:
        current = steps[-1]
        next_time = min(
            target,
            current.time_s + maximum_step_s,
            next_pwm_edge_s(current.time_s, boundary),
        )
        steps.append(
            advance_fixed_diode_step(
                current,
                next_time,
                boundary,
                diode_state,
            )
        )
    return HybridTrajectory(boundary, tuple(steps), maximum_step_s)


def build_affine_period_map(
    boundary: ZeroStartBoundary,
    *,
    start_time_s: float,
    maximum_step_s: float,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
) -> AffinePeriodMap:
    """Identify the exact affine map induced by the chosen BE discretization."""
    mode = commanded_pwm_mode(
        start_time_s - max(1e-18, boundary.period_s * 1e-12),
        boundary,
        precharge_diode_on=diode_state,
    )
    size = assemble_descriptor(boundary, mode, start_time_s).size
    zero = np.zeros(size, dtype=float)
    offset = propagate_fixed_diode_period(
        boundary,
        zero,
        start_time_s=start_time_s,
        maximum_step_s=maximum_step_s,
        diode_state=diode_state,
    ).final.state
    matrix = np.empty((size, size), dtype=float)
    for column in range(size):
        basis = np.zeros(size, dtype=float)
        basis[column] = 1.0
        image = propagate_fixed_diode_period(
            boundary,
            basis,
            start_time_s=start_time_s,
            maximum_step_s=maximum_step_s,
            diode_state=diode_state,
        ).final.state
        matrix[:, column] = image - offset
    return AffinePeriodMap(
        matrix=matrix,
        offset=offset,
        start_time_s=start_time_s,
        maximum_step_s=maximum_step_s,
        diode_state=diode_state,
    )


def solve_periodic_fixed_point(
    boundary: ZeroStartBoundary,
    period_map: AffinePeriodMap,
    *,
    voltage_tolerance_v: float = 1e-9,
    current_tolerance_a: float = 1e-9,
) -> PeriodicFixedPoint:
    """Solve and physically audit one candidate fixed point."""
    identity_minus_map = np.eye(period_map.matrix.shape[0]) - period_map.matrix
    state, _, rank, singular_values = np.linalg.lstsq(
        identity_minus_map,
        period_map.offset,
        rcond=None,
    )
    algebraic_residual = (
        period_map.matrix @ state + period_map.offset - state
    )
    orbit = propagate_fixed_diode_period(
        boundary,
        state,
        start_time_s=period_map.start_time_s,
        maximum_step_s=period_map.maximum_step_s,
        diode_state=period_map.diode_state,
    )
    closure = orbit.final.state - state
    off_forward_voltages = [
        voltage
        for step in orbit.steps
        for voltage, enabled in zip(
            step.diode_observation.anode_minus_cathode_v,
            period_map.diode_state,
        )
        if not enabled
    ]
    maximum_forward = max(off_forward_voltages, default=float("-inf"))
    valid = all(
        complementarity_admissible(
            step.diode_observation,
            period_map.diode_state,
            voltage_tolerance_v=voltage_tolerance_v,
            current_tolerance_a=current_tolerance_a,
        )
        for step in orbit.steps
    )
    return PeriodicFixedPoint(
        period_map=period_map,
        state=state,
        least_squares_rank=int(rank),
        singular_values=singular_values,
        fixed_point_residual_inf=float(np.linalg.norm(algebraic_residual, ord=np.inf)),
        orbit=orbit,
        orbit_closure_inf=float(np.linalg.norm(closure, ord=np.inf)),
        maximum_off_diode_forward_voltage_v=float(maximum_forward),
        diode_complementarity_valid=valid,
    )


def periodic_orbit_metrics(
    boundary: ZeroStartBoundary,
    fixed_point: PeriodicFixedPoint,
) -> PeriodicOrbitMetrics:
    """Integrate one recovered period using the solver's right-endpoint rule."""
    orbit = fixed_point.orbit
    system = assemble_descriptor(
        boundary,
        orbit.steps[0].mode,
        orbit.steps[0].time_s,
    )
    index = {name: position for position, name in enumerate(system.variable_names)}
    duration = orbit.final.time_s - orbit.steps[0].time_s
    if duration <= 0:
        raise ValueError("periodic orbit must have positive duration")
    weighted_state = np.zeros(system.size, dtype=float)
    weighted_load_power = 0.0
    phase_names = ("L1", "L2", "L3", "L4")
    phase_min = np.full(4, np.inf)
    phase_max = np.full(4, -np.inf)
    for left, right in zip(orbit.steps, orbit.steps[1:]):
        dt = right.time_s - left.time_s
        weighted_state += right.state * dt
        output_v = float(right.state[index["out"]])
        weighted_load_power += output_v**2 / boundary.load_resistance_ohm * dt
        phase_values = np.array(
            [right.state[index[name]] for name in phase_names], dtype=float
        )
        phase_min = np.minimum(phase_min, phase_values)
        phase_max = np.maximum(phase_max, phase_values)
    average = weighted_state / duration
    return PeriodicOrbitMetrics(
        average_output_v=float(average[index["out"]]),
        average_load_power_w=float(weighted_load_power / duration),
        average_phase_currents_a=tuple(
            float(average[index[name]]) for name in phase_names
        ),  # type: ignore[arg-type]
        minimum_phase_currents_a=tuple(float(value) for value in phase_min),  # type: ignore[arg-type]
        maximum_phase_currents_a=tuple(float(value) for value in phase_max),  # type: ignore[arg-type]
        average_input_inductor_current_a=float(average[index["LPAR_IN"]]),
        average_flying_capacitor_v=(
            float(average[index["a1"]] - average[index["x1"]]),
            float(average[index["a2"]] - average[index["x2"]]),
            float(average[index["a3"]] - average[index["x3"]]),
        ),
    )
