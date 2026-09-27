"""D02: P25 native three-phase first handoff, defined by physical events.

Sources: APEC 2025, DOI 10.1109/APEC48143.2025.10977125,
Sec. II, Figs. 1-3, printed pp. 2102-2104. No paper t-number is an ID.
This is a specification/trace-order checker, NOT an electrical solver.
"""
from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .evidence import Evidence


class Event(str, Enum):
    H1_ON = "SH1_effective_on"
    H1_OFF = "SH1_effective_off"
    L1_ZERO = "SL1_vds_zero_reached"
    L1_ON = "SL1_effective_on"
    I2_ZERO = "iL2_downward_zero_crossing"
    I2_TARGET = "iL2_negative_target_reached"
    L2_OFF = "SL2_effective_off"
    H2_ZERO = "SH2_vds_zero_reached"
    H2_ON = "SH2_effective_on"
    H2_OFF = "SH2_effective_off"


@dataclass(frozen=True)
class NativeBoundary:
    nP: int
    nM: int  # total system modules retained, even when tracing one module
    module: int
    output_boundary: str  # externally provided, e.g. unresolved/shared bus model
    alpha: float  # explicit Mode-4 choice; no default or automatic optimization
    branch: str = "P25"

    def __post_init__(self):
        if self.branch != "P25" or type(self.nP) is not int or self.nP != 3:
            raise ValueError("P25 native contract requires P25 and nP=3; no four-phase extension")
        if type(self.nM) is not int or self.nM < 1:
            raise ValueError("nM must be explicit and positive")
        if type(self.module) is not int or not 1 <= self.module <= self.nM:
            raise ValueError("module outside system")
        if not self.output_boundary.strip():
            raise ValueError("output boundary must be declared, not silently clamped")
        if not isfinite(self.alpha) or not 0.05 <= self.alpha <= 0.10:
            raise ValueError("Mode-4 native alpha must lie in published 5%-10% range")


@dataclass(frozen=True)
class PeakReference:
    phase: int
    amperes: float
    basis: str
    source: str

    def __post_init__(self):
        if type(self.phase) is not int or not 1 <= self.phase <= 3:
            raise ValueError("peak phase must be 1, 2 or 3")
        if not isfinite(self.amperes) or self.amperes <= 0:
            raise ValueError("peak magnitude must be positive and finite")
        if self.basis not in {"previous_measured_peak", "declared_design_peak"}:
            raise ValueError("causal peak reference required; no future peak")
        if not self.source.strip():
            raise ValueError("peak reference provenance required")


@dataclass(frozen=True)
class GateState:
    # Effective channel commands in ideal paper modes, not total conduction paths.
    high: tuple[bool, bool, bool]
    low: tuple[bool, bool, bool]

    def __post_init__(self):
        if len(self.high) != 3 or len(self.low) != 3:
            raise ValueError("three phases required")
        if any(type(x) is not bool for x in (*self.high, *self.low)):
            raise ValueError("gate states must be explicit booleans")
        if sum(self.high) > 1 or any(h and l for h, l in zip(self.high, self.low)):
            raise ValueError("overlapping gates outside P25 mode contract")


@dataclass(frozen=True)
class ModeSpec:
    name: str
    gates: GateState
    entry: Event
    exit: Event
    physical_condition: str
    current_description: tuple[str, str, str]
    source: str
    source_evidence: Evidence = Evidence.P25_EXPLICIT
    contract_evidence: Evidence = Evidence.PROJECT_DECISION


MODES = (
    ModeSpec("M1", GateState((True, False, False), (False, True, True)),
             Event.H1_ON, Event.H1_OFF, "SH1 prescribed on interval ends; duration not assigned here",
             ("rises", "freewheels and decreases", "freewheels and decreases"), "p2102 Interval 1; Fig3 M1"),
    ModeSpec("M2", GateState((False, False, False), (False, True, True)),
             Event.H1_OFF, Event.L1_ZERO, "vDS(SL1) reaches zero during commutation",
             ("positive; nearly constant is a local approximation", "continues", "continues"), "pp2102-2103 Interval 2; Fig3 M2"),
    ModeSpec("M2_PRIME_OPTIONAL", GateState((False, False, False), (False, True, True)),
             Event.L1_ZERO, Event.L1_ON, "possible SL1 reverse conduction before gate-on; not mandatory",
             ("continuous; not reset", "continues", "continues"), "pp2102-2103 Interval 2; Fig3 M2-prime"),
    ModeSpec("M3", GateState((False, False, False), (True, True, True)),
             Event.L1_ON, Event.I2_ZERO, "iL2 crosses zero downward, not iL1",
             ("positive and decreases", "decreases to zero", "positive and decreases"), "p2103 Interval 3, Eqs7-10; Fig3 M3"),
    ModeSpec("M4", GateState((False, False, False), (True, True, True)),
             Event.I2_ZERO, Event.I2_TARGET, "iL2 = -alpha*Ipk2_ref; control requests SL2 off",
             ("positive and decreases", "becomes negative", "positive and decreases"), "p2103 Interval 4, Eq11; Fig3 M4"),
    ModeSpec("M5", GateState((False, False, False), (True, False, True)),
             Event.L2_OFF, Event.H2_ZERO, "vDS(SH2) reaches zero during commutation",
             ("continues", "negative drives commutation; not reset", "continues"), "p2104 Interval 5; Fig3 M5"),
    ModeSpec("M5_PRIME_OPTIONAL", GateState((False, False, False), (True, False, True)),
             Event.H2_ZERO, Event.H2_ON, "possible SH2 reverse conduction before gate-on; not mandatory",
             ("continues", "continuous; not reset", "continues"), "p2104 Interval 5; Fig3 M5-prime"),
    ModeSpec("M6", GateState((False, True, False), (True, False, True)),
             Event.H2_ON, Event.H2_OFF, "SH2 prescribed on interval ends; duration not assigned here",
             ("freewheels and decreases", "rises from actual entry current", "freewheels and decreases"), "p2104 Interval 6; Fig3 M6"),
)

# Separate the physical target, actual turn-off, Vds condition, and gate action.
# Separation does NOT invent any nonzero delay between these events.
FIRST_HANDOFF = (
    Event.H1_ON, Event.H1_OFF, Event.L1_ZERO, Event.L1_ON,
    Event.I2_ZERO, Event.I2_TARGET, Event.L2_OFF,
    Event.H2_ZERO, Event.H2_ON, Event.H2_OFF,
)


@dataclass(frozen=True)
class Occurrence:
    event: Event
    absolute_time_s: float


def validate_order(boundary: NativeBoundary, events: tuple[Occurrence, ...]) -> None:
    """Check one already-separated module/handoff trace, NOT physical feasibility.

    Caller supplies a trace from one run/clock/cycle. Root detection, gate-on
    voltage persistence, all-phase electrical state and evidence are separate
    unimplemented adapters. Prefixes are allowed; an empty trace is rejected.
    """
    if not isinstance(boundary, NativeBoundary):
        raise ValueError("native boundary object required")
    if not events or tuple(x.event for x in events) != FIRST_HANDOFF[:len(events)]:
        raise ValueError("wrong physical event order or missing separate event")
    times = tuple(x.absolute_time_s for x in events)
    if not all(isfinite(t) for t in times) or any(b < a for a, b in zip(times, times[1:])):
        raise ValueError("event times must be finite and nondecreasing")


def negative_target_a(boundary: NativeBoundary, reference: PeakReference) -> float:
    """Mode-4 signed target. Choice of reference basis is a project policy."""
    if reference.phase != 2:
        raise ValueError("first handoff requires phase-2 peak reference, not phase 1")
    return -boundary.alpha * reference.amperes


def negative_ramp_duration_s(*, inductance_h: float, vout_v: float,
                             reverse_drop_magnitude_v: float, target_a: float) -> float:
    """P25 Eq11-derived interval: -L*i_target/(Vo+Vreverse).

    Assumes iL2(entry)=0, constant positive L, constant output/drop, SL2 on.
    Vreverse is a NONNEGATIVE magnitude, not signed vDS (which is negative
    in reverse conduction). This freezes the paper's drop convention into
    negative current; it is NOT the signed resistive-channel equation.
    Omits winding R and nonlinear channel drop. For a resistive channel use
    L*di/dt=-Vo-R*i instead, with a separately derived crossing time.
    This ends at the target, not at Vds-zero or at a delayed gate-off.
    No claim about ZVS energy follows from this ramp.
    """
    values = (inductance_h, vout_v, reverse_drop_magnitude_v, target_a)
    if not all(isfinite(v) for v in values):
        raise ValueError("finite inputs required")
    if inductance_h <= 0 or vout_v <= 0 or reverse_drop_magnitude_v < 0 or target_a >= 0:
        raise ValueError("positive L/Vo, nonnegative drop magnitude, negative target required")
    return -inductance_h * target_a / (vout_v + reverse_drop_magnitude_v)
