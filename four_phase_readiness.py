"""Diagnose, but do not bypass, gaps in the P24 single-module four-phase run."""

from __future__ import annotations

import json
from pathlib import Path

from assembly_planner import assemble
from evidence import Evidence
from model_contracts import ExperimentRequest


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/diagnostics/P24_single_module_four_phase_readiness.json"

CAPABILITY_OWNER = {
    "complete_four_phase_gate_vector": "sequence/controller interface",
    "commutation_capacitance": "device/commutation slot",
    "dead_time": "controller/device slot",
    "negative_current_detector": "controller slot",
    "startup_initialization": "startup slot",
}


P24_SINGLE_MODULE_FOUR_PHASE = ExperimentRequest(
    experiment_id="P24_SINGLE_MODULE_FOUR_PHASE",
    required_capabilities=frozenset(
        {
            "four_phase_power_topology",
            "duty",
            "on_time",
            "phase_peak_current",
            "critical_inductance",
            "phase_local_three_interval_sequence",
            "symbolic_coss_commutation",
            "complete_four_phase_gate_vector",
            "commutation_capacitance",
            "dead_time",
            "negative_current_detector",
            "startup_initialization",
        }
    ),
    allowed_evidence=frozenset(
        {
            Evidence.P24_EXPLICIT,
            Evidence.P24_DERIVED,
            Evidence.P25_SUPPLEMENT,
            Evidence.PROJECT_DECISION,
        }
    ),
)


def readiness_report() -> dict:
    plan = assemble(P24_SINGLE_MODULE_FOUR_PHASE)
    return {
        "experiment_id": plan.experiment_id,
        "ready": plan.ready,
        "selected_modules": [
            {
                "slot": module.slot.value,
                "module": module.module_id,
                "evidence": module.evidence.value,
            }
            for module in plan.selected_modules
        ],
        "missing": [
            {
                "capability": capability,
                "responsible_slot": CAPABILITY_OWNER.get(
                    capability, "unassigned interface"
                ),
            }
            for capability in plan.missing_capabilities
        ],
        "conflicts": list(plan.unresolved_conflicts),
        "action": (
            "do not generate publication-locked SPICE"
            if not plan.ready
            else "eligible for netlist emission; electrical checks still required"
        ),
    }


def main() -> None:
    result = readiness_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
