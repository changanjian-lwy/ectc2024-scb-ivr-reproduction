"""Explicit first-interval switch-set branches; omission never means OFF."""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class FirstIntervalBranch:
    branch_id: str
    phases: int
    commanded_on: tuple[str, ...]
    unspecified: tuple[str, ...]
    evidence: Evidence
    source_location: str
    claim_boundary: str


P24_MINIMAL_PHASE1 = FirstIntervalBranch(
    branch_id="P24_MINIMAL_PHASE1",
    phases=4,
    commanded_on=("QH1", "QS2"),
    unspecified=("remaining low-side switches", "QH2-QH4"),
    evidence=Evidence.P24_EXPLICIT,
    source_location="P24 Sec. II-B, first interval",
    claim_boundary=(
        "minimum explicitly named conducting set; unspecified switches are "
        "not asserted OFF"
    ),
)


P25_EXPANDED_TO_FOUR_PHASE = FirstIntervalBranch(
    branch_id="P25_EXPANDED_TO_FOUR_PHASE",
    phases=4,
    commanded_on=("SH1", "SL2", "SL3", "SL4"),
    unspecified=("SH2-SH4",),
    evidence=Evidence.CROSS_PAPER_EXTENSION,
    source_location=(
        "P25 Fig. 3 Mode 1 explicitly supplies SH1+SL2+SL3 for nP=3; "
        "SL4 is the labelled nP=4 rotation extension"
    ),
    claim_boundary="may supplement P24 silence; cannot be called P24 explicit",
)


FIRST_INTERVAL_BRANCHES = {
    branch.branch_id: branch
    for branch in (P24_MINIMAL_PHASE1, P25_EXPANDED_TO_FOUR_PHASE)
}
