"""State/residual interface for P24 main-line periodic-orbit reproduction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FourPhasePeriodicState:
    capacitor_voltages_v: tuple[float, float, float]
    inductor_currents_a: tuple[float, float, float, float]
    output_voltage_v: float


@dataclass(frozen=True)
class FastSwitchingState:
    """Node/Coss state required when device capacitances are present."""

    high_side_nodes_v: tuple[float, float, float]
    switching_nodes_v: tuple[float, float, float, float]


@dataclass(frozen=True)
class PeriodicResidual:
    capacitor_delta_v: tuple[float, float, float]
    inductor_delta_a: tuple[float, float, float, float]
    output_delta_v: float

    @property
    def max_abs(self) -> float:
        return max(
            *(abs(value) for value in self.capacitor_delta_v),
            *(abs(value) for value in self.inductor_delta_a),
            abs(self.output_delta_v),
        )


def residual(initial: FourPhasePeriodicState, final: FourPhasePeriodicState) -> PeriodicResidual:
    return PeriodicResidual(
        tuple(b - a for a, b in zip(initial.capacitor_voltages_v, final.capacitor_voltages_v)),
        tuple(b - a for a, b in zip(initial.inductor_currents_a, final.inductor_currents_a)),
        final.output_voltage_v - initial.output_voltage_v,
    )


def p24_voltage_guess(vin_v: float, n_p: int) -> tuple[float, ...]:
    """Return a solver seed, never a forced periodic solution."""
    if n_p < 2:
        raise ValueError("n_p must be explicit and at least 2")
    return tuple(vin_v * (n_p - index) / n_p for index in range(1, n_p))


def phase1_origin_fast_seed(vin_v: float, n_p: int) -> FastSwitchingState:
    """A topology-consistent phase-1-origin seed, not a solved orbit."""
    if n_p != 4:
        raise ValueError("current P24 phase-1 seed is defined only for n_p=4")
    step = vin_v / n_p
    return FastSwitchingState(
        high_side_nodes_v=(vin_v, 2 * step, step),
        switching_nodes_v=(step, 0.0, 0.0, 0.0),
    )
