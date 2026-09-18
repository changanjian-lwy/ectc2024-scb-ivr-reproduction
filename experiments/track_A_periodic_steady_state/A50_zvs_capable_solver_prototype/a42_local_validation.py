"""A50 gate 2 - the closest in-framework analog of A42's local ZVS threshold.

See `RESULTS.md` for the full discussion.  Summary of the construction and of
what does and does not match A42's own circuit:

A42's local netlist (`.../A42_.../fine_cases/a42_fine_777bp_zero_snubber.cir`)
is a deliberately ISOLATED single-phase commutation cell::

    vin(48 V hard) --SH1--+--CH1(385p)--+ a1 --CF1(53.8u)-- x1 --CL1(770p)-- gnd
                                              x1 --SL1-- gnd
                                              x1 --L1(1.4666667n, Rser=1u)-- out(1 V hard)

This framework's descriptor is four-phase-only: its switch branches are the
series-capacitor ladder `vin-a1, a1-a2, a2-a3, a3-x4` (high) and `x1..x4-gnd`
(low).  There is therefore NO way to instantiate one isolated phase.  The four
candidate switching nodes are not equivalent, and the choice matters:

* Phase 1's switching node `x1` reaches `a1`, and `a1` carries BOTH `CH1`
  (`vin-a1`) and `CH2` (`a1-a2`).  With the 385 pF / 770 pF plug-in, `x1`
  therefore commutates 770 + 385 + 385 = 1540 pF, a 33% capacitance excess
  over A42's own 1155 pF.  Phases 2 and 3 are worse still.
* Phase 4's switching node `x4` is touched by exactly three elements: its own
  low-side capacitance `CL4` (`x4-gnd`, 770 pF), its own high-side capacitance
  `CH4` (`a3-x4`, 385 pF) and `L4` (`x4-out`).  Nothing else in the ladder
  connects to `x4`.  Holding phase 3's low side on pins `x3` at the ground
  reference, so `a3 = x3 + Vc3` becomes the hard node that `CH4` returns to --
  structurally identical to A42's `vin` behind `CH1` (A42's `a1` is itself
  pinned to `x1` by the same 53.8 uF flying capacitor used here).

**Phase 4 is therefore an exact capacitive analog of A42's cell: 385 pF to a
hard node plus 770 pF to ground, across a 1.4666667 nH phase inductor into a
1 V rail.**  This is not a coincidence of tuning; it is a property of where
phase 4 sits at the bottom of the ladder.

Better still, the commanded schedule produces this state by itself.  With
`dead_time_s = 10 ns`, `T = 200 ns`, `Ton = 16.6667 ns` and the unchanged `T/4`
phase shift, phase 4's turn-on dead-time window is `[145 ns, 155 ns)` modulo
`T`, and during that window the commanded state of phases 1, 2 and 3 is
LOW - LOW - LOW.  No state is forced by hand.

Residual differences from A42, all documented in `RESULTS.md`:

1. `switch_on_resistance_ohm` is a single global value in this framework, so
   A42's `RHS = 7 mOhm` / `RLS = 3.5 mOhm` split cannot be expressed.  Inside
   the dead-time window this is irrelevant -- both phase-4 switches are off --
   but it does change the pre-window current ramp, and phases 1-3's own
   low-side drops would otherwise move the `a3` reference.  The framework's own
   default `1 uOhm` is therefore used, and A42's `RLS` drop at the release
   instant is instead applied as an explicit initial condition on `V(x4)`,
   which is exactly where it enters A42's own commutation.
2. `out` is an ideal 1 V source in A42.  Here it is the 4.672 mF output node
   with the load made negligible, which holds it to sub-microvolt over the
   window.
3. The three idle phases' inductor currents ramp during the window; with a
   1 uOhm on-resistance their switch-node voltages move by under 20 uV, which
   is reported.

Nothing here writes to, or imports from, `src/scb_ivr/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from solver_copy.commutation_capacitance import CommutationCapacitance  # noqa: E402
from solver_copy.device_library import (  # noqa: E402
    GS61008T,
    P25_GS61008T_POPULATION,
    CapacitanceView,
)
from solver_copy.evidence import Evidence  # noqa: E402
from solver_copy.zero_start_descriptor import (  # noqa: E402
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

# ---------------------------------------------------------------------------
# A42's own published boundary, reused verbatim (see `../A42_.../BOUNDARY.md`).
# ---------------------------------------------------------------------------
IPEAK_P24_A = 125.0
LPHASE_H = 1.4666667e-9
LPHASE_RSER_OHM = 1e-6
VIN_V = 48.0
VOUT_V = 1.0
CFLY_A42_F = 53.8e-6
#: A42 `VC1_T2` / `VA1_T2` / `VX1_T2`, chained from R04D2A.
A42_VC1_T2_V = 36.0193959392
A42_VA1_T2_V = 36.0193862915
A42_VX1_T2_V = -9.6476751536e-6
#: The high-side blocking voltage the commutation has to remove.
A42_VDS_HIGH_AT_T2_V = VIN_V - A42_VA1_T2_V
#: A42's `RHS`/`RLS`, from `GS61008T_typical_params.lib` + P25 Table III.
A42_RHS_OHM = GS61008T.rds_on(P25_GS61008T_POPULATION.high_side_parallel)
A42_RLS_OHM = GS61008T.rds_on(P25_GS61008T_POPULATION.low_side_parallel)
#: `CH=385p`, `CL=770p` -- the GS61008T Co(tr) plug-in, 1 high / 2 low devices.
A42_SWITCH_CAPACITANCE = CommutationCapacitance(
    high_device_f=GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, P25_GS61008T_POPULATION.high_side_parallel
    ),
    low_device_f=GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, P25_GS61008T_POPULATION.low_side_parallel
    ),
    device_evidence=Evidence.EXTERNAL_DEVICE_DATA,
)
#: A42's own published outcome, the comparison target for gate 2.
A42_PUBLISHED = {
    "no_cross_fraction": 0.0776,
    "no_cross_minimum_vds_v": 13.924e-3,
    "cross_fraction": 0.0777,
    "cross_absolute_time_s": 16.6469e-9,
    "cross_release_time_s": 14.4918e-9,
    "cross_commutation_time_s": 2.1551e-9,
    "cross_current_at_zvs_a": -33.65e-3,
}

#: Phase 4 (zero-based index 3) -- see the module docstring for why.
TEST_PHASE_INDEX = 3
DEAD_TIME_S = 10e-9
#: First whole PWM period at or after the end of the 22.87 us input ramp, so
#: the descriptor's own affine/constant-Vin precondition holds.
BASE_PERIOD_INDEX = 115


def build_boundary(*, dead_time_s: float = DEAD_TIME_S) -> ZeroStartBoundary:
    return ZeroStartBoundary(
        vin_target_v=VIN_V,
        vout_target_v=VOUT_V,
        # A42's `out` is an ideal source; make the load current negligible so
        # the 4.672 mF output node is the closest available zero-impedance rail.
        module_power_w=1e-6,
        phase_inductance_h=LPHASE_H,
        phase_inductor_resistance_ohm=LPHASE_RSER_OHM,
        flying_capacitances_f=(CFLY_A42_F, CFLY_A42_F, CFLY_A42_F),
        divider_enabled=False,
        switch_on_resistance_ohm=1e-6,
        switch_off_resistance_ohm=1e12,
        dead_time_s=dead_time_s,
        switch_capacitance=A42_SWITCH_CAPACITANCE,
        evidence=Evidence.CROSS_PAPER_EXTENSION,
    )


def dead_time_window_start_s(boundary: ZeroStartBoundary) -> float:
    """Absolute time of phase 4's commanded turn-on dead-time window start."""
    period = boundary.period_s
    nominal_edge = TEST_PHASE_INDEX * period / boundary.phases
    return BASE_PERIOD_INDEX * period + nominal_edge - 0.5 * boundary.dead_time_s


def _state_vector(
    boundary: ZeroStartBoundary,
    time_s: float,
    values: dict[str, float],
) -> tuple[np.ndarray, tuple[str, ...]]:
    mode = commanded_pwm_mode(time_s, boundary)
    system = assemble_descriptor(boundary, mode, time_s)
    missing = set(system.variable_names) - set(values)
    extra = set(values) - set(system.variable_names)
    if missing or extra:
        raise ValueError(f"state mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    state = np.array([values[name] for name in system.variable_names], dtype=float)
    return state, system.variable_names


def _hybrid_step(
    boundary: ZeroStartBoundary, time_s: float, values: dict[str, float]
) -> HybridStep:
    state, _ = _state_vector(boundary, time_s, values)
    mode = commanded_pwm_mode(time_s, boundary)
    return HybridStep(
        time_s=time_s,
        state=state,
        mode=mode,
        diode_observation=diode_observation(state, boundary, mode),
        descriptor_residual_inf=0.0,
        descriptor_relative_backward_error=0.0,
    )


def release_state_values(
    *, negative_current_a: float, switch_node_v: float
) -> dict[str, float]:
    """A42's own `t2`-chained local state, mapped onto the phase-4 cell.

    The mapping is chosen so the commutation has to move exactly the charge
    A42's does.  In A42 the hard node is `vin` and the switching node `x1`
    drags `a1 = x1 + Vc1` with it, so ZVS means `x1 -> VIN - VC1_T2 =
    11.9806137085 V` whatever `x1` started at.  Here the hard node is
    `a3 = x3 + Vc3` and the switching node is `x4` itself, so the same
    statement is `V(a3) = 11.9806137085 V` and ZVS means `x4 -> V(a3)`.
    `V(x4)` then carries A42's own low-side conduction drop at the release
    instant, which shortens the required swing by exactly as much as it does
    in A42.  The three idle phases sit at zero current with their low sides
    conducting, which pins `x1 = x2 = x3 = 0`.
    """
    return {
        "src": VIN_V,
        "src_r": VIN_V,
        "vin": VIN_V,
        "a1": A42_VC1_T2_V,
        "a2": 2.0 * VIN_V / 4.0,
        "a3": A42_VDS_HIGH_AT_T2_V,
        "x1": 0.0,
        "x2": 0.0,
        "x3": 0.0,
        "x4": switch_node_v,
        "out": VOUT_V,
        "LPAR_IN": 0.0,
        "L1": 0.0,
        "L2": 0.0,
        "L3": 0.0,
        "L4": -negative_current_a,
        "I_VSTEP": 0.0,
    }


def build_case(
    *,
    negative_fraction: float,
    dead_time_s: float = DEAD_TIME_S,
    apply_a42_low_side_drop: bool = True,
) -> dict[str, object]:
    """Build the phase-4 dead-time commutation case at one negative-current target."""
    boundary = build_boundary(dead_time_s=dead_time_s)
    negative_current_a = negative_fraction * IPEAK_P24_A
    start_time_s = dead_time_window_start_s(boundary)
    switch_node_v = (
        negative_current_a * A42_RLS_OHM if apply_a42_low_side_drop else 0.0
    )
    values = release_state_values(
        negative_current_a=negative_current_a, switch_node_v=switch_node_v
    )
    initial = _hybrid_step(boundary, start_time_s, values)
    commanded = commanded_pwm_mode(start_time_s + 1e-13, boundary)
    return {
        "boundary": boundary,
        "negative_fraction": negative_fraction,
        "negative_current_a": negative_current_a,
        "release_switch_node_v": switch_node_v,
        "start_time_s": start_time_s,
        "initial": initial,
        "commanded_high_side_on": commanded.high_side_on,
        "commanded_low_side_on": commanded.low_side_on,
    }


def resolve_case(
    case: dict[str, object],
    *,
    sub_step_s: float = 50e-12,
    crossing_tolerance_v: float = 1e-3,
) -> dict[str, object]:
    boundary = case["boundary"]
    window = resolve_deadtime_window(
        boundary,
        case["initial"],
        phase_index=TEST_PHASE_INDEX,
        sub_step_s=sub_step_s,
        crossing_tolerance_v=crossing_tolerance_v,
    )
    system = assemble_descriptor(boundary, window.final.mode, window.final.time_s)
    index = {name: i for i, name in enumerate(system.variable_names)}
    reference_drift_v = max(
        abs(float(step.state[index["x3"]])) for step in window.steps
    )
    output_drift_v = max(
        abs(float(step.state[index["out"]]) - VOUT_V) for step in window.steps
    )
    return {
        "window": window,
        "sub_step_s": sub_step_s,
        "idle_phase_reference_drift_v": reference_drift_v,
        "output_rail_drift_v": output_drift_v,
    }


def ramp_to_release(
    *,
    negative_fraction: float,
    dead_time_s: float = DEAD_TIME_S,
    sub_step_s: float = 1e-12,
    iterations: int = 3,
) -> dict[str, object]:
    """Integrate the pre-window low-side ramp from `iL4 = 0` to `-INEG`.

    A42 releases the low side the instant `I(L1)` reaches `-INEG`.  Here the
    release instant is fixed by the commanded schedule, so the ramp START is
    solved for instead: the time `t0` such that `iL4(t_window) = -INEG`.
    """
    boundary = build_boundary(dead_time_s=dead_time_s)
    negative_current_a = negative_fraction * IPEAK_P24_A
    window_start_s = dead_time_window_start_s(boundary)
    ramp_s = negative_current_a * boundary.phase_inductance_h / VOUT_V
    history: list[dict[str, float]] = []
    final_current = float("nan")
    for _ in range(iterations):
        start_time_s = window_start_s - ramp_s
        values = release_state_values(
            negative_current_a=0.0, switch_node_v=0.0
        )
        step = _hybrid_step(boundary, start_time_s, values)
        commanded = commanded_pwm_mode(
            0.5 * (start_time_s + window_start_s), boundary
        )
        if commanded.high_side_on[TEST_PHASE_INDEX] or not commanded.low_side_on[
            TEST_PHASE_INDEX
        ]:
            raise RuntimeError("ramp interval is not a commanded low-side interval")
        system = assemble_descriptor(boundary, step.mode, step.time_s)
        index = {name: i for i, name in enumerate(system.variable_names)}
        time_s = start_time_s
        while time_s < window_start_s - 1e-21:
            next_time_s = min(time_s + sub_step_s, window_start_s)
            step = advance_fixed_diode_step(step, next_time_s, boundary, (False,) * 3)
            time_s = next_time_s
        final_current = float(step.state[index["L4"]])
        slope = -VOUT_V / boundary.phase_inductance_h
        history.append({"ramp_s": ramp_s, "current_a": final_current})
        ramp_s += (final_current + negative_current_a) / slope
    return {
        "boundary": boundary,
        "negative_fraction": negative_fraction,
        "negative_current_a": negative_current_a,
        "ramp_duration_s": history[-1]["ramp_s"],
        "current_at_window_start_a": final_current,
        "sub_step_s": sub_step_s,
        "iterations": history,
        "final_step": step,
        "window_start_s": window_start_s,
    }


def analytic_lossless_commutation(
    *, negative_current_a: float, switch_node_v: float
) -> dict[str, float]:
    """Closed-form isolated-LC reference for the same cell.

    Not a P25 equation: this is the general-physics resonant solution of the
    exact cell phase 4 realizes (`L` against `CH + CL` into a `Vout` rail),
    used only to separate the extension's physics from its time-discretization.
    """
    capacitance_f = (
        A42_SWITCH_CAPACITANCE.high_total_f + A42_SWITCH_CAPACITANCE.low_total_f
    )
    omega = 1.0 / np.sqrt(LPHASE_H * capacitance_f)
    offset = switch_node_v - VOUT_V
    velocity = abs(negative_current_a) * np.sqrt(LPHASE_H / capacitance_f)
    amplitude = float(np.hypot(offset, velocity))
    peak_switch_node_v = VOUT_V + amplitude
    target = A42_VDS_HIGH_AT_T2_V
    minimum_vds_v = target - peak_switch_node_v
    result = {
        "participating_capacitance_f": capacitance_f,
        "resonant_angular_frequency_rad_s": float(omega),
        "peak_switch_node_v": peak_switch_node_v,
        "minimum_vds_v": float(minimum_vds_v),
        "quarter_period_s": float(0.5 * np.pi / omega),
    }
    if minimum_vds_v <= 0.0:
        phase = float(np.arctan2(offset, velocity))
        wanted = (target - VOUT_V) / amplitude
        result["crossing_time_s"] = float(
            (np.arcsin(min(1.0, wanted)) - phase) / omega
        )
        # iL = -C dV(x4)/dt, and dV/dt = omega * sqrt(amplitude^2 - u^2).
        slope = omega * float(np.sqrt(max(0.0, amplitude**2 - (target - VOUT_V) ** 2)))
        result["phase_current_at_crossing_a"] = float(-capacitance_f * slope)
    else:
        result["crossing_time_s"] = float("nan")
        result["phase_current_at_crossing_a"] = float("nan")
    return result


def threshold_current_a(*, switch_node_v: float) -> float:
    """Exact lossless-LC negative current at which `Vds` just reaches zero."""
    capacitance_f = (
        A42_SWITCH_CAPACITANCE.high_total_f + A42_SWITCH_CAPACITANCE.low_total_f
    )
    target = A42_VDS_HIGH_AT_T2_V
    amplitude = target - VOUT_V
    offset = switch_node_v - VOUT_V
    velocity_squared = amplitude**2 - offset**2
    return float(np.sqrt(velocity_squared) / np.sqrt(LPHASE_H / capacitance_f))
