"""Capability-driven assembly with P24-first selection and hard blockers."""

from __future__ import annotations

from evidence import Evidence
from model_contracts import AssemblyPlan, ExperimentRequest, Module, Slot
from module_registry import MODULES


EVIDENCE_PRIORITY = {
    Evidence.P24_EXPLICIT: 0,
    Evidence.P24_DERIVED: 1,
    Evidence.P25_SUPPLEMENT: 2,
    Evidence.CROSS_PAPER_EXTENSION: 3,
    Evidence.EXTERNAL_DEVICE_DATA: 4,
    Evidence.PROJECT_DECISION: 5,
    Evidence.EXPLORATORY_ASSUMPTION: 6,
    Evidence.UNKNOWN_BLOCKING: 99,
}


def _eligible(
    request: ExperimentRequest, modules: tuple[Module, ...]
) -> tuple[Module, ...]:
    return tuple(
        module
        for module in modules
        if module.evidence in request.allowed_evidence
        and module.evidence is not Evidence.UNKNOWN_BLOCKING
    )


def assemble(
    request: ExperimentRequest, modules: tuple[Module, ...] = MODULES
) -> AssemblyPlan:
    """Assemble from any supplied catalogue; MODULES is only the default."""

    eligible = _eligible(request, modules)
    selected: list[Module] = []
    provided: set[str] = set()
    slot_conflicts: set[str] = set()

    # Explicit module choices are the only way to override normal priority.
    for slot, module_id in request.preferred_modules.items():
        try:
            module = next(m for m in modules if m.module_id == module_id)
        except StopIteration as exc:
            raise KeyError(module_id) from exc
        if module.slot is not slot:
            raise ValueError(f"{module_id} does not belong to slot {slot.value}")
        if module.evidence not in request.allowed_evidence:
            raise ValueError(f"evidence for {module_id} is not allowed")
        selected.append(module)
        provided.update(module.provides)

    # Resolve the dependency closure. A newly selected module may introduce
    # new required capabilities, which are then filled by another slot.
    needed = set(request.required_capabilities)
    for module in selected:
        needed.update(module.requires)
    while True:
        added = False
        for capability in sorted(needed - provided):
            if capability in provided:
                continue
            candidates = [m for m in eligible if capability in m.provides]
            candidates.sort(key=lambda m: EVIDENCE_PRIORITY[m.evidence])
            occupied_candidates = []
            for candidate in candidates:
                if any(m.slot is candidate.slot for m in selected):
                    occupied_candidates.append(candidate)
                    continue
                selected.append(candidate)
                provided.update(candidate.provides)
                needed.update(candidate.requires)
                added = True
                break
            else:
                if occupied_candidates:
                    occupant = next(
                        m for m in selected if m.slot is occupied_candidates[0].slot
                    )
                    slot_conflicts.add(
                        f"slot:{occupant.slot.value}:{occupant.module_id}"
                        f"|{occupied_candidates[0].module_id}"
                    )
        if not added:
            break

    missing = needed - provided

    conflicts: set[str] = set(slot_conflicts)
    selected_ids = {m.module_id for m in selected}
    for module in selected:
        for conflict_capability in module.conflicts_with & provided:
            if conflict_capability in module.provides:
                conflicts.add(
                    f"self-conflict:{module.module_id}:{conflict_capability}"
                )
                continue
            key = f"{module.module_id}:{conflict_capability}"
            chosen = request.conflict_choices.get(key)
            if chosen not in selected_ids:
                conflicts.add(key)

    return AssemblyPlan(
        experiment_id=request.experiment_id,
        selected_modules=tuple(selected),
        missing_capabilities=tuple(sorted(missing)),
        unresolved_conflicts=tuple(sorted(conflicts)),
    )
