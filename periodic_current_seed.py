"""Paper-derived phase-shifted triangular-current seed for Track A."""

from __future__ import annotations


def triangular_current_at_age(
    age_s: float,
    *,
    period_s: float,
    on_time_s: float,
    peak_a: float,
) -> float:
    """Ideal P24 0-to-peak-to-0 current at one phase-cycle age."""
    if not 0 <= age_s < period_s:
        raise ValueError("age_s must be inside one period")
    if not 0 < on_time_s < period_s:
        raise ValueError("on_time_s must be inside one period")
    if peak_a <= 0:
        raise ValueError("peak_a must be positive")
    if age_s <= on_time_s:
        return peak_a * age_s / on_time_s
    return peak_a * (period_s - age_s) / (period_s - on_time_s)


def interleaved_initial_currents(
    *, n_p: int, period_s: float, on_time_s: float, peak_a: float
) -> tuple[float, ...]:
    """Currents at the phase-1 origin for n_p uniformly shifted phases."""
    if n_p < 1:
        raise ValueError("n_p must remain explicit and positive")
    phase_shift = period_s / n_p
    currents = []
    for index in range(n_p):
        origin = index * phase_shift
        age = (-origin) % period_s
        currents.append(
            triangular_current_at_age(
                age,
                period_s=period_s,
                on_time_s=on_time_s,
                peak_a=peak_a,
            )
        )
    return tuple(currents)
