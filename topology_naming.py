"""Canonical names for the four switch positions drawn in P24 Fig. 3."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseNames:
    phase_index: int
    paper_high: str
    paper_low: str
    canonical_high: str
    canonical_low: str
    inductor: str
    switch_node: str


def phase_names(phase_index: int, phases: int) -> PhaseNames:
    if not isinstance(phases, int) or phases <= 0:
        raise ValueError("phases must be a positive integer")
    if not isinstance(phase_index, int) or not 1 <= phase_index <= phases:
        raise ValueError("phase_index must lie in 1..phases")
    return PhaseNames(
        phase_index=phase_index,
        paper_high=f"S{phase_index}a",
        paper_low=f"S{phase_index}b",
        canonical_high=f"H{phase_index}",
        canonical_low=f"L{phase_index}",
        inductor=f"LIND{phase_index}",
        switch_node=f"X{phase_index}",
    )


def build_name_map(phases: int) -> dict[str, str]:
    """Map every Fig. 3 switch label to exactly one canonical gate name."""

    mapping: dict[str, str] = {}
    for k in range(1, phases + 1):
        names = phase_names(k, phases)
        mapping[names.paper_high] = names.canonical_high
        mapping[names.paper_low] = names.canonical_low
    return mapping
