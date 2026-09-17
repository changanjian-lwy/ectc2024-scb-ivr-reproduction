"""Run the Track-B theoretical solver for one period at decreasing step size."""

from __future__ import annotations

import json

from scb_ivr.zero_start_descriptor import (
    ZeroStartBoundary,
    assemble_descriptor,
    input_voltage_v,
)
from scb_ivr.zero_start_hybrid_solver import simulate_zero_start


STEP_SIZES_S = (2e-9, 1e-9, 0.5e-9, 0.25e-9, 0.125e-9, 0.0625e-9)
OBSERVABLES = ("a1", "a2", "a3", "out", "L1", "L2", "L3", "L4")


def build_report() -> dict:
    boundary = ZeroStartBoundary()
    rows = []
    for step_size in STEP_SIZES_S:
        trajectory = simulate_zero_start(
            boundary,
            stop_time_s=boundary.period_s,
            maximum_step_s=step_size,
        )
        system = assemble_descriptor(
            boundary,
            trajectory.final.mode,
            trajectory.final.time_s,
        )
        index = {name: position for position, name in enumerate(system.variable_names)}
        rows.append(
            {
                "maximum_step_ns": step_size * 1e9,
                "accepted_steps": len(trajectory.steps) - 1,
                "diode_transitions": trajectory.diode_transition_count,
                "maximum_descriptor_residual": max(
                    step.descriptor_residual_inf for step in trajectory.steps
                ),
                "final": {
                    name: float(trajectory.final.state[index[name]])
                    for name in OBSERVABLES
                },
            }
        )
    return {
        "classification": "THEORETICAL_SOLVER_CONVERGENCE_ONLY",
        "boundary": {
            "input_ramp_s": boundary.input_ramp_s,
            "one_period_s": boundary.period_s,
            "source_command_at_period_end_v": input_voltage_v(
                boundary.period_s, boundary
            ),
            "not_claimed": [
                "startup success",
                "P24 hardware reproduction",
                "long-time convergence",
            ],
        },
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
