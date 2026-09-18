"""A51 - the one-period map `F(z)` with real dead time, switch capacitance and
state-dependent (event-resolved) turn-on, built on A50's validated solver copy.

`BOUNDARY.md` Section 3.  Nothing here modifies, or writes to, A50's own
committed files; `solver_copy` is imported read-only through `sys.path`, and
`src/scb_ivr/` is neither imported nor read.

--------------------------------------------------------------------------
Period reference (`BOUNDARY.md` Section 3, A37's own `T0` convention)
--------------------------------------------------------------------------
A37's netlist sets `T0 = 0` at phase 1's own high-side turn-on instant (its
event machine enters `P1_M1`, which drives `gh1`, exactly there).  With a real
dead time `d` the framework's commanded schedule
(`solver_copy.zero_start_descriptor.commanded_pwm_mode`) centers each dead-time
window on the original nominal edge, so phase 1's commanded high-side turn-on is
at phase-local `d/2`.  This module therefore takes

    t0 = BASE_PERIOD_INDEX * T + d/2

as the period start, i.e. A37's `T0`, mapped onto the framework's own schedule.
`BASE_PERIOD_INDEX = 115` puts `t0` at `23.0 us + d/2`, safely past the
`22.87 us` input ramp so the descriptor's constant-`Vin` precondition holds
(the same base period A50's own gate 2 used).

With `T = 200 ns`, `Ton = 16.6667 ns` and `d = 2.15 ns` the period
`[t0, t0 + T)` contains, in order and without any overlap, all eight commanded
dead-time windows (local times relative to `t0`, in ns):

    ph1 HIGH        [0.0000,  14.5167)
    ph1 turn-OFF DT [14.5167, 16.6667)     low-side ZVS transition of phase 1
    normal          [16.6667, 47.8500)
    ph2 turn-ON  DT [47.8500, 50.0000)     high-side ZVS transition of phase 2
    ph2 HIGH        [50.0000, 64.5167)
    ph2 turn-OFF DT [64.5167, 66.6667)
    normal          [66.6667, 97.8500)
    ph3 turn-ON  DT [97.8500, 100.0000)
    ...
    ph4 turn-ON  DT [147.8500, 150.0000)
    ...
    ph4 turn-OFF DT [164.5167, 166.6667)
    normal          [166.6667, 197.8500)
    ph1 turn-ON  DT [197.8500, 200.0000)   high-side ZVS transition of phase 1

--------------------------------------------------------------------------
Why `F` is not affine
--------------------------------------------------------------------------
Inside a turn-on dead-time window the high-side switch is commanded off, but the
device's own reverse conduction (A27's ideal GaN clamp, and A37's own
`.rule ... V(vin,a1)<=0` admission rule) makes the phase start conducting the
instant `Vds` reaches zero.  Whether and when that happens depends on the state
itself, so the switching instant -- and hence the linear mode sequence over the
period -- is state-dependent.  The same holds for each turn-off window, where
A37's own `.rule P1_M2 P1_M3 V(x1)<=0` admits the low side at its own crossing.
Both are modeled here:

* turn-ON window of phase `p`: step finely; at the first sub-step where
  `Vds_p = V(high node) - V(next node) <= 0`, force `high_side_on[p] = True`
  for the remainder of the window (NATURAL ZVS).  If no such sub-step exists,
  the commanded schedule turns the high side on at the window end with whatever
  `Vds` remains (HARD SWITCH), and that residual is recorded.
* turn-OFF window of phase `p`: step finely; at the first sub-step where
  `V(x_{p+1}) <= 0`, force `low_side_on[p] = True` for the remainder of the
  window.  Otherwise the commanded schedule takes over at the window end.

The turn-ON verdict itself is produced by A50's own `resolve_deadtime_window`,
unchanged, so the reported ZVS numbers come from the already-validated function
rather than from this module's stepping loop.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

HERE = Path(__file__).resolve().parent
A50_DIR = HERE.parent / "A50_zvs_capable_solver_prototype"
if str(A50_DIR) not in sys.path:
    sys.path.insert(0, str(A50_DIR))

from solver_copy.commutation_capacitance import CommutationCapacitance  # noqa: E402
from solver_copy.device_library import (  # noqa: E402
    GS61008T,
    P25_GS61008T_POPULATION,
    CapacitanceView,
)
from solver_copy.evidence import Evidence  # noqa: E402
from solver_copy.zero_start_descriptor import (  # noqa: E402
    HIGH_SIDE_BRANCHES,
    Mode,
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
)
from solver_copy.zero_start_hybrid_solver import (  # noqa: E402
    HybridStep,
    advance_fixed_diode_step,
    diode_observation,
    resolve_deadtime_window,
)

# `_candidate_step` is A50's own (unchanged) backward-Euler descriptor kernel.
# It is used here READ-ONLY, and only because it is the single place that
# accepts an explicit `high_side_on` / `low_side_on` pair -- which is exactly
# what an event-resolved early turn-on needs.  `advance_fixed_diode_step` is
# this same kernel with the mode taken from the commanded schedule instead.
from solver_copy.zero_start_hybrid_solver import _candidate_step  # noqa: E402

# ---------------------------------------------------------------------------
# Boundary (`BOUNDARY.md` Section 5)
# ---------------------------------------------------------------------------
#: `R04E8`/`A49`'s corrected flying capacitance, re-verified in A51 step 2.
CFLY_F = 3e-6
#: A42's own GS61008T Co(tr) plug-in: 385 pF high side, 770 pF low side.
SWITCH_CAPACITANCE = CommutationCapacitance(
    high_device_f=GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, P25_GS61008T_POPULATION.high_side_parallel
    ),
    low_device_f=GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, P25_GS61008T_POPULATION.low_side_parallel
    ),
    device_evidence=Evidence.EXTERNAL_DEVICE_DATA,
)
#: A48's own published practical bracket center for the 7.77% single-phase case.
DEAD_TIME_S = 2.15e-9
#: First whole PWM period at or after the 22.87 us input ramp (A50 gate 2's own).
BASE_PERIOD_INDEX = 115
#: P24's own locked Table-1 peak current, used only for the safety bound scale.
IPEAK_P24_A = 125.0
#: Standing project safety bound on every phase current.
PHASE_CURRENT_LIMIT_A = 250.0

#: A37's own published best candidate (`A37_.../best_candidate.json`).
A37_BEST_CANDIDATE = {
    "IL1_INIT": 5.2947,
    "IL2_INIT": 21.205095337,
    "IL3_INIT": 41.5782701063,
    "IL4_INIT": 84.1447433786,
    "VC1_INIT": 36.000066454,
    "VC2_INIT": 23.9999142326,
    "VC3_INIT": 12.0006048777,
}
#: A37's own `.ic` ladder node voltages at `T0` (from its own netlist, verbatim).
A37_IC_LADDER_V = {"a1": 48.0, "a2": 24.0, "a3": 12.0, "x4": 0.0, "out": 1.0}


def build_boundary(
    *,
    dead_time_s: float = DEAD_TIME_S,
    cfly_f: float = CFLY_F,
    switch_on_resistance_ohm: float = 1e-6,
    module_power_w: float = 250.0,
) -> ZeroStartBoundary:
    """The A51 four-phase boundary.

    Every field not named here is `ZeroStartBoundary`'s own dataclass default,
    which is exactly the boundary A50's gate-1 regression reproduced against
    `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`.  `divider_enabled` stays
    at its default `True`, which is what makes the descriptor the 20-variable
    vector `BOUNDARY.md` Section 3 names.
    """
    return ZeroStartBoundary(
        flying_capacitances_f=(cfly_f, cfly_f, cfly_f),
        switch_on_resistance_ohm=switch_on_resistance_ohm,
        module_power_w=module_power_w,
        dead_time_s=dead_time_s,
        switch_capacitance=SWITCH_CAPACITANCE,
        evidence=Evidence.CROSS_PAPER_EXTENSION,
    )


def variable_names(boundary: ZeroStartBoundary) -> tuple[str, ...]:
    mode = commanded_pwm_mode(0.0, boundary)
    return assemble_descriptor(boundary, mode, 0.0).variable_names


def period_start_s(boundary: ZeroStartBoundary) -> float:
    """A37's `T0`: phase 1's own commanded high-side turn-on instant."""
    return BASE_PERIOD_INDEX * boundary.period_s + 0.5 * boundary.dead_time_s


# ---------------------------------------------------------------------------
# Seed-state conversion (`BOUNDARY.md` Section 4.1)
# ---------------------------------------------------------------------------
def a37_seed_state(boundary: ZeroStartBoundary) -> tuple[NDArray[np.float64], list[dict]]:
    """Convert A37's own seven published values into the 20-variable descriptor.

    The conversion is table-driven and every entry carries its own source, so
    the mapping is explicit rather than assumed.  A37's netlist topology is
    node-for-node the descriptor's own (`SH1 vin a1`, `SH2 a1 a2`, `SH3 a2 a3`,
    `SH4 a3 x4`; `SL1..SL4 x1..x4 g`; `C1 a1 x1`, `C2 a2 x2`, `C3 a3 x3`;
    `LIND1..4 x1..x4 out`), so the seven solved coordinates map directly.
    """
    seed = A37_BEST_CANDIDATE
    rows: list[dict] = [
        {
            "variable": "src",
            "value": boundary.vin_target_v,
            "source": "A37 `V1 vin 0 {VIN}` hard 48 V source; equals "
            "`input_voltage_v(t0)` post-ramp",
        },
        {
            "variable": "src_r",
            "value": boundary.vin_target_v,
            "source": "A37 has no source impedance; seeded equal to `src` "
            "(zero drop across `source_resistance_ohm`)",
        },
        {
            "variable": "vin",
            "value": A37_IC_LADDER_V["a1"],
            "source": "A37 `.ic V(xmod:a1)=48` with `SH1` closed at T0 => "
            "`vin = a1 = 48 V`",
        },
        {
            "variable": "tap3",
            "value": 0.75 * boundary.vin_target_v,
            "source": "no A37 analog (Track-B precharge divider); seeded at the "
            "equal-series divider equilibrium 3*48/4",
        },
        {
            "variable": "tap2",
            "value": 0.50 * boundary.vin_target_v,
            "source": "no A37 analog; equal-series divider equilibrium 2*48/4",
        },
        {
            "variable": "tap1",
            "value": 0.25 * boundary.vin_target_v,
            "source": "no A37 analog; equal-series divider equilibrium 1*48/4",
        },
        {
            "variable": "a1",
            "value": A37_IC_LADDER_V["a1"],
            "source": "A37 `.ic V(xmod:a1)=48`",
        },
        {
            "variable": "a2",
            "value": A37_IC_LADDER_V["a2"],
            "source": "A37 `.ic V(xmod:a2)=24`",
        },
        {
            "variable": "a3",
            "value": A37_IC_LADDER_V["a3"],
            "source": "A37 `.ic V(xmod:a3)=12`",
        },
        {
            "variable": "x1",
            "value": A37_IC_LADDER_V["a1"] - seed["VC1_INIT"],
            "source": "A37 `.ic V(xmod:x1)={48-VC1_INIT}` => carries `VC1_INIT`",
        },
        {
            "variable": "x2",
            "value": A37_IC_LADDER_V["a2"] - seed["VC2_INIT"],
            "source": "A37 `.ic V(xmod:x2)={24-VC2_INIT}` => carries `VC2_INIT`",
        },
        {
            "variable": "x3",
            "value": A37_IC_LADDER_V["a3"] - seed["VC3_INIT"],
            "source": "A37 `.ic V(xmod:x3)={12-VC3_INIT}` => carries `VC3_INIT`",
        },
        {
            "variable": "x4",
            "value": A37_IC_LADDER_V["x4"],
            "source": "A37 `.ic V(xmod:x4)=0` (phase 4's low side conducting)",
        },
        {
            "variable": "out",
            "value": A37_IC_LADDER_V["out"],
            "source": "A37 `.ic V(out)=1`",
        },
        {
            "variable": "LPAR_IN",
            "value": boundary.module_power_w / boundary.vin_target_v,
            "source": "no A37 analog (A37 has no input inductor); seeded at the "
            "250 W average input current 250/48",
        },
        {
            "variable": "L1",
            "value": seed["IL1_INIT"],
            "source": "A37 `IL1_INIT` (`LIND1 x1 out ... ic={IL1_INIT}`)",
        },
        {
            "variable": "L2",
            "value": seed["IL2_INIT"],
            "source": "A37 `IL2_INIT`",
        },
        {
            "variable": "L3",
            "value": seed["IL3_INIT"],
            "source": "A37 `IL3_INIT`",
        },
        {
            "variable": "L4",
            "value": seed["IL4_INIT"],
            "source": "A37 `IL4_INIT`",
        },
        {
            "variable": "I_VSTEP",
            "value": -boundary.module_power_w / boundary.vin_target_v,
            "source": "purely algebraic (its column of `E` is exactly zero, so it "
            "cannot influence propagation); seeded at `-LPAR_IN` for MNA sign "
            "consistency",
        },
    ]
    names = variable_names(boundary)
    if tuple(row["variable"] for row in rows) != names:
        raise RuntimeError(
            f"seed table ordering != descriptor ordering:\n"
            f"  table: {tuple(row['variable'] for row in rows)}\n"
            f"  descriptor: {names}"
        )
    state = np.array([row["value"] for row in rows], dtype=float)
    # Self-check: the three flying-capacitor voltages must come back out exactly.
    index = {name: position for position, name in enumerate(names)}
    for number, key in ((1, "VC1_INIT"), (2, "VC2_INIT"), (3, "VC3_INIT")):
        recovered = state[index[f"a{number}"]] - state[index[f"x{number}"]]
        if abs(recovered - seed[key]) > 1e-12:
            raise RuntimeError(f"VC{number} round-trip failed: {recovered} vs {seed[key]}")
    return state, rows


# ---------------------------------------------------------------------------
# Interval schedule
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Interval:
    kind: str  # "normal" | "turn_on" | "turn_off"
    start_s: float
    end_s: float
    phase_index: int | None


def period_intervals(boundary: ZeroStartBoundary, t0: float) -> tuple[Interval, ...]:
    """Ordered, non-overlapping cover of `[t0, t0 + T)` (module docstring)."""
    period = boundary.period_s
    half = 0.5 * boundary.dead_time_s
    windows: list[tuple[str, float, int]] = []
    for phase in range(boundary.phases):
        nominal_on = BASE_PERIOD_INDEX * period + phase * period / boundary.phases
        nominal_off = nominal_on + boundary.on_time_s
        for center, kind in ((nominal_on, "turn_on"), (nominal_off, "turn_off")):
            # shift each nominal edge into `[t0, t0 + T)`
            shifted = center
            while shifted - half < t0 - 1e-18:
                shifted += period
            while shifted - half >= t0 + period - 1e-18:
                shifted -= period
            windows.append((kind, shifted, phase))
    windows.sort(key=lambda item: item[1])

    intervals: list[Interval] = []
    cursor = t0
    for kind, center, phase in windows:
        start = center - half
        end = center + half
        if start < cursor - 1e-18:
            raise RuntimeError("dead-time windows overlap; reduce dead_time_s")
        if start > cursor + 1e-18:
            intervals.append(Interval("normal", cursor, start, None))
        intervals.append(Interval(kind, start, min(end, t0 + period), phase))
        cursor = min(end, t0 + period)
    if cursor < t0 + period - 1e-18:
        intervals.append(Interval("normal", cursor, t0 + period, None))
    return tuple(intervals)


# ---------------------------------------------------------------------------
# Stepping helpers
# ---------------------------------------------------------------------------
def _initial_step(
    boundary: ZeroStartBoundary,
    state: NDArray[np.float64],
    time_s: float,
    diode_state: tuple[bool, bool, bool],
) -> HybridStep:
    mode = commanded_pwm_mode(time_s, boundary, precharge_diode_on=diode_state)
    return HybridStep(
        time_s=time_s,
        state=np.asarray(state, dtype=float).copy(),
        mode=mode,
        diode_observation=diode_observation(state, boundary, mode),
        descriptor_residual_inf=0.0,
        descriptor_relative_backward_error=0.0,
    )


def _advance_forced(
    previous: HybridStep,
    next_time_s: float,
    boundary: ZeroStartBoundary,
    high_side_on: tuple[bool, ...],
    low_side_on: tuple[bool, ...],
    diode_state: tuple[bool, bool, bool],
) -> HybridStep:
    """One backward-Euler step with an explicitly overridden switch mode.

    Identical to `advance_fixed_diode_step` except that the mode is supplied by
    the caller instead of read from the commanded schedule.  Both funnel into
    A50's own unchanged `_candidate_step`.
    """
    return _candidate_step(
        previous.state,
        previous.time_s,
        next_time_s,
        boundary,
        tuple(high_side_on),  # type: ignore[arg-type]
        tuple(low_side_on),  # type: ignore[arg-type]
        diode_state,
    )


def _march(
    previous: HybridStep,
    end_s: float,
    step_s: float,
    boundary: ZeroStartBoundary,
    diode_state: tuple[bool, bool, bool],
    monitor: "Monitor",
) -> HybridStep:
    """Uniform commanded-schedule stepping to `end_s` (no mode override)."""
    current = previous
    tolerance = max(1e-21, (end_s - previous.time_s) * 1e-12)
    while current.time_s < end_s - tolerance:
        next_time_s = min(current.time_s + step_s, end_s)
        current = advance_fixed_diode_step(current, next_time_s, boundary, diode_state)
        monitor.observe(current)
    return current


def _window_mode(
    boundary: ZeroStartBoundary,
    start_s: float,
    end_s: float,
    diode_state: tuple[bool, bool, bool],
) -> Mode:
    """The commanded mode, which is constant across a whole dead-time window.

    Dead-time windows never overlap at `d = 2.15 ns` (see `period_intervals`,
    which raises if they ever did), and each window lies strictly inside one
    commanded segment of every phase, so one sample at the window midpoint
    determines the mode for the entire window.  Capturing it explicitly is what
    lets a crossing be refined to a sub-grid instant: an arbitrary partial step
    can then be taken without re-deriving the schedule from a midpoint that no
    longer sits where `advance_fixed_diode_step` would assume.
    """
    return commanded_pwm_mode(
        0.5 * (start_s + end_s), boundary, precharge_diode_on=diode_state
    )


def _refine_crossing(
    previous: HybridStep,
    upper_time_s: float,
    boundary: ZeroStartBoundary,
    high_side_on: tuple[bool, ...],
    low_side_on: tuple[bool, ...],
    diode_state: tuple[bool, bool, bool],
    value_of,
    *,
    maximum_iterations: int = 60,
    voltage_tolerance_v: float = 1e-13,
) -> HybridStep:
    """Locate the sub-grid instant at which `value_of(state)` reaches zero.

    Without this the switching instant would be quantized to `sub_step_s`, and
    since `dV/dt` at a low-side crossing is of order `100 V/ns`, a `5 ps` grid
    would put a `0.5 V` staircase discontinuity into `F` -- which would floor the
    attainable fixed-point residual near `1e-2` relative and make the Newton
    Jacobian meaningless.  `value_of(state(dt))` is a smooth function of the
    step size for a fixed mode, so plain bisection on `dt` converges cleanly and
    deterministically.  Bisection (not secant) is used so the bracket is never
    lost, which matters because the two ends can differ by many volts.
    """
    low = 0.0
    high = upper_time_s - previous.time_s
    value_low = value_of(previous.state)
    if value_low <= 0.0:
        return previous
    best = _candidate_step(
        previous.state,
        previous.time_s,
        previous.time_s + high,
        boundary,
        tuple(high_side_on),  # type: ignore[arg-type]
        tuple(low_side_on),  # type: ignore[arg-type]
        diode_state,
    )
    for _ in range(maximum_iterations):
        middle = 0.5 * (low + high)
        if middle <= low or middle >= high:
            break
        candidate = _candidate_step(
            previous.state,
            previous.time_s,
            previous.time_s + middle,
            boundary,
            tuple(high_side_on),  # type: ignore[arg-type]
            tuple(low_side_on),  # type: ignore[arg-type]
            diode_state,
        )
        value = value_of(candidate.state)
        if value <= 0.0:
            high = middle
            best = candidate
            if -value <= voltage_tolerance_v:
                break
        else:
            low = middle
            if value <= voltage_tolerance_v:
                best = candidate
                break
    return best


@dataclass
class Monitor:
    """Running safety/validity observations over one `F` evaluation."""

    index: dict[str, int]
    maximum_abs_phase_current_a: float = 0.0
    maximum_abs_input_current_a: float = 0.0
    maximum_off_diode_forward_voltage_v: float = float("-inf")
    maximum_relative_backward_error: float = 0.0
    step_count: int = 0
    argmax_phase: int = -1
    argmax_time_s: float = float("nan")
    phase_minimum_a: list[float] = field(default_factory=lambda: [float("inf")] * 4)
    phase_maximum_a: list[float] = field(default_factory=lambda: [float("-inf")] * 4)
    #: Time-weighted (right-endpoint rule, as `periodic_orbit_metrics` uses)
    #: accumulators, so the recovered orbit can be compared with A50's own
    #: published gate-1 period metrics without storing the whole trajectory.
    weighted_sum: dict[str, float] = field(default_factory=dict)
    weighted_duration_s: float = 0.0
    _previous_time_s: float | None = None

    def observe(self, step: HybridStep) -> None:
        self.step_count += 1
        if self._previous_time_s is not None:
            dt = step.time_s - self._previous_time_s
            if dt > 0:
                self.weighted_duration_s += dt
                for name in ("out", "a1", "a2", "a3", "x1", "x2", "x3", "x4", "LPAR_IN"):
                    self.weighted_sum[name] = self.weighted_sum.get(name, 0.0) + dt * float(
                        step.state[self.index[name]]
                    )
        self._previous_time_s = step.time_s
        for phase in range(4):
            signed = float(step.state[self.index[f"L{phase + 1}"]])
            self.phase_minimum_a[phase] = min(self.phase_minimum_a[phase], signed)
            self.phase_maximum_a[phase] = max(self.phase_maximum_a[phase], signed)
            value = abs(signed)
            if value > self.maximum_abs_phase_current_a:
                self.maximum_abs_phase_current_a = value
                self.argmax_phase = phase + 1
                self.argmax_time_s = step.time_s
        self.maximum_abs_input_current_a = max(
            self.maximum_abs_input_current_a,
            abs(float(step.state[self.index["LPAR_IN"]])),
        )
        self.maximum_relative_backward_error = max(
            self.maximum_relative_backward_error,
            step.descriptor_relative_backward_error,
        )
        for voltage, enabled in zip(
            step.diode_observation.anode_minus_cathode_v,
            step.mode.precharge_diode_on,
        ):
            if not enabled:
                self.maximum_off_diode_forward_voltage_v = max(
                    self.maximum_off_diode_forward_voltage_v, float(voltage)
                )


# ---------------------------------------------------------------------------
# Per-window resolution
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TurnOnVerdict:
    """One phase's own high-side turn-on dead-time window outcome."""

    phase_index: int
    window_start_s: float
    window_end_s: float
    sub_step_s: float
    step_count: int
    commanded_dead_time_confirmed: bool
    initial_vds_v: float
    minimum_abs_vds_v: float
    minimum_abs_vds_time_s: float
    minimum_signed_vds_v: float
    vds_at_window_end_v: float
    crossed_zero: bool
    sign_change_time_s: float | None
    crossed_1mv: bool
    crossed_1mv_time_s: float | None
    phase_current_at_crossing_a: float | None
    switch_on_time_s: float
    switch_on_delay_s: float
    natural_zvs: bool
    hard_switch_residual_v: float
    maximum_relative_backward_error: float


@dataclass(frozen=True)
class TurnOffVerdict:
    """One phase's own low-side turn-on (high-side turn-off) window outcome."""

    phase_index: int
    window_start_s: float
    window_end_s: float
    sub_step_s: float
    initial_switch_node_v: float
    minimum_signed_switch_node_v: float
    switch_node_at_window_end_v: float
    crossed_zero: bool
    sign_change_time_s: float | None
    switch_on_time_s: float
    natural: bool
    hard_switch_residual_v: float


def _resolve_turn_on(
    boundary: ZeroStartBoundary,
    initial: HybridStep,
    phase_index: int,
    window_end_s: float,
    sub_step_s: float,
    diode_state: tuple[bool, bool, bool],
    monitor: Monitor,
) -> tuple[HybridStep, TurnOnVerdict]:
    """Step one turn-on dead-time window, admitting the high side at `Vds <= 0`.

    The verdict numbers come from A50's own `resolve_deadtime_window`, called
    unchanged on the whole commanded window.  This function then re-uses that
    call's own stored sub-steps to find the first grid instant at which the
    high side becomes admissible, and continues from there with the high side
    forced on for the remainder of the window.
    """
    window = resolve_deadtime_window(
        boundary,
        initial,
        phase_index=phase_index,
        window_end_s=window_end_s,
        sub_step_s=sub_step_s,
        crossing_tolerance_v=1e-3,
        diode_state=diode_state,
        store_steps=True,
    )
    names = variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    first, second = HIGH_SIDE_BRANCHES[phase_index]

    def vds(step: HybridStep) -> float:
        value = float(step.state[index[first]])
        if second is not None:
            value -= float(step.state[index[second]])
        return value

    dead_mode = _window_mode(boundary, initial.time_s, window_end_s, diode_state)
    admit_position: int | None = None
    for position, step in enumerate(window.steps):
        if position == 0:
            if vds(step) <= 0.0:
                admit_position = 0
            continue
        monitor.observe(step)
        if admit_position is None and vds(step) <= 0.0:
            admit_position = position

    if admit_position is None:
        final = window.final
        natural = False
        switch_on_time_s = window_end_s
        residual = window.final_switch_voltage_v
    else:
        # Refine the switching instant off the sub-step grid (see
        # `_refine_crossing`); `admit_position == 0` means the window opened
        # already at or below zero, so no refinement is possible or needed.
        if admit_position == 0:
            current = window.steps[0]
        else:
            current = _refine_crossing(
                window.steps[admit_position - 1],
                window.steps[admit_position].time_s,
                boundary,
                dead_mode.high_side_on,
                dead_mode.low_side_on,
                diode_state,
                lambda state: float(state[index[first]])
                - (0.0 if second is None else float(state[index[second]])),
            )
            monitor.observe(current)
        natural = True
        switch_on_time_s = current.time_s
        residual = 0.0
        high = list(dead_mode.high_side_on)
        low = list(dead_mode.low_side_on)
        high[phase_index] = True
        low[phase_index] = False
        tolerance = max(1e-21, (window_end_s - initial.time_s) * 1e-12)
        while current.time_s < window_end_s - tolerance:
            next_time_s = min(current.time_s + sub_step_s, window_end_s)
            current = _advance_forced(
                current, next_time_s, boundary, tuple(high), tuple(low), diode_state
            )
            monitor.observe(current)
        final = current

    verdict = TurnOnVerdict(
        phase_index=phase_index,
        window_start_s=window.start_time_s,
        window_end_s=window.commanded_end_time_s,
        sub_step_s=sub_step_s,
        step_count=window.step_count,
        commanded_dead_time_confirmed=window.commanded_dead_time_confirmed,
        initial_vds_v=window.initial_switch_voltage_v,
        minimum_abs_vds_v=window.minimum_abs_switch_voltage_v,
        minimum_abs_vds_time_s=window.minimum_abs_switch_voltage_time_s,
        minimum_signed_vds_v=window.minimum_signed_switch_voltage_v,
        vds_at_window_end_v=window.final_switch_voltage_v,
        crossed_zero=window.sign_change_time_s is not None,
        sign_change_time_s=window.sign_change_time_s,
        crossed_1mv=window.crossed_tolerance,
        crossed_1mv_time_s=window.crossed_tolerance_time_s,
        phase_current_at_crossing_a=window.switch_current_at_crossing_a,
        switch_on_time_s=switch_on_time_s,
        switch_on_delay_s=switch_on_time_s - window.start_time_s,
        natural_zvs=natural,
        hard_switch_residual_v=residual,
        maximum_relative_backward_error=(
            window.maximum_descriptor_relative_backward_error
        ),
    )
    return final, verdict


def _resolve_turn_off(
    boundary: ZeroStartBoundary,
    initial: HybridStep,
    phase_index: int,
    window_end_s: float,
    sub_step_s: float,
    diode_state: tuple[bool, bool, bool],
    monitor: Monitor,
) -> tuple[HybridStep, TurnOffVerdict]:
    """Step one turn-off dead-time window, admitting the low side at `V(x) <= 0`.

    Mirrors A37's own `.rule P1_M2 P1_M3 V(x1)<=0` low-side admission rule.
    """
    names = variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    node = f"x{phase_index + 1}"

    def switch_node(state: NDArray[np.float64]) -> float:
        return float(state[index[node]])

    dead_mode = _window_mode(boundary, initial.time_s, window_end_s, diode_state)
    high = list(dead_mode.high_side_on)
    low = list(dead_mode.low_side_on)
    current = initial
    initial_v = switch_node(initial.state)
    minimum_signed = initial_v
    sign_change_time_s: float | None = None
    admitted = initial_v <= 0.0
    switch_on_time_s = initial.time_s if admitted else window_end_s
    if admitted:
        high[phase_index] = False
        low[phase_index] = True
    tolerance = max(1e-21, (window_end_s - initial.time_s) * 1e-12)
    while current.time_s < window_end_s - tolerance:
        next_time_s = min(current.time_s + sub_step_s, window_end_s)
        following = _advance_forced(
            current, next_time_s, boundary, tuple(high), tuple(low), diode_state
        )
        value = switch_node(following.state)
        if not admitted and value <= 0.0:
            # Refine the low-side admission instant off the sub-step grid.
            following = _refine_crossing(
                current,
                next_time_s,
                boundary,
                tuple(high),
                tuple(low),
                diode_state,
                switch_node,
            )
            admitted = True
            switch_on_time_s = following.time_s
            sign_change_time_s = following.time_s
            high[phase_index] = False
            low[phase_index] = True
            value = switch_node(following.state)
        current = following
        monitor.observe(current)
        minimum_signed = min(minimum_signed, value)

    verdict = TurnOffVerdict(
        phase_index=phase_index,
        window_start_s=initial.time_s,
        window_end_s=window_end_s,
        sub_step_s=sub_step_s,
        initial_switch_node_v=initial_v,
        minimum_signed_switch_node_v=minimum_signed,
        switch_node_at_window_end_v=switch_node(current.state),
        crossed_zero=admitted,
        sign_change_time_s=sign_change_time_s,
        switch_on_time_s=switch_on_time_s,
        natural=admitted,
        hard_switch_residual_v=0.0 if admitted else switch_node(current.state),
    )
    return current, verdict


# ---------------------------------------------------------------------------
# The one-period map
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FreeResonanceProbe:
    """What a phase's own commutation would do if the dead time were longer.

    `resolve_deadtime_window` cannot answer this: it integrates with
    `advance_fixed_diode_step`, which reads the COMMANDED schedule, so pushing
    its `window_end_s` past the real window end simply lets the commanded
    high-side turn-on happen and reports the resulting (meaningless) `Vds ~ 0`.
    This probe instead HOLDS the window's own dead-time mode for the whole
    requested duration, which is the honest "what if `d` were larger" question.

    The held mode is exact for every other phase for up to `Ton - d/2 = 15.6 ns`
    after a turn-on window opens, because no other phase has a commanded
    transition inside that span -- so a `<= 10 ns` probe changes nothing except
    the one phase being asked about.
    """

    phase_index: int
    start_time_s: float
    duration_s: float
    sub_step_s: float
    step_count: int
    phase_current_at_start_a: float
    initial_vds_v: float
    minimum_abs_vds_v: float
    minimum_abs_vds_time_s: float
    minimum_signed_vds_v: float
    downward_excursion_v: float
    crossed_zero: bool
    sign_change_time_s: float | None
    crossed_within_commanded_dead_time: bool
    maximum_relative_backward_error: float


def free_resonance_probe(
    boundary: ZeroStartBoundary,
    initial: HybridStep,
    *,
    phase_index: int,
    duration_s: float,
    sub_step_s: float,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
) -> FreeResonanceProbe:
    """Hold the dead-time mode for `duration_s` and watch one phase's `Vds`."""
    if duration_s <= 0 or sub_step_s <= 0:
        raise ValueError("probe duration and sub-step must be positive")
    dead_mode = _window_mode(
        boundary, initial.time_s, initial.time_s + boundary.dead_time_s, diode_state
    )
    if dead_mode.high_side_on[phase_index] or dead_mode.low_side_on[phase_index]:
        raise ValueError("probe must start inside the phase's own dead-time window")
    names = variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    first, second = HIGH_SIDE_BRANCHES[phase_index]

    def vds(state: NDArray[np.float64]) -> float:
        value = float(state[index[first]])
        if second is not None:
            value -= float(state[index[second]])
        return value

    end_s = initial.time_s + duration_s
    commanded_end_s = initial.time_s + boundary.dead_time_s
    current = initial
    initial_vds = vds(initial.state)
    minimum_abs = abs(initial_vds)
    minimum_abs_time = initial.time_s
    minimum_signed = initial_vds
    previous = initial_vds
    sign_change_time_s: float | None = None
    backward_error = initial.descriptor_relative_backward_error
    step_count = 0
    tolerance = max(1e-21, duration_s * 1e-12)
    while current.time_s < end_s - tolerance:
        next_time_s = min(current.time_s + sub_step_s, end_s)
        current = _advance_forced(
            current,
            next_time_s,
            boundary,
            dead_mode.high_side_on,
            dead_mode.low_side_on,
            diode_state,
        )
        step_count += 1
        value = vds(current.state)
        backward_error = max(backward_error, current.descriptor_relative_backward_error)
        if abs(value) < minimum_abs:
            minimum_abs = abs(value)
            minimum_abs_time = current.time_s
        minimum_signed = min(minimum_signed, value)
        if sign_change_time_s is None and previous * value < 0.0:
            span = value - previous
            fraction = 0.0 if span == 0.0 else -previous / span
            step_start_s = current.time_s - sub_step_s
            sign_change_time_s = step_start_s + fraction * sub_step_s
        previous = value
    return FreeResonanceProbe(
        phase_index=phase_index,
        start_time_s=initial.time_s,
        duration_s=duration_s,
        sub_step_s=sub_step_s,
        step_count=step_count,
        phase_current_at_start_a=float(
            initial.state[index[f"L{phase_index + 1}"]]
        ),
        initial_vds_v=initial_vds,
        minimum_abs_vds_v=minimum_abs,
        minimum_abs_vds_time_s=minimum_abs_time,
        minimum_signed_vds_v=minimum_signed,
        downward_excursion_v=initial_vds - minimum_signed,
        crossed_zero=sign_change_time_s is not None,
        sign_change_time_s=sign_change_time_s,
        crossed_within_commanded_dead_time=bool(
            sign_change_time_s is not None and sign_change_time_s <= commanded_end_s
        ),
        maximum_relative_backward_error=backward_error,
    )


def measure_node_capacitance_f(
    boundary: ZeroStartBoundary,
    initial: HybridStep,
    *,
    phase_index: int,
    delta_a: float = 1.0,
    step_s: float = 0.5e-12,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
) -> float:
    """Measure the capacitance the phase's own switching node commutates.

    A50 Section 3.1 argued STRUCTURALLY that phase 4 commutates `1155 pF` while
    phase 1 commutates `1540 pF` (because node `a1` carries two high-side
    switches), i.e. that the four phases are not interchangeable.  This measures
    it instead of arguing it: with the dead-time mode held, perturb only the
    phase's own inductor current by `delta_a` and take one short step; to first
    order `dV(x_p) = -delta_a * step_s / C_eff`, and everything the two runs
    share cancels.  No closed form and no assumption about the rest of the
    network enters.
    """
    dead_mode = _window_mode(
        boundary, initial.time_s, initial.time_s + boundary.dead_time_s, diode_state
    )
    names = variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    node = f"x{phase_index + 1}"
    perturbed_state = initial.state.copy()
    perturbed_state[index[f"L{phase_index + 1}"]] += delta_a
    perturbed = _initial_step(boundary, perturbed_state, initial.time_s, diode_state)
    after_base = _advance_forced(
        initial,
        initial.time_s + step_s,
        boundary,
        dead_mode.high_side_on,
        dead_mode.low_side_on,
        diode_state,
    )
    after_perturbed = _advance_forced(
        perturbed,
        initial.time_s + step_s,
        boundary,
        dead_mode.high_side_on,
        dead_mode.low_side_on,
        diode_state,
    )
    difference = float(
        after_perturbed.state[index[node]] - after_base.state[index[node]]
    )
    if difference == 0.0:
        return float("nan")
    return float(-delta_a * step_s / difference)


@dataclass
class PeriodResult:
    z_next: NDArray[np.float64]
    turn_on: list[TurnOnVerdict] = field(default_factory=list)
    turn_off: list[TurnOffVerdict] = field(default_factory=list)
    monitor: Monitor | None = None
    final_step: HybridStep | None = None
    #: The `HybridStep` entering each phase's own turn-on dead-time window, so a
    #: later script can re-verify that window independently at any sub-step.
    turn_on_entry: dict[int, HybridStep] = field(default_factory=dict)

    @property
    def natural_zvs_flags(self) -> tuple[bool, bool, bool, bool]:
        by_phase = {verdict.phase_index: verdict.natural_zvs for verdict in self.turn_on}
        return tuple(by_phase[phase] for phase in range(4))  # type: ignore[return-value]


def evaluate_period_map(
    boundary: ZeroStartBoundary,
    z: NDArray[np.float64],
    *,
    coarse_step_s: float = 62.5e-12,
    sub_step_s: float = 2e-12,
    diode_state: tuple[bool, bool, bool] = (False, False, False),
    t0: float | None = None,
) -> PeriodResult:
    """Propagate `z` forward exactly one PWM period.  This is `F`."""
    start_s = period_start_s(boundary) if t0 is None else t0
    names = variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    if np.asarray(z).shape != (len(names),):
        raise ValueError(f"state must have {len(names)} entries")
    monitor = Monitor(index=index)
    current = _initial_step(boundary, z, start_s, diode_state)
    monitor.observe(current)
    result = PeriodResult(z_next=np.empty(0))
    for interval in period_intervals(boundary, start_s):
        if interval.kind == "normal":
            current = _march(
                current, interval.end_s, coarse_step_s, boundary, diode_state, monitor
            )
        elif interval.kind == "turn_on":
            result.turn_on_entry[interval.phase_index] = current  # type: ignore[index]
            current, verdict = _resolve_turn_on(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_on.append(verdict)
        else:
            current, verdict = _resolve_turn_off(
                boundary,
                current,
                interval.phase_index,  # type: ignore[arg-type]
                interval.end_s,
                sub_step_s,
                diode_state,
                monitor,
            )
            result.turn_off.append(verdict)
    result.z_next = current.state.copy()
    result.monitor = monitor
    result.final_step = current
    result.turn_on.sort(key=lambda verdict: verdict.phase_index)
    result.turn_off.sort(key=lambda verdict: verdict.phase_index)
    return result


def relative_residual(z: NDArray[np.float64], z_next: NDArray[np.float64]) -> float:
    """`|F(z) - z|_inf` normalized by `max(|z|_inf, 1)` (project convention)."""
    return float(
        np.linalg.norm(z_next - z, ord=np.inf)
        / max(float(np.linalg.norm(z, ord=np.inf)), 1.0)
    )
