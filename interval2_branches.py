"""Separate P24 and P25 interval-2 labels over related physical events."""

from __future__ import annotations

from dataclasses import dataclass

from evidence import Evidence
from physical_events import EventId


@dataclass(frozen=True)
class Interval2Branch:
    branch_id: str
    start_event: str
    internal_events: tuple[str, ...]
    end_event: str
    commanded_context: tuple[str, ...]
    evidence: Evidence
    claim_boundary: str
    start_event_id: EventId
    end_event_ids: tuple[EventId, ...]


P24_INTERVAL2 = Interval2Branch(
    branch_id="P24_INTERVAL2_TO_IL1_ZERO",
    start_event="P24_t1: QH1 turns off at the end of Ton",
    internal_events=(
        "positive iL1 charges QH1 Coss and discharges QL1 Coss",
        "QL1 may turn on when its Vds reaches zero",
    ),
    end_event="P24_t2: iL1 reaches zero",
    commanded_context=("QH1=OFF", "QS2=ON", "remaining gates unspecified"),
    evidence=Evidence.P24_EXPLICIT,
    claim_boundary="low-side zero-voltage event is internal to the P24 interval",
    start_event_id=EventId.PHASE1_HIGH_SIDE_OFF,
    end_event_ids=(EventId.PHASE1_INDUCTOR_CURRENT_ZERO,),
)


P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE = Interval2Branch(
    branch_id="P25_INTERVAL2_TO_SL1_ZVS_ON_EXTENDED_NP4",
    start_event="P25_t1: SH1 turns off",
    internal_events=(
        "iL1 charges CH1 and discharges CL1 while approximately constant",
        "optional Mode 2-prime reverse-conduction interval depends on dead time",
    ),
    end_event="P25_t2: VCL1 is zero and SL1 turns on",
    commanded_context=("SH1=OFF", "SL2=ON", "SL3=ON", "SL4=ON (nP=4 extension)"),
    evidence=Evidence.CROSS_PAPER_EXTENSION,
    claim_boundary="P25 nP=3 Mode 2 extended to the P24 nP=4 topology",
    start_event_id=EventId.PHASE1_HIGH_SIDE_OFF,
    end_event_ids=(EventId.PHASE1_LOW_SIDE_VDS_ZERO, EventId.PHASE1_LOW_SIDE_ON),
)
