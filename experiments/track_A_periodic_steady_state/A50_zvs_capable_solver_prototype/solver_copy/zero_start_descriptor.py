"""Hybrid descriptor model for the Track-B true-zero-energy boundary.

This module translates the latest R04E17/R04E18 circuit boundary into

    E dz/dt + A_sigma z = r(t)

where ``sigma`` contains the commanded PWM switch state and the three
state-dependent precharge-diode states.  It is a mathematical model contract,
not yet a transient solver and not a P24-authored startup method.

A50 LOCAL COPY -- see `../BOUNDARY.md` Section 0 and Section 3.  This file is a
copy of `src/scb_ivr/zero_start_descriptor.py`, extended here (and only here)
with:

* `ZeroStartBoundary.dead_time_s` and `ZeroStartBoundary.switch_capacitance`,
  both defaulting to values that reproduce the original behavior exactly;
* a three-state per-phase `Mode` (`high_side_on` / `low_side_on`, both False
  meaning that phase is in dead time);
* a `commanded_pwm_mode` that emits HIGH -> DEADTIME -> LOW -> DEADTIME when
  `dead_time_s > 0`, and collapses to the exact original two-state schedule
  when `dead_time_s == 0`;
* parallel commutation capacitance across every high- and low-side switch
  branch, taken from `boundary.switch_capacitance`.

`src/scb_ivr/` is not modified and is not imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, pi, sqrt

import numpy as np
from numpy.typing import NDArray

from .commutation_capacitance import CommutationCapacitance
from .evidence import Evidence

#: The four high-side switch branches of the nP=4 series-capacitor ladder.
HIGH_SIDE_BRANCHES: tuple[tuple[str, str | None], ...] = (
    ("vin", "a1"),
    ("a1", "a2"),
    ("a2", "a3"),
    ("a3", "x4"),
)

#: The four low-side switch branches (each returns to the ground reference).
LOW_SIDE_BRANCHES: tuple[tuple[str, str | None], ...] = (
    ("x1", None),
    ("x2", None),
    ("x3", None),
    ("x4", None),
)


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
    dead_time_s: float = 0.0
    switch_capacitance: CommutationCapacitance | None = None
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
        if self.dead_time_s < 0:
            raise ValueError("dead time must be non-negative")
        if self.dead_time_s > 0:
            shortest = min(self.on_time_s, self.period_s - self.on_time_s)
            if self.dead_time_s >= shortest:
                raise ValueError(
                    "dead time must be shorter than both commanded conduction "
                    "intervals; the schedule would otherwise lose a state"
                )
        if self.switch_capacitance is not None:
            if (
                self.switch_capacitance.high_total_f < 0
                or self.switch_capacitance.low_total_f < 0
            ):
                raise ValueError("switch capacitance must be non-negative")

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
    """One commanded switching state of the four-phase stage.

    A50 change (`../BOUNDARY.md` Section 3.2): the high and low side of each
    phase are now INDEPENDENT.  ``high_side_on[p] is False and
    low_side_on[p] is False`` means phase ``p`` is in dead time -- the state
    the original single-boolean ``Mode`` could not represent at all.  Both
    True simultaneously is a commanded shoot-through and is rejected.
    """

    high_side_on: tuple[bool, bool, bool, bool]
    low_side_on: tuple[bool, bool, bool, bool]
    precharge_diode_on: tuple[bool, bool, bool]

    def __post_init__(self) -> None:
        if (
            len(self.high_side_on) != 4
            or len(self.low_side_on) != 4
            or len(self.precharge_diode_on) != 3
        ):
            raise ValueError("mode dimensions must match the four-phase boundary")
        if any(high and low for high, low in zip(self.high_side_on, self.low_side_on)):
            raise ValueError("a phase may not command both switches on")

    @property
    def dead_time_phases(self) -> tuple[bool, bool, bool, bool]:
        """True for each phase whose two switches are both commanded off."""
        return tuple(  # type: ignore[return-value]
            not high and not low
            for high, low in zip(self.high_side_on, self.low_side_on)
        )


def complementary_mode(
    high_side_on: tuple[bool, bool, bool, bool],
    precharge_diode_on: tuple[bool, bool, bool],
) -> Mode:
    """Build the original, strictly complementary two-state mode.

    Retained so that pre-A50 call sites -- which only ever knew a per-phase
    high-side boolean -- keep their exact original meaning.
    """
    return Mode(
        high_side_on,
        tuple(not value for value in high_side_on),  # type: ignore[arg-type]
        precharge_diode_on,
    )


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
    """Reproduce the fixed, phase-shifted R04E17/R04E18 gate equations.

    A50 change (`../BOUNDARY.md` Section 3.3): when ``boundary.dead_time_s``
    is positive, each phase emits

        HIGH -> DEADTIME -> LOW -> DEADTIME -> HIGH ...

    with both dead-time windows CENTERED on the original, unchanged ``T/4``-
    shifted commanded edges.  Writing ``d = dead_time_s`` and ``local`` for the
    phase-local time inside one period, the schedule is

        local in [0, d/2)                    DEADTIME  (turn-on window)
        local in [d/2, Ton - d/2)            HIGH
        local in [Ton - d/2, Ton + d/2)      DEADTIME  (turn-off window)
        local in [Ton + d/2, T - d/2)        LOW
        local in [T - d/2, T)                DEADTIME  (next turn-on window)

    so the HIGH and LOW commands each lose ``d/2`` at both of their ends and
    the original edge instants remain the centers of the transitions.  With
    ``d = 0`` this function takes the original code path verbatim and returns
    the exact original two-state schedule.
    """
    period = boundary.period_s
    dead_time = boundary.dead_time_s
    if dead_time <= 0.0:
        high = []
        for phase in range(boundary.phases):
            shifted = time_s - phase * period / boundary.phases
            local = shifted - floor(shifted / period) * period
            high.append(local < boundary.on_time_s)
        return complementary_mode(tuple(high), precharge_diode_on)  # type: ignore[arg-type]

    half = 0.5 * dead_time
    on_time = boundary.on_time_s
    high = []
    low = []
    for phase in range(boundary.phases):
        shifted = time_s - phase * period / boundary.phases
        local = shifted - floor(shifted / period) * period
        high.append(half <= local < on_time - half)
        low.append(on_time + half <= local < period - half)
    return Mode(tuple(high), tuple(low), precharge_diode_on)  # type: ignore[arg-type]


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

    # A50 change (`../BOUNDARY.md` Section 3.4): commutation capacitance now
    # sits in parallel with every switch branch.  `switch_capacitance is None`
    # yields 0.0 F, which `add_capacitance` turns into an exactly-zero rank-one
    # update -- i.e. the unmodified original E matrix, bit for bit.
    if boundary.switch_capacitance is None:
        high_switch_capacitance_f = 0.0
        low_switch_capacitance_f = 0.0
    else:
        high_switch_capacitance_f = boundary.switch_capacitance.high_total_f
        low_switch_capacitance_f = boundary.switch_capacitance.low_total_f

    high_pairs = HIGH_SIDE_BRANCHES
    low_pairs = LOW_SIDE_BRANCHES
    for high_on, low_on, high_pair, low_pair in zip(
        mode.high_side_on, mode.low_side_on, high_pairs, low_pairs
    ):
        add_conductance(
            *high_pair,
            boundary.switch_on_resistance_ohm
            if high_on
            else boundary.switch_off_resistance_ohm,
        )
        add_conductance(
            *low_pair,
            boundary.switch_on_resistance_ohm
            if low_on
            else boundary.switch_off_resistance_ohm,
        )
        if high_switch_capacitance_f:
            add_capacitance(*high_pair, high_switch_capacitance_f)
        if low_switch_capacitance_f:
            add_capacitance(*low_pair, low_switch_capacitance_f)

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
