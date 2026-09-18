"""Run a memory-bounded theoretical zero-start ramp and write JSON results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scb_ivr.zero_start_descriptor import ZeroStartBoundary
from scb_ivr.zero_start_hybrid_solver import simulate_zero_start_checkpoints


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-ns", type=float, choices=(0.125, 0.0625), default=0.125)
    parser.add_argument("--checkpoint-periods", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    boundary = ZeroStartBoundary()
    summary = simulate_zero_start_checkpoints(
        boundary,
        boundary.input_ramp_s,
        args.step_ns * 1e-9,
        checkpoint_every_periods=args.checkpoint_periods,
    )
    report = {
        "classification": "THEORETICAL_FULL_RAMP_NOT_P24_STARTUP_REPRODUCTION",
        "maximum_step_ns": args.step_ns,
        "diode_transition_count": summary.diode_transition_count,
        "maximum_descriptor_residual": summary.maximum_descriptor_residual_inf,
        "maximum_abs_phase_current_a": summary.maximum_abs_phase_current_a,
        "maximum_abs_input_inductor_current_a": (
            summary.maximum_abs_input_inductor_current_a
        ),
        "maximum_output_v": summary.maximum_output_v,
        "checkpoints": [
            {
                "time_us": point.time_s * 1e6,
                "completed_periods": point.completed_periods,
                "input_command_v": point.input_command_v,
                "flying_capacitor_v": point.flying_capacitor_v,
                "output_v": point.output_v,
                "phase_currents_a": point.phase_currents_a,
                "input_inductor_current_a": point.input_inductor_current_a,
                "cumulative_diode_transitions": point.cumulative_diode_transitions,
            }
            for point in summary.checkpoints
        ],
        "diode_transitions": [
            {
                "time_us": event.time_s * 1e6,
                "previous": event.previous_state,
                "next": event.next_state,
            }
            for event in summary.diode_transitions
        ],
    }
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
