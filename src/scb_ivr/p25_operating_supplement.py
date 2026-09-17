"""P25 six-mode description, retained as a supplement rather than P24 truth."""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class P25Mode:
    name: str
    explicitly_on: tuple[str, ...]
    event: str
    role: str
    evidence: Evidence = Evidence.P25_SUPPLEMENT


P25_PHASE1_TO_PHASE2_MODES = (
    P25Mode(
        "P25_M1_PHASE1_ENERGY",
        ("SH1", "SL2", "SL3"),
        "SH1 on-time ends",
        "iL1 rises while iL2/iL3 freewheel and fall",
    ),
    P25Mode(
        "P25_M2_M2P_PHASE1_COMMUTATION",
        ("SL2", "SL3"),
        "Vds(SL1) returns to zero and SL1 turns on",
        "iL1 commutates CH1/CL1; an optional reverse-conduction submode depends on dead time",
    ),
    P25Mode(
        "P25_M3_ALL_LOW_FREEWHEEL",
        ("SL1", "SL2", "SL3"),
        "iL2 reaches zero",
        "all three phase currents fall; the next phase zero crossing defines the boundary",
    ),
    P25Mode(
        "P25_M4_PHASE2_NEGATIVE",
        ("SL1", "SL2", "SL3"),
        "iL2 reaches 5%-10% of peak in the negative direction",
        "store commutation energy for SH2 ZVS",
    ),
    P25Mode(
        "P25_M5_M5P_PHASE2_COMMUTATION",
        ("SL1", "SL3"),
        "Vds(SH2) returns to zero and SH2 turns on",
        "negative iL2 commutates CH2/CL2; an optional submode depends on dead time",
    ),
    P25Mode(
        "P25_M6_PHASE2_ENERGY",
        ("SL1", "SH2", "SL3"),
        "SH2 on-time ends",
        "iL2 rises while iL1/iL3 freewheel and fall",
    ),
)
