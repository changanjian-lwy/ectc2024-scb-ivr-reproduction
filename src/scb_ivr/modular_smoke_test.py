"""Two tiny assembly checks: one valid case and one deliberate landmine."""

from __future__ import annotations

from scb_ivr.assembly_planner import assemble
from scb_ivr.evidence import Evidence
from scb_ivr.model_contracts import ExperimentRequest, Module, Slot
from scb_ivr.module_registry import MODULES


def run_smoke_test() -> dict:
    valid_request = ExperimentRequest(
        experiment_id="SMOKE_VALID_P24_ANALYTICAL",
        required_capabilities=frozenset({"duty", "critical_inductance"}),
        allowed_evidence=frozenset({Evidence.P24_EXPLICIT}),
    )
    valid_plan = assemble(valid_request)

    # DELIBERATE TEST-ONLY LANDMINE:
    # This module falsely packages two incompatible sequence semantics as one
    # convenient implementation. Its own conflicts_with declaration must make
    # the planner reject it even though all requested capabilities appear filled.
    trapped_sequence = Module(
        module_id="TEST_ONLY_TRAP_mixed_p24_p25_sequence",
        slot=Slot.SEQUENCE,
        evidence=Evidence.EXPLORATORY_ASSUMPTION,
        source="TEST FIXTURE - NOT A PAPER",
        location="modular_smoke_test.py",
        provides=frozenset(
            {
                "phase_local_three_interval_sequence",
                "p25_cross_phase_handoff_sequence",
            }
        ),
        conflicts_with=frozenset(
            {
                "phase_local_three_interval_sequence",
                "p25_cross_phase_handoff_sequence",
            }
        ),
        note="Deliberate self-conflicting module; must never assemble.",
    )
    trapped_request = ExperimentRequest(
        experiment_id="SMOKE_TRAPPED_MIXED_SEQUENCE",
        required_capabilities=frozenset(
            {
                "phase_local_three_interval_sequence",
                "p25_cross_phase_handoff_sequence",
            }
        ),
        allowed_evidence=frozenset({Evidence.EXPLORATORY_ASSUMPTION}),
    )
    trapped_plan = assemble(trapped_request, (trapped_sequence,))

    return {
        "valid_case": {
            "ready": valid_plan.ready,
            "modules": [m.module_id for m in valid_plan.selected_modules],
            "missing": list(valid_plan.missing_capabilities),
            "conflicts": list(valid_plan.unresolved_conflicts),
        },
        "landmine_case": {
            "ready": trapped_plan.ready,
            "modules": [m.module_id for m in trapped_plan.selected_modules],
            "missing": list(trapped_plan.missing_capabilities),
            "conflicts": list(trapped_plan.unresolved_conflicts),
            "detected": (
                not trapped_plan.ready
                and any(
                    item.startswith("self-conflict:")
                    for item in trapped_plan.unresolved_conflicts
                )
            ),
        },
    }


if __name__ == "__main__":
    result = run_smoke_test()
    print(result)
    if not result["valid_case"]["ready"]:
        raise SystemExit("valid modular case unexpectedly failed")
    if not result["landmine_case"]["detected"]:
        raise SystemExit("deliberate landmine was not detected")
