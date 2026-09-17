"""Stable physical events with paper-specific time-label aliases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scb_ivr.evidence import Evidence


class EventId(str, Enum):
    PHASE1_HIGH_SIDE_OFF = "phase1_high_side_off"
    PHASE1_LOW_SIDE_VDS_ZERO = "phase1_low_side_vds_zero"
    PHASE1_LOW_SIDE_ON = "phase1_low_side_on"
    PHASE1_INDUCTOR_CURRENT_ZERO = "phase1_inductor_current_zero"
    PHASE2_INDUCTOR_CURRENT_ZERO = "phase2_inductor_current_zero"
    PHASE2_NEGATIVE_CURRENT_TARGET = "phase2_negative_current_target"
    PHASE2_LOW_SIDE_OFF_COMMAND = "phase2_low_side_off_command"
    PHASE2_LOW_SIDE_OFF = "phase2_low_side_off"
    PHASE2_HIGH_SIDE_VDS_ZERO = "phase2_high_side_vds_zero"
    PHASE2_HIGH_SIDE_ON = "phase2_high_side_on"
    PHASE2_INDUCTOR_CURRENT_PEAK = "phase2_inductor_current_peak"
    PHASE1_NEGATIVE_CURRENT_TARGET = "phase1_negative_current_target"
    PHASE1_HIGH_SIDE_VDS_ZERO = "phase1_high_side_vds_zero"
    PHASE1_HIGH_SIDE_ON = "phase1_high_side_on"


@dataclass(frozen=True)
class PaperEventAlias:
    paper: str
    paper_label: str | None
    event_id: EventId
    role: str
    evidence: Evidence
    source_location: str


ALIASES = (
    PaperEventAlias("P24", "t1", EventId.PHASE1_HIGH_SIDE_OFF, "interval boundary", Evidence.P24_EXPLICIT, "P24 Sec. II-B"),
    PaperEventAlias("P24", None, EventId.PHASE1_LOW_SIDE_VDS_ZERO, "unnumbered internal event", Evidence.P24_EXPLICIT, "P24 Sec. II-B, interval 2"),
    PaperEventAlias("P24", None, EventId.PHASE1_LOW_SIDE_ON, "unnumbered conditional gate event", Evidence.P24_EXPLICIT, "P24 Sec. II-B, interval 2"),
    PaperEventAlias("P24", "t2", EventId.PHASE1_INDUCTOR_CURRENT_ZERO, "interval boundary", Evidence.P24_EXPLICIT, "P24 Sec. II-B, end of interval 2"),
    PaperEventAlias("P25", "t1", EventId.PHASE1_HIGH_SIDE_OFF, "interval boundary", Evidence.P25_SUPPLEMENT, "P25 Mode 2"),
    PaperEventAlias("P25", "t2", EventId.PHASE1_LOW_SIDE_VDS_ZERO, "interval boundary condition", Evidence.P25_SUPPLEMENT, "P25 Mode 2/2-prime"),
    PaperEventAlias("P25", "t2", EventId.PHASE1_LOW_SIDE_ON, "command at same ideal boundary", Evidence.P25_SUPPLEMENT, "P25 interval-2 ending statement"),
    PaperEventAlias("P25", "t3", EventId.PHASE2_INDUCTOR_CURRENT_ZERO, "interval boundary / controller zero-crossing", Evidence.P25_SUPPLEMENT, "P25 Mode 3 ending statement"),
    PaperEventAlias("P25", "t4", EventId.PHASE2_NEGATIVE_CURRENT_TARGET, "control turn-off boundary", Evidence.P25_SUPPLEMENT, "P25 Mode 4 ending statement"),
    PaperEventAlias("P25", "t4", EventId.PHASE2_LOW_SIDE_OFF_COMMAND, "control command at target", Evidence.P25_SUPPLEMENT, "P25 Mode 4 ending statement"),
    PaperEventAlias("P25", "t5", EventId.PHASE2_LOW_SIDE_OFF, "physical switch-off boundary", Evidence.P25_SUPPLEMENT, "P25 Mode 5 starting statement"),
    PaperEventAlias("P25", "t6", EventId.PHASE2_HIGH_SIDE_VDS_ZERO, "commutation-complete boundary", Evidence.P25_SUPPLEMENT, "P25 Mode 5 ending statement"),
    PaperEventAlias("P25", "t6", EventId.PHASE2_HIGH_SIDE_ON, "ZVS gate event", Evidence.P25_SUPPLEMENT, "P25 Mode 5 ending / Mode 6 physical start"),
    PaperEventAlias("P25", None, EventId.PHASE2_INDUCTOR_CURRENT_PEAK, "Mode-6 physical end; printed time span is inconsistent", Evidence.P25_SUPPLEMENT, "P25 Mode 6 ending statement"),
)


def aliases_for_event(event_id: EventId) -> tuple[PaperEventAlias, ...]:
    return tuple(alias for alias in ALIASES if alias.event_id is event_id)


def event_for_label(paper: str, paper_label: str) -> tuple[EventId, ...]:
    return tuple(
        alias.event_id
        for alias in ALIASES
        if alias.paper == paper and alias.paper_label == paper_label
    )
