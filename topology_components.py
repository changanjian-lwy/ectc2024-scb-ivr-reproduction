"""Modular circuit-description layer for the ECTC 2024 IVR reproduction.

The analytical equations live in ``ivr_framework.py``.  This file describes
the circuit structure separately so that adding a phase, capacitor, resistor,
or a future component model does not require changing the user interface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SeriesCapacitor:
    name: str
    capacitance_f: float
    esr_ohm: float = 0.0


@dataclass(frozen=True)
class SeriesResistor:
    name: str
    resistance_ohm: float


@dataclass(frozen=True)
class PhaseCell:
    """One electrical phase replicated across all parallel modules."""

    name: str
    series_capacitors: tuple[SeriesCapacitor, ...] = field(default_factory=tuple)
    series_resistors: tuple[SeriesResistor, ...] = field(default_factory=tuple)

    @property
    def total_series_resistance_ohm(self) -> float:
        return sum(item.resistance_ohm for item in self.series_resistors)


@dataclass(frozen=True)
class ModularTopology:
    name: str
    phases_per_module: int
    parallel_modules: int
    phase_template: PhaseCell
    shared_series_capacitors_per_module: int = 0

    @property
    def total_electrical_phases(self) -> int:
        return self.phases_per_module * self.parallel_modules

    @property
    def total_shared_series_capacitors(self) -> int:
        return self.shared_series_capacitors_per_module * self.parallel_modules

    def as_dict(self) -> dict:
        data = asdict(self)
        data["total_electrical_phases"] = self.total_electrical_phases
        data["total_shared_series_capacitors"] = (
            self.total_shared_series_capacitors
        )
        data["phase_series_resistance_ohm"] = (
            self.phase_template.total_series_resistance_ohm
        )
        return data


def paper_topology(
    phases: int,
    modules: int,
    shared_series_capacitors_per_module: int | None = None,
    extra_series_resistance_ohm: float = 0.0,
) -> ModularTopology:
    """Build the paper topology, with optional small structural additions.

    The paper uses nP-1 flying/series capacitors per module: three for a
    four-phase module.  Their capacitance values are not specified, so they
    remain structural counts instead of invented electrical values.
    """

    capacitor_count = (
        phases - 1
        if shared_series_capacitors_per_module is None
        else shared_series_capacitors_per_module
    )
    resistors = ()
    if extra_series_resistance_ohm > 0:
        resistors = (
            SeriesResistor("R_series_extra", extra_series_resistance_ohm),
        )
    return ModularTopology(
        name="ECTC-2024 multi-phase series-capacitor buck",
        phases_per_module=phases,
        parallel_modules=modules,
        phase_template=PhaseCell("repeated_phase_cell", series_resistors=resistors),
        shared_series_capacitors_per_module=capacitor_count,
    )
