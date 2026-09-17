"""Phase-local time frames for event-driven interleaved converter models.

This module places phases on the global clock.  It deliberately does not infer
an electrical mode from time alone: P24 interval 2/3 endpoints are physical
events, not published fixed durations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseLocalFrame:
    phase_index: int
    origin_s: float
    local_cycle_time_s: float
    time_to_next_origin_s: float
    mode: None = None
    mode_status: str = "REQUIRES_EVENT_HISTORY"


def phase_local_time(global_time_s: float, phase_index: int, phases: int, period_s: float) -> float:
    """Return `(t-(phase-1)T/nP) mod T` with explicit nP validation."""

    if not isinstance(phases, int) or phases <= 0:
        raise ValueError("phases must be a positive integer")
    if not isinstance(phase_index, int) or not 1 <= phase_index <= phases:
        raise ValueError("phase_index must lie in 1..phases")
    if period_s <= 0:
        raise ValueError("period_s must be positive")
    origin = (phase_index - 1) * period_s / phases
    return (global_time_s - origin) % period_s


def build_phase_frames(global_time_s: float, phases: int, period_s: float) -> tuple[PhaseLocalFrame, ...]:
    """Build phase coordinates without inventing event-dependent mode times."""

    frames = []
    for phase_index in range(1, phases + 1):
        origin = (phase_index - 1) * period_s / phases
        local = phase_local_time(global_time_s, phase_index, phases, period_s)
        frames.append(
            PhaseLocalFrame(
                phase_index=phase_index,
                origin_s=origin,
                local_cycle_time_s=local,
                time_to_next_origin_s=(-local) % period_s,
            )
        )
    return tuple(frames)


def assert_event_not_replaced_by_global_clock(*, event_name: str, event_observed: bool) -> None:
    """Fail closed when a physical transition is requested without its event."""

    if not event_observed:
        raise RuntimeError(f"{event_name} is event-driven; a global clock edge cannot replace it")
