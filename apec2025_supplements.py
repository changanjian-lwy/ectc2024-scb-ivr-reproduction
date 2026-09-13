"""2025 APEC supplements used only where the 2024 paper is silent.

Nothing in this module is automatically promoted into the P24 model.  A
caller must preserve the provenance and check for a P24 conflict first.
"""

from __future__ import annotations

from dataclasses import dataclass

from evidence import Evidence
from ivr_framework import SystemSpec, critical_inductance


@dataclass(frozen=True)
class SupplementedValue:
    value: float
    evidence: Evidence
    source_location: str
    interpretation: str


def inductance_for_negative_peak_fraction(
    spec: SystemSpec,
    phases: int,
    modules: int,
    switching_frequency_hz: float,
    negative_peak_fraction: float,
) -> SupplementedValue:
    """Generalize the 0.95 factor printed in P25 Eq. (20).

    P25 explicitly prints 0.95 for its 5% design endpoint. Replacing 0.95 by
    (1-alpha) is a cross-paper mathematical generalization, not a P24 equation
    and not an independently printed P25 equation for arbitrary alpha.
    """

    if not 0.0 <= negative_peak_fraction < 1.0:
        raise ValueError("negative_peak_fraction must satisfy 0 <= value < 1")
    value = (1.0 - negative_peak_fraction) * critical_inductance(
        spec, phases, modules, switching_frequency_hz
    )
    return SupplementedValue(
        value=value,
        evidence=Evidence.CROSS_PAPER_EXTENSION,
        source_location="P25 Eq. (20), generalized from its printed 0.95 factor",
        interpretation=(
            "Allowed only as a labelled branch after the P24 critical-inductance "
            "calculation; it must not be reported as P24 explicit."
        ),
    )
