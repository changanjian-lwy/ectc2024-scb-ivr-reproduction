"""Exploratory startup-readiness detector for the P24 four-phase ladder.

This module is intentionally outside the paper-locked operating sequence.  P24
defines the steady-state four-phase topology, but does not publish a zero-start
release controller.  The detector observes the ladder; it does not create,
precharge, or rebalance any capacitor voltage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scb_ivr.evidence import Evidence


class ReleaseReason(str, Enum):
    READY = "READY"
    SEGMENT_UNDERVOLTAGE = "SEGMENT_UNDERVOLTAGE"
    SEGMENT_OVERVOLTAGE = "SEGMENT_OVERVOLTAGE"
    NODE_ORDER_INVALID = "NODE_ORDER_INVALID"
    CAPACITOR_OVERVOLTAGE = "CAPACITOR_OVERVOLTAGE"
    CURRENT_NOT_SAFE = "CURRENT_NOT_SAFE"


@dataclass(frozen=True)
class StartupBoundary:
    n_p: int = 4
    segment_tolerance_fraction: float = 1 / 6  # exploratory: +/-2 V at 48 V
    capacitor_ov_fraction: float = 1.10
    current_safe_a: float = 1.0
    evidence: Evidence = Evidence.EXPLORATORY_ASSUMPTION

    def __post_init__(self) -> None:
        if self.n_p < 2:
            raise ValueError("n_p must remain explicit and be at least 2")
        if not 0 <= self.segment_tolerance_fraction < 1:
            raise ValueError("segment tolerance must be in [0, 1)")
        if self.current_safe_a < 0:
            raise ValueError("current limit cannot be negative")


@dataclass(frozen=True)
class StartupObservation:
    vin_v: float
    ladder_nodes_v: tuple[float, ...]  # top to bottom: C1, C2, ...
    phase_currents_a: tuple[float, ...]


@dataclass(frozen=True)
class StartupDecision:
    release: bool
    reason: ReleaseReason
    target_segment_v: float
    segment_voltages_v: tuple[float, ...]
    allowed_segment_window_v: tuple[float, float]
    evidence: Evidence


def evaluate_startup_readiness(
    observation: StartupObservation,
    boundary: StartupBoundary = StartupBoundary(),
) -> StartupDecision:
    """Evaluate readiness from adjacent voltage differences, never absolutes."""
    if len(observation.ladder_nodes_v) != boundary.n_p - 1:
        raise ValueError("four-phase boundary requires exactly n_p-1 ladder nodes")
    if len(observation.phase_currents_a) != boundary.n_p:
        raise ValueError("one current observation is required for every phase")

    levels = (observation.vin_v, *observation.ladder_nodes_v, 0.0)
    segments = tuple(levels[index] - levels[index + 1] for index in range(boundary.n_p))
    target = observation.vin_v / boundary.n_p
    low = target * (1 - boundary.segment_tolerance_fraction)
    high = target * (1 + boundary.segment_tolerance_fraction)

    reason = ReleaseReason.READY
    if any(levels[index] < levels[index + 1] for index in range(len(levels) - 1)):
        reason = ReleaseReason.NODE_ORDER_INVALID
    elif any(node > observation.vin_v * boundary.capacitor_ov_fraction for node in observation.ladder_nodes_v):
        reason = ReleaseReason.CAPACITOR_OVERVOLTAGE
    elif any(segment < low for segment in segments):
        reason = ReleaseReason.SEGMENT_UNDERVOLTAGE
    elif any(segment > high for segment in segments):
        reason = ReleaseReason.SEGMENT_OVERVOLTAGE
    elif any(abs(current) > boundary.current_safe_a for current in observation.phase_currents_a):
        reason = ReleaseReason.CURRENT_NOT_SAFE

    return StartupDecision(
        release=reason is ReleaseReason.READY,
        reason=reason,
        target_segment_v=target,
        segment_voltages_v=segments,
        allowed_segment_window_v=(low, high),
        evidence=boundary.evidence,
    )

