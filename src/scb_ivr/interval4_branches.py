"""P25 Mode-4 boundary, kept separate from P24 same-phase interval labels."""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.evidence import Evidence
from scb_ivr.physical_events import EventId


@dataclass(frozen=True)
class P25Mode4Boundary:
    start_event: EventId
    end_event: EventId
    monitored_current: str
    explicitly_on_np3: tuple[str, ...]
    other_phase_sign_contracts: tuple[str, ...]
    design_negative_fraction: float
    textual_range: tuple[float, float]
    evidence: Evidence = Evidence.P25_SUPPLEMENT


P25_MODE4 = P25Mode4Boundary(
    start_event=EventId.PHASE2_INDUCTOR_CURRENT_ZERO,
    end_event=EventId.PHASE2_NEGATIVE_CURRENT_TARGET,
    monitored_current="iL2",
    explicitly_on_np3=("SL1", "SL2", "SL3"),
    other_phase_sign_contracts=("iL1 > 0 and decreasing", "iL3 > 0 and decreasing"),
    design_negative_fraction=0.05,
    textual_range=(0.05, 0.10),
)
