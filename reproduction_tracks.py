"""Top-level separation between the paper reproduction and startup extension."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from evidence import Evidence


class TrackId(str, Enum):
    A_P24_PERIODIC_STEADY_STATE = "A_P24_PERIODIC_STEADY_STATE"
    B_ZERO_START_ENGINEERING_EXTENSION = "B_ZERO_START_ENGINEERING_EXTENSION"


@dataclass(frozen=True)
class ReproductionTrack:
    track_id: TrackId
    objective: str
    required_for_p24_reproduction: bool
    allowed_initialization: str
    evidence: Evidence


TRACK_A = ReproductionTrack(
    TrackId.A_P24_PERIODIC_STEADY_STATE,
    "Close one single-module four-phase periodic orbit, then reproduce the P24 four-module row.",
    True,
    "A solved periodic state is allowed; 36/24/12 V may be an initial guess but must not be forced as the final answer.",
    Evidence.P24_DERIVED,
)

TRACK_B = ReproductionTrack(
    TrackId.B_ZERO_START_ENGINEERING_EXTENSION,
    "Reach the periodic orbit from discharged flying/output capacitors without unsafe current or voltage.",
    False,
    "True zero stored energy or an explicitly named powered-rail/precharge boundary.",
    Evidence.EXPLORATORY_ASSUMPTION,
)


def assert_tracks_do_not_merge() -> None:
    assert TRACK_A.track_id is not TRACK_B.track_id
    assert TRACK_A.required_for_p24_reproduction
    assert not TRACK_B.required_for_p24_reproduction
    assert TRACK_A.evidence is not TRACK_B.evidence

