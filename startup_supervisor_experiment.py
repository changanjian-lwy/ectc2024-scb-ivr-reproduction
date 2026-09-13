"""Emit reproducible R04E0 static startup-supervisor experiment results."""

from __future__ import annotations

import json
from pathlib import Path

from startup_voltage_supervisor import StartupObservation, evaluate_startup_readiness


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/diagnostics/R04E0_startup_supervisor_static.json"


CASES = {
    "E0_reference_periodic_candidate": ((36.0, 24.0, 12.0), (0.0,) * 4),
    "E1_shifted_but_balanced": ((37.0, 25.0, 13.0), (0.0,) * 4),
    "E2_planted_absolute_voltage_trap": ((39.0, 21.0, 15.0), (0.0,) * 4),
    "E3_voltage_ready_but_current_unsafe": ((36.0, 24.0, 12.0), (0.0, 0.0, 1.01, 0.0)),
    "E4_zero_initial_energy": ((0.0, 0.0, 0.0), (0.0,) * 4),
}


def main() -> None:
    rows = []
    for case_id, (nodes, currents) in CASES.items():
        decision = evaluate_startup_readiness(StartupObservation(48.0, nodes, currents))
        rows.append(
            {
                "case_id": case_id,
                "changed_variable_vs_E0": {
                    "ladder_nodes_v": nodes,
                    "phase_currents_a": currents,
                },
                "segments_v": decision.segment_voltages_v,
                "window_v": decision.allowed_segment_window_v,
                "release": decision.release,
                "reason": decision.reason.value,
                "evidence": decision.evidence.value,
            }
        )
    payload = {
        "experiment": "R04E0_STARTUP_SUPERVISOR_STATIC_ONLY",
        "claim_boundary": (
            "Observer-only exploratory controller. No P24 power switch is driven; "
            "no zero-start voltage build-up is claimed."
        ),
        "fixed_boundary": {"vin_v": 48.0, "n_p": 4, "target_segment_v": 12.0},
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
