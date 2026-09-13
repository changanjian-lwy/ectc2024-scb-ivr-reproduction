"""Stable interfaces for assembling paper-aware IVR experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from evidence import Evidence


class Slot(str, Enum):
    TOPOLOGY = "topology"
    ANALYTICAL = "analytical"
    SEQUENCE = "sequence"
    COMMUTATION = "commutation"
    CONTROLLER = "controller"
    STARTUP = "startup"
    DEVICE = "device"
    BOUNDARY = "boundary"
    NUMERICAL_ENGINE = "numerical_engine"


@dataclass(frozen=True)
class Module:
    module_id: str
    slot: Slot
    evidence: Evidence
    source: str
    location: str
    provides: frozenset[str]
    requires: frozenset[str] = frozenset()
    conflicts_with: frozenset[str] = frozenset()
    payload: Any = None
    note: str = ""


@dataclass(frozen=True)
class ExperimentRequest:
    experiment_id: str
    required_capabilities: frozenset[str]
    allowed_evidence: frozenset[Evidence]
    preferred_modules: dict[Slot, str] = field(default_factory=dict)
    conflict_choices: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AssemblyPlan:
    experiment_id: str
    selected_modules: tuple[Module, ...]
    missing_capabilities: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.missing_capabilities and not self.unresolved_conflicts

    def require_ready(self) -> None:
        problems = []
        if self.missing_capabilities:
            problems.append("missing=" + ",".join(self.missing_capabilities))
        if self.unresolved_conflicts:
            problems.append("conflicts=" + ",".join(self.unresolved_conflicts))
        if problems:
            raise RuntimeError(
                f"experiment {self.experiment_id} is not assemblable: "
                + "; ".join(problems)
            )


NetlistEmitter = Callable[[AssemblyPlan, dict[str, float]], str]
