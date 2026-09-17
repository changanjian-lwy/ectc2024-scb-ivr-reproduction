"""P25 Mode-5/6 physical boundaries with printed-label conflicts exposed."""

from dataclasses import dataclass

from scb_ivr.evidence import Evidence
from scb_ivr.physical_events import EventId


@dataclass(frozen=True)
class StageBoundary:
    stage: str
    start_events: tuple[EventId, ...]
    end_events: tuple[EventId, ...]
    source_time_span: str
    unresolved: tuple[str, ...]
    evidence: Evidence = Evidence.P25_SUPPLEMENT


P25_MODE5 = StageBoundary(
    "P25_MODE5_PHASE2_COMMUTATION",
    (EventId.PHASE2_LOW_SIDE_OFF,),
    (EventId.PHASE2_HIGH_SIDE_VDS_ZERO, EventId.PHASE2_HIGH_SIDE_ON),
    "printed [t5,t6]",
    ("t5-t4 command/driver delay", "numeric CH2/CL2/snubber values", "Mode-5-prime dead time"),
)

P25_MODE6 = StageBoundary(
    "P25_MODE6_PHASE2_ENERGY",
    (EventId.PHASE2_HIGH_SIDE_ON,),
    (EventId.PHASE2_INDUCTOR_CURRENT_PEAK,),
    "printed [t5,t6], but physical start is the Mode-5 t6 event",
    ("reliable printed label for the physical end event",),
)
