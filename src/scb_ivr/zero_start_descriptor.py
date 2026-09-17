"""Hybrid descriptor model for the Track-B true-zero-energy boundary.

This module translates the latest R04E17/R04E18 circuit boundary into

    E dz/dt + A_sigma z = r(t)

where ``sigma`` contains the commanded PWM switch state and the three
state-dependent precharge-diode states.  It is a mathematical model contract,
not yet a transient solver and not a P24-authored startup method.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, pi, sqrt

import numpy as np
from numpy.typing import NDArray

from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class ZeroStartBoundary:
    vin_target_v: float = 48.0
    vout_target_v: float = 1.0
    module_power_w: float = 250.0
    phases: int = 4
    switching_frequency_hz: float = 5e6
    input_ramp_s: float = 22.87e-6
    phase_inductance_h: float = 1.4666667e-9
    phase_inductor_resistance_ohm: float = 1e-6
    flying_capacitances_f: tuple[float, float, float] = (3e-6, 3e-6, 3e-6)
    output_capacitance_f: float = 4.672e-3
    divider_enabled: bool = True
    divider_capacitance_f: float = 300e-6
    divider_leakage_ohm: float = 1e9
    source_inductance_h: float = 5e-9
    source_resistance_ohm: float = 10e-3
    switch_on_resistance_ohm: float = 1e-6
    switch_off_resistance_ohm: float = 1e12
    diode_on_resistance_ohm: float = 1e-3
    diode_off_resistance_ohm: float = 1e12
    evidence: Evidence = Evidence.CROSS_PAPER_EXTENSION

    def __post_init__(self) -> None:
        if self.phases != 4:
            raise ValueError("the present topology compiler is explicitly four-phase")
        positive = (
            self.vin_target_v,
            self.vout_target_v,
            self.module_power_w,
            self.switching_frequency_hz,
            self.input_ramp_s,
            self.phase_inductance_h,
            self.output_capacitance_f,
            self.source_inductance_h,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("physical boundary values must be positive")
        if len(self.flying_capacitances_f) != self.phases - 1:
            raise ValueError("nP=4 requires exactly three flying capacitors")
        if any(value <= 0 for value in self.flying_capacitances_f):
            raise ValueError("flying capacitances must be positive")

    @property
    def period_s(self) -> float:
        return 1 / self.switching_frequency_hz

    @property
    def duty(self) -> float:
        return self.phases * self.vout_target_v / self.vin_target_v

    @property
    def on_time_s(self) -> float:
        return self.duty * self.period_s

    @property
    def load_resistance_ohm(self) -> float:
        return self.vout_target_v**2 / self.module_power_w


@dataclass(frozen=True)
class Mode:
    high_side_on: tuple[bool, bool, bool, bool]
    precharge_diode_on: tuple[bool, bool, bool]

    def __post_init__(self) -> None:
        if len(self.high_side_on) != 4 or len(self.precharge_diode_on) != 3:
            raise ValueError("mode dimensions must match the four-phase boundary")


@dataclass(frozen=True)
class DescriptorSystem:
    e: NDArray[np.float64]
    a: NDArray[np.float64]
    rhs: NDArray[np.float64]
    variable_names: tuple[str, ...]
    node_names: tuple[str, ...]
    mode: Mode

    @property
    def size(self) -> int:
        return self.e.shape[0]

    @property
    def differential_rank(self) -> int:
        return int(np.linalg.matrix_rank(self.e))

    @property
    def pencil_rank_at_one(self) -> int:
        return int(np.linalg.matrix_rank(self.e + self.a))


@dataclass(frozen=True)
class StartupDimensionlessGroups:
    binding_resonance_hz: float
    ramp_resonance_cycles: float
    divider_to_flying_ratio: float | None


def equal_series_divider_capacitance_f(boundary: ZeroStartBoundary) -> float:
    if not boundary.divider_enabled:
        return 0.0
    return boundary.divider_capacitance_f / boundary.phases


def ideal_divider_ramp_current_a(boundary: ZeroStartBoundary) -> float:
    """Base current required by the equal series divider during a linear ramp."""
    return (
        equal_series_divider_capacitance_f(boundary)
        * boundary.vin_target_v
        / boundary.input_ramp_s
    )


def minimum_ramp_time_for_divider_current_s(
    boundary: ZeroStartBoundary, maximum_current_a: float
) -> float:
    """Necessary ramp-time screen from the divider charge alone."""
    if maximum_current_a <= 0:
        raise ValueError("maximum current must be positive")
    return (
        equal_series_divider_capacitance_f(boundary)
        * boundary.vin_target_v
        / maximum_current_a
    )


def startup_dimensionless_groups(
    boundary: ZeroStartBoundary,
    *,
    representative_flying_capacitance_f: float | None = None,
) -> StartupDimensionlessGroups:
    """Return independent groups changed by a Cfly/ramp sensitivity case.

    Reporting ``Cdiv/Cfly`` alongside ``Tramp*fres`` prevents a fixed-Cdiv
    Cfly sweep from being misread as a pure resonance experiment.
    """
    cfly = (
        boundary.flying_capacitances_f[0]
        if representative_flying_capacitance_f is None
        else representative_flying_capacitance_f
    )
    if cfly <= 0:
        raise ValueError("representative flying capacitance must be positive")
    omega = (
        boundary.duty
        * sqrt(2 - sqrt(2))
        / sqrt(boundary.phase_inductance_h * cfly)
    )
    frequency = omega / (2 * pi)
    ratio = boundary.divider_capacitance_f / cfly if boundary.divider_enabled else None
    return StartupDimensionlessGroups(
        binding_resonance_hz=frequency,
        ramp_resonance_cycles=boundary.input_ramp_s * frequency,
        divider_to_flying_ratio=ratio,
    )


def input_voltage_v(time_s: float, boundary: ZeroStartBoundary) -> float:
    if time_s <= 0:
        return 0.0
    return boundary.vin_target_v * min(time_s / boundary.input_ramp_s, 1.0)


def commanded_pwm_mode(
    time_s: float,
    boundary: ZeroStartBoundary,
    *,
    precharge_diode_on: tuple[bool, bool, bool] = (False, False, False),
) -> Mode:
    """Reproduce the fixed, phase-shifted R04E17/R04E18 gate equations."""
    period = boundary.period_s
    high = []
    for phase in range(boundary.phases):
        shifted = time_s - phase * period / boundary.phases
        local = shifted - floor(shifted / period) * period
        high.append(local < boundary.on_time_s)
    return Mode(tuple(high), precharge_diode_on)  # type: ignore[arg-type]


def true_zero_initial_vector(boundary: ZeroStartBoundary) -> NDArray[np.float64]:
    """All MNA variables are zero; therefore every stored-energy state is zero."""
    nodes = _node_names(boundary)
    # node voltages + five inductor currents + one source current
    return np.zeros(len(nodes) + 5 + 1, dtype=float)


def _node_names(boundary: ZeroStartBoundary) -> tuple[str, ...]:
    base = ("src", "src_r", "vin")
    divider = ("tap3", "tap2", "tap1") if boundary.divider_enabled else ()
    stage = ("a1", "a2", "a3", "x1", "x2", "x3", "x4", "out")
    return base + divider + stage


def assemble_descriptor(
    boundary: ZeroStartBoundary,
    mode: Mode,
    time_s: float,
) -> DescriptorSystem:
    """Assemble one linear DAE mode using modified nodal analysis.

    Switches and diodes use the same finite on/off resistance boundary as the
    latest LTspice model.  Diode-state selection is intentionally external:
    a future hybrid solver must change it only at complementarity events.
    """
    nodes = _node_names(boundary)
    node_index = {name: index for index, name in enumerate(nodes)}
    n_nodes = len(nodes)
    inductors = ("LPAR_IN", "L1", "L2", "L3", "L4")
    n_inductors = len(inductors)
    n_sources = 1
    size = n_nodes + n_inductors + n_sources
    e = np.zeros((size, size), dtype=float)
    a = np.zeros((size, size), dtype=float)
    rhs = np.zeros(size, dtype=float)

    def incidence(first: str | None, second: str | None) -> NDArray[np.float64]:
        vector = np.zeros(n_nodes, dtype=float)
        if first is not None:
            vector[node_index[first]] += 1
        if second is not None:
            vector[node_index[second]] -= 1
        return vector

    def add_conductance(first: str | None, second: str | None, resistance: float) -> None:
        branch = incidence(first, second)
        a[:n_nodes, :n_nodes] += np.outer(branch, branch) / resistance

    def add_capacitance(first: str | None, second: str | None, capacitance: float) -> None:
        branch = incidence(first, second)
        e[:n_nodes, :n_nodes] += capacitance * np.outer(branch, branch)

    add_conductance("src", "src_r", boundary.source_resistance_ohm)
    add_conductance("out", None, boundary.load_resistance_ohm)

    if boundary.divider_enabled:
        divider_pairs = (
            ("vin", "tap3"),
            ("tap3", "tap2"),
            ("tap2", "tap1"),
            ("tap1", None),
        )
        for first, second in divider_pairs:
            add_capacitance(first, second, boundary.divider_capacitance_f)
            add_conductance(first, second, boundary.divider_leakage_ohm)
        for enabled, (anode, cathode) in zip(
            mode.precharge_diode_on,
            (("tap3", "a1"), ("tap2", "a2"), ("tap1", "a3")),
        ):
            add_conductance(
                anode,
                cathode,
                boundary.diode_on_resistance_ohm
                if enabled
                else boundary.diode_off_resistance_ohm,
            )
    elif any(mode.precharge_diode_on):
        raise ValueError("precharge diodes cannot conduct when divider is absent")

    for capacitance, (first, second) in zip(
        boundary.flying_capacitances_f,
        (("a1", "x1"), ("a2", "x2"), ("a3", "x3")),
    ):
        add_capacitance(first, second, capacitance)
    add_capacitance("out", None, boundary.output_capacitance_f)

    high_pairs = (("vin", "a1"), ("a1", "a2"), ("a2", "a3"), ("a3", "x4"))
    low_pairs = (("x1", None), ("x2", None), ("x3", None), ("x4", None))
    for high_on, high_pair, low_pair in zip(
        mode.high_side_on, high_pairs, low_pairs
    ):
        add_conductance(
            *high_pair,
            boundary.switch_on_resistance_ohm
            if high_on
            else boundary.switch_off_resistance_ohm,
        )
        add_conductance(
            *low_pair,
            boundary.switch_off_resistance_ohm
            if high_on
            else boundary.switch_on_resistance_ohm,
        )

    inductor_pairs = (
        ("src_r", "vin"),
        ("x1", "out"),
        ("x2", "out"),
        ("x3", "out"),
        ("x4", "out"),
    )
    inductances = (boundary.source_inductance_h,) + (boundary.phase_inductance_h,) * 4
    resistances = (0.0,) + (boundary.phase_inductor_resistance_ohm,) * 4
    for index, (pair, inductance, resistance) in enumerate(
        zip(inductor_pairs, inductances, resistances)
    ):
        branch = incidence(*pair)
        row = n_nodes + index
        a[:n_nodes, row] += branch
        a[row, :n_nodes] -= branch
        a[row, row] += resistance
        e[row, row] += inductance

    source_branch = incidence("src", None)
    source_column = n_nodes + n_inductors
    a[:n_nodes, source_column] += source_branch
    a[source_column, :n_nodes] += source_branch
    rhs[source_column] = input_voltage_v(time_s, boundary)

    variables = nodes + inductors + ("I_VSTEP",)
    return DescriptorSystem(e, a, rhs, variables, nodes, mode)


def stored_energy_j(z: NDArray[np.float64], boundary: ZeroStartBoundary) -> float:
    """Stored energy for a consistent MNA vector; useful at the t=0 boundary."""
    mode = commanded_pwm_mode(0.0, boundary)
    system = assemble_descriptor(boundary, mode, 0.0)
    if z.shape != (system.size,):
        raise ValueError("state vector size does not match the selected boundary")
    return float(0.5 * z @ system.e @ z)
