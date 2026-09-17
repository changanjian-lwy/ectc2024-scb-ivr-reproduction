"""Symbolic P24 event ring; no unpublished interval duration is assigned."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scb_ivr.topology_naming import phase_names


class LocalEvent(str, Enum):
    HIGH_SIDE_ON = "high_side_on"
    HIGH_SIDE_OFF = "high_side_off"
    LOW_SIDE_VDS_ZERO = "low_side_vds_zero"
    LOW_SIDE_ON = "low_side_on"
    INDUCTOR_CURRENT_ZERO = "inductor_current_zero"
    NEGATIVE_CURRENT_TARGET = "negative_current_target"
    LOW_SIDE_OFF = "low_side_off"
    HIGH_SIDE_VDS_ZERO = "high_side_vds_zero"


P24_LOCAL_EVENT_ORDER = (
    LocalEvent.HIGH_SIDE_ON,
    LocalEvent.HIGH_SIDE_OFF,
    LocalEvent.LOW_SIDE_VDS_ZERO,
    LocalEvent.LOW_SIDE_ON,
    LocalEvent.INDUCTOR_CURRENT_ZERO,
    LocalEvent.NEGATIVE_CURRENT_TARGET,
    LocalEvent.LOW_SIDE_OFF,
    LocalEvent.HIGH_SIDE_VDS_ZERO,
)


@dataclass(frozen=True)
class PhaseEventRing:
    phase_index: int
    next_phase_index: int
    high_side: str
    own_low_side: str
    adjacent_support_low_side: str
    inductor: str
    events: tuple[LocalEvent, ...] = P24_LOCAL_EVENT_ORDER


def build_p24_event_rings(phases: int) -> tuple[PhaseEventRing, ...]:
    if not isinstance(phases, int) or phases <= 1:
        raise ValueError("interleaved event ring requires at least two phases")
    return tuple(
        _build_ring(k, phases)
        for k in range(1, phases + 1)
    )


def _build_ring(k: int, phases: int) -> PhaseEventRing:
    own = phase_names(k, phases)
    next_index = (k % phases) + 1
    adjacent = phase_names(next_index, phases)
    return PhaseEventRing(
        phase_index=k,
        next_phase_index=next_index,
        high_side=own.canonical_high,
        own_low_side=own.canonical_low,
        adjacent_support_low_side=adjacent.canonical_low,
        inductor=own.inductor,
    )


def validate_observed_prefix(ring: PhaseEventRing, observed: tuple[LocalEvent, ...]) -> None:
    """Reject skipped/reordered physical events while allowing a partial run."""

    expected = ring.events[: len(observed)]
    if observed != expected:
        raise RuntimeError(
            f"phase {ring.phase_index} event order mismatch: "
            f"expected {expected}, observed {observed}"
        )
