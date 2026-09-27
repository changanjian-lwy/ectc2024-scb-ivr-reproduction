"""Path-resolved switch-conduction loss with explicit device population.

This module deliberately does not infer switch duty from total phase-current
RMS.  A phase current can pass through the high-side device, the low-side
device, or an unmodelled reverse-conduction path at different times.  Callers
must therefore supply the time integrals of ``i(t)^2`` for each path.

The returned result is a *partial* electrical-loss result.  Dead-time reverse
conduction is reported but not converted to watts unless a separately sourced
third-quadrant model is provided by a later module.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from scb_ivr.device_library import GaNDevice, SwitchPopulation


@dataclass(frozen=True)
class PathI2Integrals:
    """Per-phase integrals of squared current over one complete period."""

    period_s: float
    high_side_a2s: tuple[float, ...]
    low_side_a2s: tuple[float, ...]
    dead_time_a2s: tuple[float, ...]

    def __post_init__(self) -> None:
        vectors: Sequence[tuple[float, ...]] = (
            self.high_side_a2s,
            self.low_side_a2s,
            self.dead_time_a2s,
        )
        if not isfinite(self.period_s) or self.period_s <= 0:
            raise ValueError("period_s must be finite and positive")
        if not self.high_side_a2s:
            raise ValueError("at least one phase is required")
        if len({len(values) for values in vectors}) != 1:
            raise ValueError("all path-integral vectors must have the same length")
        if any(not isfinite(value) or value < 0 for values in vectors for value in values):
            raise ValueError("path i^2 integrals must be finite and non-negative")


@dataclass
class PathI2Accumulator:
    """Accumulate path-specific ``i^2 dt`` from ordered solver samples.

    The switch mode attached to a sample is taken to describe the interval
    ending at that sample, matching the project's backward-Euler convention.
    Calling code must insert samples at every switch-mode transition.
    """

    phase_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.phase_count, int) or self.phase_count <= 0:
            raise ValueError("phase_count must be a positive integer")
        self._previous_time_s: float | None = None
        self._high_side_a2s = [0.0] * self.phase_count
        self._low_side_a2s = [0.0] * self.phase_count
        self._dead_time_a2s = [0.0] * self.phase_count

    def observe(
        self,
        *,
        time_s: float,
        phase_currents_a: Sequence[float],
        high_side_on: Sequence[bool],
        low_side_on: Sequence[bool],
    ) -> None:
        values = (phase_currents_a, high_side_on, low_side_on)
        if any(len(value) != self.phase_count for value in values):
            raise ValueError("sample dimensions must match phase_count")
        if not isfinite(time_s):
            raise ValueError("sample time must be finite")
        if any(not isfinite(float(current)) for current in phase_currents_a):
            raise ValueError("phase currents must be finite")
        if any(high and low for high, low in zip(high_side_on, low_side_on)):
            raise ValueError("high and low side may not conduct simultaneously")
        if self._previous_time_s is None:
            self._previous_time_s = time_s
            return
        dt = time_s - self._previous_time_s
        if dt < 0:
            raise ValueError("sample times must be monotonic")
        self._previous_time_s = time_s
        if dt == 0:
            return
        for phase, current in enumerate(phase_currents_a):
            i2dt = float(current) ** 2 * dt
            if high_side_on[phase]:
                self._high_side_a2s[phase] += i2dt
            elif low_side_on[phase]:
                self._low_side_a2s[phase] += i2dt
            else:
                self._dead_time_a2s[phase] += i2dt

    def integrals(self, *, period_s: float) -> PathI2Integrals:
        return PathI2Integrals(
            period_s=period_s,
            high_side_a2s=tuple(self._high_side_a2s),
            low_side_a2s=tuple(self._low_side_a2s),
            dead_time_a2s=tuple(self._dead_time_a2s),
        )


@dataclass(frozen=True)
class ConductionLossResult:
    high_side_effective_resistance_ohm: float
    low_side_effective_resistance_ohm: float
    high_side_loss_w_per_phase: tuple[float, ...]
    low_side_loss_w_per_phase: tuple[float, ...]
    dead_time_i2_average_a2_per_phase: tuple[float, ...]

    @property
    def modeled_loss_w(self) -> float:
        return sum(self.high_side_loss_w_per_phase) + sum(self.low_side_loss_w_per_phase)

    @property
    def has_unmodeled_dead_time_current(self) -> bool:
        return any(value > 0 for value in self.dead_time_i2_average_a2_per_phase)

    @property
    def is_complete_total_loss(self) -> bool:
        """Always false: this object models channel conduction only."""
        return False


def path_resolved_conduction_loss(
    device: GaNDevice,
    population: SwitchPopulation,
    integrals: PathI2Integrals,
) -> ConductionLossResult:
    """Calculate channel-conduction loss without hiding device population.

    ``integral(i^2 dt) / period`` is the path-specific mean-square current.
    Multiplying it by the corresponding parallel-corrected resistance yields
    the average channel-conduction loss for that path.
    """

    rhs = device.rds_on(population.high_side_parallel)
    rls = device.rds_on(population.low_side_parallel)
    high = tuple(rhs * value / integrals.period_s for value in integrals.high_side_a2s)
    low = tuple(rls * value / integrals.period_s for value in integrals.low_side_a2s)
    dead = tuple(value / integrals.period_s for value in integrals.dead_time_a2s)
    return ConductionLossResult(
        high_side_effective_resistance_ohm=rhs,
        low_side_effective_resistance_ohm=rls,
        high_side_loss_w_per_phase=high,
        low_side_loss_w_per_phase=low,
        dead_time_i2_average_a2_per_phase=dead,
    )
