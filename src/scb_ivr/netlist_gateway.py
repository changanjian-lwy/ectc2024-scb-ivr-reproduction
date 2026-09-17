"""The only allowed gateway from an AssemblyPlan to a generated netlist."""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.model_contracts import AssemblyPlan, NetlistEmitter


@dataclass(frozen=True)
class NetlistGenerationResult:
    generated: bool
    text: str | None
    blockers: tuple[str, ...]


def generate_netlist(
    plan: AssemblyPlan,
    parameters: dict[str, float],
    emitter: NetlistEmitter,
) -> NetlistGenerationResult:
    if not plan.ready:
        blockers = tuple(
            [f"missing:{item}" for item in plan.missing_capabilities]
            + [f"conflict:{item}" for item in plan.unresolved_conflicts]
        )
        return NetlistGenerationResult(False, None, blockers)

    provenance_header = [
        "* GENERATED THROUGH MODULAR ASSEMBLY GATEWAY",
        f"* experiment_id={plan.experiment_id}",
    ]
    for module in plan.selected_modules:
        provenance_header.append(
            f"* module={module.module_id} evidence={module.evidence.value} "
            f"source={module.source} location={module.location}"
        )
    body = emitter(plan, parameters)
    return NetlistGenerationResult(
        True, "\n".join(provenance_header) + "\n" + body, ()
    )
