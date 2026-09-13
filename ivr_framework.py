"""Source-locked analytical models from the 2024 ECTC 1-kW IVR paper.

All public inputs and outputs use SI units.  This module is the single source
of truth for paper equations; audit scripts and future SPICE generators must
import these functions rather than copying the equations.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil


PAPER_DOI = "10.1109/ECTC51529.2024.00054"
PAPER_TITLE = (
    "Package Power Delivery Architecture for High Performance Computing "
    "Systems With a 1 kW IVR Operated in CCM-DCM Boundary Mode Condition"
)


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0; received {value!r}")


def _validate_spec(spec: "SystemSpec") -> None:
    _require_positive("vin_v", spec.vin_v)
    _require_positive("vout_v", spec.vout_v)
    _require_positive("pout_w", spec.pout_w)
    _require_positive("minimum_on_time_s", spec.minimum_on_time_s)
    if spec.vout_v >= spec.vin_v:
        raise ValueError("buck-derived model requires vout_v < vin_v")


def _validate_architecture(phases: int, modules: int | None = None) -> None:
    if not isinstance(phases, int) or phases <= 0:
        raise ValueError(f"phases must be a positive integer; received {phases!r}")
    if modules is not None and (not isinstance(modules, int) or modules <= 0):
        raise ValueError(
            f"modules must be a positive integer; received {modules!r}"
        )


def _validate_frequency(switching_frequency_hz: float) -> None:
    _require_positive("switching_frequency_hz", switching_frequency_hz)


@dataclass(frozen=True)
class SystemSpec:
    vin_v: float = 48.0
    vout_v: float = 1.0
    pout_w: float = 1000.0
    minimum_on_time_s: float = 3.4e-9

    @property
    def iout_a(self) -> float:
        return self.pout_w / self.vout_v


@dataclass(frozen=True)
class ConverterResult:
    phases: int
    modules: int
    switching_frequency_hz: float
    power_per_module_w: float
    duty_cycle: float
    high_side_on_time_s: float
    critical_inductance_h: float
    inductor_peak_current_a: float
    minimum_on_time_s: float
    feasible_on_time: bool

    def as_dict(self) -> dict:
        row = asdict(self)
        row.update(
            switching_frequency_mhz=self.switching_frequency_hz / 1e6,
            duty_cycle_percent=100.0 * self.duty_cycle,
            high_side_on_time_ns=self.high_side_on_time_s * 1e9,
            critical_inductance_nh=self.critical_inductance_h * 1e9,
            minimum_on_time_ns=self.minimum_on_time_s * 1e9,
        )
        return row


@dataclass(frozen=True)
class EmbeddedInductorResult:
    phases: int
    modules: int
    switching_frequency_hz: float
    embedded_inductor_peak_rating_a: float
    parallel_inductors_exact: float
    parallel_inductors_engineering: int
    unit_inductance_h: float

    def as_dict(self) -> dict:
        row = asdict(self)
        row.update(
            switching_frequency_mhz=self.switching_frequency_hz / 1e6,
            unit_inductance_nh=self.unit_inductance_h * 1e9,
        )
        return row


def duty_cycle(spec: SystemSpec, phases: int) -> float:
    """Paper Eq. (1): D = nP * Vo / Vin."""
    _validate_spec(spec)
    _validate_architecture(phases)
    value = phases * spec.vout_v / spec.vin_v
    if value >= 1:
        raise ValueError(
            "Eq. (1) requires nP * vout_v / vin_v < 1 for this step-down model"
        )
    return value


def inductor_peak_current(spec: SystemSpec, phases: int, modules: int) -> float:
    """Paper Eq. (2): IL,pk = 2 Io / (nP nM)."""
    _validate_spec(spec)
    _validate_architecture(phases, modules)
    return 2.0 * spec.iout_a / (phases * modules)


def high_side_on_time(
    spec: SystemSpec, phases: int, switching_frequency_hz: float
) -> float:
    """Paper Eq. (3): Ton = nP Vo / (fsw Vin)."""
    _validate_spec(spec)
    _validate_architecture(phases)
    _validate_frequency(switching_frequency_hz)
    return phases * spec.vout_v / (switching_frequency_hz * spec.vin_v)


def critical_inductance(
    spec: SystemSpec, phases: int, modules: int, switching_frequency_hz: float
) -> float:
    """Paper Eq. (4), preserved literally despite its Table-I conflict."""
    _validate_spec(spec)
    _validate_architecture(phases, modules)
    _validate_frequency(switching_frequency_hz)
    conversion_term = 1.0 - duty_cycle(spec, phases)
    return (
        phases * modules * spec.vout_v * conversion_term
        / (2.0 * spec.iout_a * switching_frequency_hz)
    )


def parallel_embedded_inductors(
    spec: SystemSpec, phases: int, modules: int, peak_rating_a: float
) -> tuple[float, int]:
    """Paper Eq. (5), plus the conservative engineering ceiling."""
    _validate_spec(spec)
    _validate_architecture(phases, modules)
    _require_positive("peak_rating_a", peak_rating_a)
    exact = 2.0 * spec.iout_a / (modules * phases * peak_rating_a)
    return exact, ceil(exact)


def unit_embedded_inductance(
    spec: SystemSpec,
    phases: int,
    switching_frequency_hz: float,
    peak_rating_a: float,
) -> float:
    """Paper Eq. (6), inductance required from each parallel unit."""
    _validate_spec(spec)
    _validate_architecture(phases)
    _validate_frequency(switching_frequency_hz)
    _require_positive("peak_rating_a", peak_rating_a)
    conversion_term = 1.0 - duty_cycle(spec, phases)
    return spec.vout_v * conversion_term / (
        switching_frequency_hz * peak_rating_a
    )


def evaluate_converter(
    spec: SystemSpec, phases: int, modules: int, switching_frequency_hz: float
) -> ConverterResult:
    ton = high_side_on_time(spec, phases, switching_frequency_hz)
    return ConverterResult(
        phases=phases,
        modules=modules,
        switching_frequency_hz=switching_frequency_hz,
        power_per_module_w=spec.pout_w / modules,
        duty_cycle=duty_cycle(spec, phases),
        high_side_on_time_s=ton,
        critical_inductance_h=critical_inductance(
            spec, phases, modules, switching_frequency_hz
        ),
        inductor_peak_current_a=inductor_peak_current(spec, phases, modules),
        minimum_on_time_s=spec.minimum_on_time_s,
        feasible_on_time=ton >= spec.minimum_on_time_s,
    )


def evaluate_embedded_inductor(
    spec: SystemSpec,
    phases: int,
    modules: int,
    switching_frequency_hz: float,
    peak_rating_a: float,
) -> EmbeddedInductorResult:
    exact, engineering = parallel_embedded_inductors(
        spec, phases, modules, peak_rating_a
    )
    return EmbeddedInductorResult(
        phases=phases,
        modules=modules,
        switching_frequency_hz=switching_frequency_hz,
        embedded_inductor_peak_rating_a=peak_rating_a,
        parallel_inductors_exact=exact,
        parallel_inductors_engineering=engineering,
        unit_inductance_h=unit_embedded_inductance(
            spec, phases, switching_frequency_hz, peak_rating_a
        ),
    )
