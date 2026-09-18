"""Resume a saved full-state checkpoint and audit a post-ramp period map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scb_ivr.zero_start_descriptor import ZeroStartBoundary
from scb_ivr.zero_start_hybrid_solver import (
    continue_zero_start_poincare,
    hybrid_step_from_named_state,
    named_hybrid_state,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--periods", type=int, required=True)
    parser.add_argument("--step-ns", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.periods <= 0 or args.step_ns <= 0:
        parser.error("periods and step size must be positive")

    source = json.loads(args.checkpoint.read_text())
    boundary = ZeroStartBoundary()
    mode = source["final_mode"]
    initial = hybrid_step_from_named_state(
        boundary,
        time_s=float(source["final_time_us"]) * 1e-6,
        state_by_variable=source["final_state_by_variable"],
        high_side_on=tuple(mode["high_side_on"]),
        precharge_diode_on=tuple(mode["precharge_diode_on"]),
    )
    summary = continue_zero_start_poincare(
        boundary,
        initial,
        args.periods,
        args.step_ns * 1e-9,
    )
    report = {
        "classification": "EXPLORATORY_POST_RAMP_POINCARE_MAP",
        "source_checkpoint": str(args.checkpoint),
        "maximum_step_ns": args.step_ns,
        "periods": args.periods,
        "sampling_section": "left limit before phase-1 high-side rising edge",
        "diode_transition_count": summary.diode_transition_count,
        "maximum_descriptor_residual": summary.maximum_descriptor_residual_inf,
        "maximum_descriptor_relative_backward_error": (
            summary.maximum_descriptor_relative_backward_error
        ),
        "final_time_us": summary.final_step.time_s * 1e6,
        "final_mode": {
            "high_side_on": summary.final_step.mode.high_side_on,
            "precharge_diode_on": summary.final_step.mode.precharge_diode_on,
        },
        "final_state_by_variable": named_hybrid_state(summary.final_step, boundary),
        "samples": [
            {
                "sample_index": sample.sample_index,
                "time_us": sample.checkpoint.time_s * 1e6,
                "flying_capacitor_v": sample.checkpoint.flying_capacitor_v,
                "output_v": sample.checkpoint.output_v,
                "phase_currents_a": sample.checkpoint.phase_currents_a,
                "input_inductor_current_a": sample.checkpoint.input_inductor_current_a,
                "diode_state": sample.diode_state,
            }
            for sample in summary.samples
        ],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
