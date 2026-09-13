"""Resolve P25 details only after checking the P24-first hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Resolution(str, Enum):
    P24_CONTROLS = "P24_CONTROLS"
    P25_FILLS_P24_SILENCE = "P25_FILLS_P24_SILENCE"
    CONFLICT_REQUIRES_DECISION = "CONFLICT_REQUIRES_DECISION"
    UNKNOWN_BLOCKING = "UNKNOWN_BLOCKING"


@dataclass(frozen=True)
class SequenceResolution:
    topic: str
    p24_statement: str
    p25_statement: str
    resolution: Resolution
    adopted_rule: str | None
    consequence: str


SEQUENCE_RESOLUTIONS = (
    SequenceResolution(
        "phase-1 energy interval",
        "QH1 and QS2 conduct; iL1 rises through Vin-QH1-C1-output",
        "SH1, SL2 and SL3 conduct in the three-phase example",
        Resolution.P25_FILLS_P24_SILENCE,
        "Keep QH1/QS2 from P24; P25 may identify other non-active low sides only as a supplement",
        "A four-phase fourth-low-side command remains an explicit extension, not a paper fact",
    ),
    SequenceResolution(
        "QH1 turn-off and QL1 ZVS commutation",
        "positive iL1 charges QH1 Coss and discharges QL1 Coss; QL1 may turn on losslessly",
        "Mode 2/2' supplies CH1/CL1 equations and a dead-time-dependent reverse-conduction submode",
        Resolution.P25_FILLS_P24_SILENCE,
        "P24 controls the mechanism; use P25 only for missing submode/equation structure",
        "Numeric timing remains blocked without CH1/CL1 and dead time",
    ),
    SequenceResolution(
        "third-interval boundary variable",
        "P24 follows iL1 through zero and negative current before returning QH1 to ZVS",
        "P25 Mode 3 ends when next-phase iL2 reaches zero, then Modes 4-6 prepare and start SH2",
        Resolution.CONFLICT_REQUIRES_DECISION,
        None,
        "Do not compile P25 Modes 3-6 as an automatic subdivision of P24 interval three",
    ),
    SequenceResolution(
        "negative-current magnitude",
        "P24: QL1 turns off at 1%-2% of phase peak in the negative direction",
        "P25 Mode 4: SL2 turns off at 5%-10%; Eq. (20) designs up to 5%",
        Resolution.CONFLICT_REQUIRES_DECISION,
        None,
        "Keep independent P24 and P25 branches; neither value overrides the other",
    ),
    SequenceResolution(
        "complete numeric commutation model",
        "P24 does not publish Coss/snubber values or dead time",
        "P25 gives equations and says added snubbers are used, but does not publish their numeric values",
        Resolution.UNKNOWN_BLOCKING,
        None,
        "A publication-locked numeric ZVS run cannot be generated",
    ),
)


def publication_sequence_ready() -> bool:
    """Only true after every conflict and blocking unknown has been resolved."""

    blocked = {
        Resolution.CONFLICT_REQUIRES_DECISION,
        Resolution.UNKNOWN_BLOCKING,
    }
    return not any(item.resolution in blocked for item in SEQUENCE_RESOLUTIONS)


def assert_publication_sequence_ready() -> None:
    unresolved = [
        item.topic
        for item in SEQUENCE_RESOLUTIONS
        if item.resolution
        in {Resolution.CONFLICT_REQUIRES_DECISION, Resolution.UNKNOWN_BLOCKING}
    ]
    if unresolved:
        raise RuntimeError(
            "publication-locked sequence is blocked by: " + ", ".join(unresolved)
        )
