"""Separate module-origin shift from total switch-event spacing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from math import gcd


@dataclass(frozen=True)
class InterleavingAudit:
    phases_per_module: int
    modules: int
    module_origin_shift_cycles: Fraction
    ideal_total_event_spacing_cycles: Fraction
    total_nominal_events: int
    unique_event_times: int
    collision_multiplicity: int
    uniformly_spaced_unique_events: bool

    @property
    def has_collisions(self) -> bool:
        return self.collision_multiplicity > 1

    def as_dict(self) -> dict:
        row = asdict(self)
        row["module_origin_shift_cycles"] = str(self.module_origin_shift_cycles)
        row["ideal_total_event_spacing_cycles"] = str(
            self.ideal_total_event_spacing_cycles
        )
        row["has_collisions"] = self.has_collisions
        return row


@dataclass(frozen=True)
class SingleModulePhaseEvent:
    """One P24 phase origin on a declared absolute time axis."""

    phase_index: int
    phase_origin_s: float
    high_side_off_s: float


@dataclass(frozen=True)
class SingleModuleSchedule:
    """P24 single-module phase origins; commutation endpoints stay event-driven."""

    phases_per_module: int
    modules: int
    reference_time_s: float
    switching_period_s: float
    high_side_on_time_s: float
    phase_spacing_s: float
    module_spacing_s: float
    events: tuple[SingleModulePhaseEvent, ...]


def build_single_module_phase_schedule(
    *,
    phases: int,
    modules: int,
    reference_time_s: float,
    switching_period_s: float,
    high_side_on_time_s: float,
) -> SingleModuleSchedule:
    """Build the nM=1 schedule without inventing commutation durations.

    P24 states that the phases are interleaved and that every high-side uses
    the same frequency, duty ratio and on-time.  For the current one-module
    experiment this records the conventional equal phase origins T/nP.  The
    high-side OFF edge is fixed by P24 Eq. (3); zero crossing, negative-current
    turn-off and ZVS edges are deliberately absent because they are state
    conditions, not fixed offsets published by P24.
    """

    if not isinstance(phases, int) or phases <= 0:
        raise ValueError("phases must be a positive integer")
    if modules != 1:
        raise ValueError("single-module schedule requires modules=1 explicitly")
    if reference_time_s < 0:
        raise ValueError("reference_time_s must be nonnegative")
    if switching_period_s <= 0:
        raise ValueError("switching_period_s must be positive")
    if not 0 < high_side_on_time_s < switching_period_s:
        raise ValueError("high_side_on_time_s must lie inside one period")

    phase_spacing_s = switching_period_s / phases
    module_spacing_s = switching_period_s / modules
    events = tuple(
        SingleModulePhaseEvent(
            phase_index=phase + 1,
            phase_origin_s=reference_time_s + phase * phase_spacing_s,
            high_side_off_s=(
                reference_time_s + phase * phase_spacing_s + high_side_on_time_s
            ),
        )
        for phase in range(phases)
    )
    return SingleModuleSchedule(
        phases_per_module=phases,
        modules=modules,
        reference_time_s=reference_time_s,
        switching_period_s=switching_period_s,
        high_side_on_time_s=high_side_on_time_s,
        phase_spacing_s=phase_spacing_s,
        module_spacing_s=module_spacing_s,
        events=events,
    )


def paper_module_origin_shift_cycles(phases: int, modules: int) -> Fraction:
    """P25 module shift with nP retained explicitly in the model interface.

    Written on the total-event grid this is nP/(nP*nM), which simplifies to
    1/nM. Keeping `phases` mandatory prevents the architecture dimension from
    disappearing when nP=1.
    """

    if not isinstance(phases, int) or phases <= 0:
        raise ValueError("phases must be a positive integer")
    if not isinstance(modules, int) or modules <= 0:
        raise ValueError("modules must be a positive integer")
    return Fraction(phases, phases * modules)


def ideal_total_event_spacing_cycles(phases: int, modules: int) -> Fraction:
    """Spacing if all nP*nM events are uniformly distributed without overlap."""

    if not isinstance(phases, int) or phases <= 0:
        raise ValueError("phases must be a positive integer")
    if not isinstance(modules, int) or modules <= 0:
        raise ValueError("modules must be a positive integer")
    return Fraction(1, phases * modules)


def audit_naive_two_level_interleaving(
    phases: int, modules: int
) -> InterleavingAudit:
    """Audit k/nP + m/nM event placement implied by naive superposition.

    This is a mathematical audit, not a claim that the papers require this
    exact construction. It exposes when independently applying T/nP and T/nM
    creates coincident events.
    """

    ideal_total_event_spacing_cycles(phases, modules)  # validates both
    events = {
        (Fraction(phase, phases) + Fraction(module, modules)) % 1
        for phase in range(phases)
        for module in range(modules)
    }
    ordered = sorted(events)
    gaps = [
        (ordered[(index + 1) % len(ordered)] - ordered[index]) % 1
        for index in range(len(ordered))
    ]
    return InterleavingAudit(
        phases_per_module=phases,
        modules=modules,
        module_origin_shift_cycles=paper_module_origin_shift_cycles(
            phases, modules
        ),
        ideal_total_event_spacing_cycles=Fraction(1, phases * modules),
        total_nominal_events=phases * modules,
        unique_event_times=len(events),
        collision_multiplicity=gcd(phases, modules),
        uniformly_spaced_unique_events=len(set(gaps)) == 1,
    )
