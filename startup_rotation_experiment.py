"""Write an auditable logic-only trace for both startup rotation branches."""

from __future__ import annotations

import json
from pathlib import Path

from startup_rotation_controller import (
    RotationBranch,
    RotationController,
    StartupEvent,
    assert_gate_interlock,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/diagnostics/R04E3_rotation_controller_logic.json"

P24_EVENTS = (
    StartupEvent.ACTIVE_CURRENT_LIMIT,
    StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO,
    StartupEvent.ACTIVE_CURRENT_ZERO,
    StartupEvent.ACTIVE_NEGATIVE_TARGET,
    StartupEvent.ACTIVE_HIGH_SIDE_VDS_ZERO,
)
P25_EVENTS = (
    StartupEvent.ACTIVE_CURRENT_LIMIT,
    StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO,
    StartupEvent.NEXT_CURRENT_ZERO,
    StartupEvent.NEXT_NEGATIVE_TARGET,
    StartupEvent.NEXT_HIGH_SIDE_VDS_ZERO,
)


def trace(branch: RotationBranch, rotations: int) -> list[dict]:
    controller = RotationController(4, branch)
    rows = []
    events = P24_EVENTS if branch is RotationBranch.P24_MINIMAL else P25_EVENTS
    for _ in range(rotations):
        for event in events:
            before = controller
            controller = controller.transition(event)
            assert_gate_interlock(controller)
            rows.append(
                {
                    "event": event.value,
                    "from": before.state.value,
                    "to": controller.state.value,
                    "active_phase": controller.active_phase,
                    "commanded_on": controller.commanded_on(),
                    "evidence": controller.evidence.value,
                }
            )
        if branch is RotationBranch.P24_MINIMAL:
            break
    return rows


def main() -> None:
    payload = {
        "claim_boundary": "logic-only; electrical feasibility is tested separately in R04E3 SPICE",
        "p24_minimal": trace(RotationBranch.P24_MINIMAL, 1),
        "p25_to_p24_four_phase_extension": trace(
            RotationBranch.P25_TO_P24_FOUR_PHASE_EXTENSION, 4
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

