"""D33: distinguish arbitrary SH1-on test entry from a periodic return section.

M15 has negative iL1; continuous M15->M1 handoff retains that current.
Positive iL1 may be a valid initial-value debug fixture, but cannot equal the
return state of this declared event cycle. No seed is changed or fitted.
"""
from dataclasses import dataclass
from math import isfinite
from .p25_periodic_section import section_coordinates


@dataclass(frozen=True)
class SectionNecessity:
    status: str
    active_current_a: float
    distance_to_nonpositive_domain_a: float
    scope: str = "NECESSARY_RETURN_DIRECTION_ONLY; not trajectory or periodicity proof"


def section_return_necessity(memory, *, current_margin_a):
    section_coordinates(memory)  # fresh SH1-on section and complete peak records
    b = memory.last_event.boundary
    if b.branch != "P25" or b.nP != 3 or b.nM != 1 or b.module != 1:
        raise ValueError("P25 native three-phase single module only")
    if not isfinite(current_margin_a) or current_margin_a < 0:
        raise ValueError("explicit finite nonnegative current decision margin required")
    current = memory.last_event.current_a[0]
    if current > current_margin_a:
        status = "EXCLUDED_FROM_EXACT_PERIODIC_RETURN"
    elif current < -current_margin_a:
        status = "NECESSARY_DIRECTION_PASSED_NOT_SUFFICIENT"
    else:
        status = "ZERO_CURRENT_BOUNDARY_UNRESOLVED"
    return SectionNecessity(status, current, max(current, 0.))
