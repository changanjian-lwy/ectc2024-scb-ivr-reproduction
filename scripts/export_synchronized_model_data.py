"""Export synchronized four-phase event data as JSON and flat CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scb_ivr.model_data_export import export_model_dataset
from scb_ivr.periodic_affine_solver import (
    build_affine_period_map,
    solve_periodic_fixed_point,
)
from scb_ivr.zero_start_descriptor import ZeroStartBoundary


def _flat_event_row(snapshot: dict[str, object]) -> dict[str, object]:
    global_state = snapshot["global"]
    assert isinstance(global_state, dict)
    phases = snapshot["phases"]
    assert isinstance(phases, list)
    raw_state = snapshot["raw_state_by_variable"]
    assert isinstance(raw_state, dict)
    diodes = snapshot["precharge_diodes"]
    assert isinstance(diodes, list)
    row: dict[str, object] = {
        "label": snapshot["label"],
        "absolute_time_s": snapshot["absolute_time_s"],
        "relative_time_s": snapshot["relative_time_s"],
        "sampling_side": snapshot["sampling_side"],
        "transition_phase": snapshot["transition_phase"],
        "transition": snapshot["transition"],
        **global_state,
    }
    for name, value in raw_state.items():
        row[f"raw_{name}"] = value
    for diode in diodes:
        assert isinstance(diode, dict)
        prefix = f"precharge_diode{diode['diode']}_"
        row[prefix + "on_left_limit"] = diode["on_left_limit"]
        row[prefix + "anode_minus_cathode_v"] = diode["anode_minus_cathode_v"]
        row[prefix + "reliability"] = diode["reliability"]
    for phase in phases:
        assert isinstance(phase, dict)
        prefix = f"phase{phase['phase']}_"
        for key in (
            "high_side_on_left_limit",
            "low_side_on_left_limit",
            "switch_node_v",
            "high_side_voltage_first_minus_second_v",
            "low_side_voltage_first_minus_ground_v",
            "inductor_current_first_to_second_a",
            "inductor_voltage_first_minus_second_v",
            "flying_capacitor_voltage_first_minus_second_v",
        ):
            row[prefix + key] = phase[key]
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-ns", type=float, default=0.0625)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()
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
    dataset = export_model_dataset(boundary, fixed)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(dataset, indent=2) + "\n")
    rows = [_flat_event_row(item) for item in dataset["event_snapshots"]]
    with args.csv_output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
