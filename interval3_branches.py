"""Paper-specific interval-3 branches expressed with stable physical events.

The name ``interval 3`` is local to each paper.  It is deliberately not used
as a framework transition key because P24 and P25 assign different physics to
their t2-t3 spans.
"""

from __future__ import annotations

from dataclasses import dataclass

from evidence import Evidence
from physical_events import EventId


@dataclass(frozen=True)
class Interval3Branch:
    branch_id: str
    paper: str
    start_event_ids: tuple[EventId, ...]
    end_event_ids: tuple[EventId, ...]
    explicitly_on: tuple[str, ...]
    physical_process: str
    evidence: Evidence
    scope_note: str


P24_INTERVAL3 = Interval3Branch(
    branch_id="P24_SAME_PHASE_NEGATIVE_CURRENT_AND_HIGH_SIDE_ZVS",
    paper="P24",
    start_event_ids=(EventId.PHASE1_INDUCTOR_CURRENT_ZERO,),
    end_event_ids=(EventId.PHASE1_HIGH_SIDE_VDS_ZERO, EventId.PHASE1_HIGH_SIDE_ON),
    explicitly_on=("QL1 until the negative-current turn-off event",),
    physical_process=(
        "iL1 crosses below zero; QL1 is then turned off at the P24 negative-current "
        "target, and reverse iL1 commutates the phase-1 switch capacitances until "
        "QH1 reaches zero Vds and turns on"
    ),
    evidence=Evidence.P24_EXPLICIT,
    scope_note="P24 follows phase 1 back to QH1 ZVS; it does not define this boundary by iL2=0.",
)


P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE = Interval3Branch(
    branch_id="P25_MODE3_ALL_LOW_FREEWHEEL_EXTENDED_NP4",
    paper="P25_TO_NP4_EXTENSION",
    start_event_ids=(EventId.PHASE1_LOW_SIDE_VDS_ZERO, EventId.PHASE1_LOW_SIDE_ON),
    end_event_ids=(EventId.PHASE2_INDUCTOR_CURRENT_ZERO,),
    explicitly_on=("SL1", "SL2", "SL3", "SL4"),
    physical_process=(
        "SL1 turns on at zero Vds; all four low-side switches freewheel their phase "
        "currents. iL1 decreases, while the published next boundary is the phase-2 "
        "current zero crossing"
    ),
    evidence=Evidence.CROSS_PAPER_EXTENSION,
    scope_note=(
        "P25 explicitly states SL1/SL2/SL3 and iL2=0 for nP=3. Adding SL4 is the "
        "declared nP=4 extension, not an explicit P24 command."
    ),
)
