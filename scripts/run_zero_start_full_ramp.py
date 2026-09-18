"""Run a memory-bounded theoretical zero-start ramp and write JSON results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scb_ivr.zero_start_descriptor import ZeroStartBoundary
from scb_ivr.zero_start_hybrid_solver import (
    continue_zero_start_poincare,
    named_hybrid_state,
    simulate_zero_start_checkpoints,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-ns", type=float, choices=(0.125, 0.0625), default=0.125)
    parser.add_argument("--checkpoint-periods", type=int, default=5)
    parser.add_argument("--post-ramp-periods", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    boundary = ZeroStartBoundary()
    summary = simulate_zero_start_checkpoints(
        boundary,
        boundary.input_ramp_s,
        args.step_ns * 1e-9,
        checkpoint_every_periods=args.checkpoint_periods,
    )
    final_state = named_hybrid_state(summary.final_step, boundary)
    report = {
        "classification": "THEORETICAL_FULL_RAMP_NOT_P24_STARTUP_REPRODUCTION",
        "maximum_step_ns": args.step_ns,
        "diode_transition_count": summary.diode_transition_count,
        "maximum_descriptor_residual": summary.maximum_descriptor_residual_inf,
        "maximum_descriptor_relative_backward_error": (
            summary.maximum_descriptor_relative_backward_error
        ),
        "maximum_abs_phase_current_a": summary.maximum_abs_phase_current_a,
        "maximum_abs_input_inductor_current_a": (
            summary.maximum_abs_input_inductor_current_a
        ),
        "maximum_output_v": summary.maximum_output_v,
        "final_time_us": summary.final_step.time_s * 1e6,
        "final_mode": {
            "high_side_on": summary.final_step.mode.high_side_on,
            "precharge_diode_on": summary.final_step.mode.precharge_diode_on,
        },
        "final_state_by_variable": final_state,
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
    if args.post_ramp_periods:
        continuation = continue_zero_start_poincare(
            boundary,
            summary.final_step,
            args.post_ramp_periods,
            args.step_ns * 1e-9,
        )
        report["post_ramp_poincare"] = {
            "sampling_section": "left limit before phase-1 high-side rising edge",
            "periods": args.post_ramp_periods,
            "diode_transition_count": continuation.diode_transition_count,
            "maximum_descriptor_residual": (
                continuation.maximum_descriptor_residual_inf
            ),
            "maximum_descriptor_relative_backward_error": (
                continuation.maximum_descriptor_relative_backward_error
            ),
            "final_time_us": continuation.final_step.time_s * 1e6,
            "final_mode": {
                "high_side_on": continuation.final_step.mode.high_side_on,
                "precharge_diode_on": (
                    continuation.final_step.mode.precharge_diode_on
                ),
            },
            "final_state_by_variable": named_hybrid_state(
                continuation.final_step, boundary
            ),
            "samples": [
                {
                    "sample_index": sample.sample_index,
                    "time_us": sample.checkpoint.time_s * 1e6,
                    "flying_capacitor_v": sample.checkpoint.flying_capacitor_v,
                    "output_v": sample.checkpoint.output_v,
                    "phase_currents_a": sample.checkpoint.phase_currents_a,
                    "input_inductor_current_a": (
                        sample.checkpoint.input_inductor_current_a
                    ),
                    "diode_state": sample.diode_state,
                }
                for sample in continuation.samples
            ],
        }
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
