"""D01: typed timing definitions, not a paper controller or event detector.

All definitions here are PROJECT_DECISION bookkeeping. Paper-label mappings
must be audited separately; a label such as t2 is never an event identity.
"""

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .evidence import Evidence


class TimingKind(str, Enum):
    NOMINAL_ON = "nominal_on"
    NOMINAL_OFF = "nominal_off"
    COMMAND_ON = "command_on"
    COMMAND_OFF = "command_off"
    GATE_ON = "effective_gate_on"
    GATE_OFF = "effective_gate_off"
    VDS_ZERO = "vds_zero"
    REVERSE_CONDUCTION = "reverse_conduction_start"


@dataclass(frozen=True)
class TimingContext:
    branch: str
    run_id: str
    clock_id: str
    nP: int
    nM: int
    module: int
    phase: int
    cycle: int

    def __post_init__(self):
        if self.branch not in {"P24", "P25", "P24_PLUS_P25"}:
            raise ValueError("explicit evidence branch required")
        if not self.run_id.strip() or not self.clock_id.strip():
            raise ValueError("run and absolute clock identifiers required")
        for name in ("nP", "nM", "module", "phase", "cycle"):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == "cycle" else 1):
                raise ValueError(f"invalid {name}")
        if self.phase > self.nP or self.module > self.nM:
            raise ValueError("phase/module outside architecture")


@dataclass(frozen=True)
class TimingEvent:
    context: TimingContext
    switch: str  # H or L in context.phase, not a paper's t-number
    kind: TimingKind
    time_s: float | None
    evidence: Evidence
    source: str  # source location OR explicitly named modeling assumption

    def __post_init__(self):
        if self.switch not in {"H", "L"}:
            raise ValueError("switch must be H or L")
        if not isinstance(self.kind, TimingKind) or not isinstance(self.evidence, Evidence):
            raise ValueError("typed kind/evidence required")
        if not self.source.strip():
            raise ValueError("source or assumption must be explicit")
        if self.time_s is not None and not isfinite(self.time_s):
            raise ValueError("time must be finite or explicitly unknown")


class DurationKind(str, Enum):
    NOMINAL_ON = "nominal_on_duration"
    COMMAND_ON = "command_on_duration"
    GATE_ON = "effective_gate_on_duration"
    COMMAND_DEADTIME = "command_deadtime"
    GATE_DEADTIME = "effective_gate_deadtime"
    COMMUTATION = "off_to_opposite_vds_zero"


_ENDPOINTS = {
    DurationKind.NOMINAL_ON: (TimingKind.NOMINAL_ON, TimingKind.NOMINAL_OFF, False),
    DurationKind.COMMAND_ON: (TimingKind.COMMAND_ON, TimingKind.COMMAND_OFF, False),
    DurationKind.GATE_ON: (TimingKind.GATE_ON, TimingKind.GATE_OFF, False),
    DurationKind.COMMAND_DEADTIME: (TimingKind.COMMAND_OFF, TimingKind.COMMAND_ON, True),
    DurationKind.GATE_DEADTIME: (TimingKind.GATE_OFF, TimingKind.GATE_ON, True),
    DurationKind.COMMUTATION: (TimingKind.GATE_OFF, TimingKind.VDS_ZERO, True),
}


def duration_s(kind: DurationKind, start: TimingEvent, end: TimingEvent) -> float:
    """One paired interval only; unknown events and cross-context pairs fail.

    Nonnegative deadtime only. Overlap is an error, not clipped to zero.
    This does not establish ZVS, conduction duration, or periodic closure.
    """
    if not isinstance(kind, DurationKind):
        raise ValueError("typed duration kind required")
    first, last, opposite = _ENDPOINTS[kind]
    if start.context != end.context:
        raise ValueError("cannot mix branch/run/clock/phase/module/cycle")
    if (start.kind, end.kind) != (first, last):
        raise ValueError("endpoint semantics do not match duration definition")
    if (start.switch != end.switch) != opposite:
        raise ValueError("incorrect switch pair")
    if start.time_s is None or end.time_s is None:
        raise ValueError("unknown event time is not zero")
    if Evidence.UNKNOWN_BLOCKING in (start.evidence, end.evidence):
        raise ValueError("unresolved evidence blocks evaluation")
    if end.time_s < start.time_s:
        raise ValueError("negative duration or unpaired events")
    return end.time_s - start.time_s
