"""Solve the fixed-diode affine period map at selected BE step sizes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scb_ivr.periodic_affine_solver import (
    build_affine_period_map,
    periodic_orbit_metrics,
    solve_periodic_fixed_point,
)
from scb_ivr.zero_start_descriptor import ZeroStartBoundary, assemble_descriptor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-ns", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.step_ns <= 0:
        parser.error("step size must be positive")

    boundary = ZeroStartBoundary()
    start_time_s = (
        int(boundary.input_ramp_s / boundary.period_s) + 1
    ) * boundary.period_s
    period_map = build_affine_period_map(
        boundary,
        start_time_s=start_time_s,
        maximum_step_s=args.step_ns * 1e-9,
    )
    fixed = solve_periodic_fixed_point(boundary, period_map)
    metrics = periodic_orbit_metrics(boundary, fixed)
    system = assemble_descriptor(
        boundary, fixed.orbit.steps[0].mode, start_time_s
    )
    named_state = {
        name: float(value)
        for name, value in zip(system.variable_names, fixed.state, strict=True)
    }
    report = {
        "classification": "THEORETICAL_FIXED_DIODE_AFFINE_PERIOD_AUDIT",
        "maximum_step_ns": args.step_ns,
        "start_time_us": start_time_s * 1e6,
        "map_size": int(period_map.matrix.shape[0]),
        "least_squares_rank": fixed.least_squares_rank,
        "numerical_nullity": int(
            period_map.matrix.shape[0] - fixed.least_squares_rank
        ),
        "singular_values": [float(value) for value in fixed.singular_values],
        "fixed_point_residual_inf": fixed.fixed_point_residual_inf,
        "orbit_closure_inf": fixed.orbit_closure_inf,
        "diode_complementarity_valid": fixed.diode_complementarity_valid,
        "maximum_off_diode_forward_voltage_v": (
            fixed.maximum_off_diode_forward_voltage_v
        ),
        "minimum_norm_state_by_variable": named_state,
        "period_metrics": {
            "average_output_v": metrics.average_output_v,
            "average_load_power_w": metrics.average_load_power_w,
            "average_phase_currents_a": metrics.average_phase_currents_a,
            "minimum_phase_currents_a": metrics.minimum_phase_currents_a,
            "maximum_phase_currents_a": metrics.maximum_phase_currents_a,
            "average_input_inductor_current_a": (
                metrics.average_input_inductor_current_a
            ),
            "average_flying_capacitor_v": metrics.average_flying_capacitor_v,
        },
        "warning": (
            "Rank deficiency represents the isolated divider-charge slow "
            "coordinates; their minimum-norm voltages are not a physical "
            "startup steady state."
        ),
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
