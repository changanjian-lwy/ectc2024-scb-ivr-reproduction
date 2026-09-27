"""A56 accepted-orbit diagnostics for BOUNDARY.md S3.4 (capacitive accounting).

Nothing here replaces A55's meter. ``accepted_orbit`` repeats the first lines
of A55 ``audit_accepted_orbit.metered_orbit`` (same FullStateMonitor injection,
same rollback of provisional samples) only because ``metered_orbit`` does not
return the accepted samples. ``channel_power_w`` recomputes A55's number from
those samples; the driver asserts equality with ``metered_orbit`` before any
diagnostic is reported.

Three independent views of a hard-switched turn-on:

1. ``event_window_energy``: re-integrate the post-event interval from the
   orbit's own window-end state with A50's unchanged backward-Euler step
   (``advance_fixed_diode_step``, commanded mode) at step ``h``, metering every
   enabled channel exactly as A55 does (right endpoint, v^2/R). At the orbit's
   own coarse step this reproduces the orbit's metered energy; at h << Ron*C
   it converges to the physical dissipation.
2. ``capacitance_from_transient``: charge through the switching branch in
   excess of its (linearly fitted) conduction current, divided by Vres.
3. ``energy_balance``: the exact discrete energy identity of backward Euler,
   ``sum h (P_src - P_diss) = W_end - W_start + sum 1/2 dz^T E dz``. The last
   term is energy removed by the integrator without passing through any
   metered resistor. It is localized to the post-event windows.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import regulated_boundary as R

NO_DIODES = (False, False, False)
#: Post-event window: 8 x 62.5 ps. ~50-70 discharge time constants, and
#: >= 10 ns away from any other commanded edge for every A56 Ton_cmd.
EVENT_WINDOW_S = 500e-12
#: Local step ladder (all divide 500 ps exactly).
STEP_LADDER_S = (62.5e-12, 31.25e-12, 15.625e-12, 7.8125e-12, 1.25e-12, 0.25e-12,
                 0.05e-12, 0.025e-12)
#: Conduction baseline fitted where t - t_e >= 250 ps (>= 25 time constants).
FIT_START_S = 250e-12


def accepted_orbit(boundary, z, *, coarse_step_s: float, sub_step_s: float):
    P = R.A.P
    original = P.PathResolvedMonitor
    P.PathResolvedMonitor = R.A.FullStateMonitor
    try:
        with R.asymmetric_ron_context():
            result, _, _ = P.evaluate_period_map_with_paths(
                boundary, np.asarray(z, dtype=float),
                coarse_step_s=coarse_step_s, sub_step_s=sub_step_s)
    finally:
        P.PathResolvedMonitor = original
    return result, result.monitor.accepted, result.monitor.index


def _branch_voltage(state, index, pair):
    first, second = pair
    return float(state[index[first]]) - (float(state[index[second]]) if second else 0.0)


def enabled_channel_power_w(boundary, state, mode, index) -> float:
    total = 0.0
    for enabled, pair in zip(mode.high_side_on, R.D.HIGH_SIDE_BRANCHES):
        if enabled:
            total += _branch_voltage(state, index, pair) ** 2 / boundary.high_side_on_resistance_ohm
    for enabled, pair in zip(mode.low_side_on, R.D.LOW_SIDE_BRANCHES):
        if enabled:
            total += _branch_voltage(state, index, pair) ** 2 / boundary.low_side_on_resistance_ohm
    return total


def channel_power_w(boundary, steps, index) -> float:
    energy = 0.0
    for previous, step in zip(steps, steps[1:]):
        energy += (step.time_s - previous.time_s) * enabled_channel_power_w(
            boundary, step.state, step.mode, index)
    return energy / boundary.period_s


@dataclass(frozen=True)
class HardEvent:
    side: str  # "high" | "low"
    phase_index: int
    window_end_s: float  # wrapped into [t0, t0 + T)
    residual_v: float
    sample_position: int
    branch: tuple
    resistance_ohm: float
    window_entry_position: int


def hard_events(boundary, result, steps) -> list[HardEvent]:
    times = np.array([s.time_s for s in steps])
    t0, period = times[0], boundary.period_s

    def position(t):
        if t >= t0 + period - 1e-18:
            t -= period
        k = int(np.argmin(np.abs(times - t)))
        if abs(times[k] - t) > 1e-18:
            raise RuntimeError("no accepted sample at the event instant")
        return t, k

    events = []
    for verdict in result.turn_on:
        if not verdict.natural_zvs:
            t, k = position(verdict.window_end_s)
            _, entry = position(verdict.window_start_s)
            p = verdict.phase_index
            events.append(HardEvent("high", p, t, verdict.hard_switch_residual_v, k,
                                    R.D.HIGH_SIDE_BRANCHES[p], boundary.high_side_on_resistance_ohm,
                                    entry))
    for verdict in result.turn_off:
        if not verdict.natural:
            t, k = position(verdict.window_end_s)
            _, entry = position(verdict.window_start_s)
            p = verdict.phase_index
            events.append(HardEvent("low", p, t, verdict.hard_switch_residual_v, k,
                                    R.D.LOW_SIDE_BRANCHES[p], boundary.low_side_on_resistance_ohm,
                                    entry))
    return events


def orbit_window_energy_j(boundary, steps, index, event: HardEvent) -> float:
    end = event.window_end_s + EVENT_WINDOW_S
    energy = 0.0
    k = event.sample_position
    while k + 1 < len(steps) and steps[k + 1].time_s <= end + 1e-18:
        energy += (steps[k + 1].time_s - steps[k].time_s) * enabled_channel_power_w(
            boundary, steps[k + 1].state, steps[k + 1].mode, index)
        k += 1
    if abs(steps[k].time_s - end) > 1e-18:
        raise RuntimeError("orbit samples do not reach the end of the event window")
    return energy


def event_window_energy(boundary, state, t_e, h, index, branch, resistance, *, keep=False):
    n = int(round(EVENT_WINDOW_S / h))
    if abs(n * h - EVENT_WINDOW_S) > 1e-18:
        raise ValueError("step must divide the event window")
    with R.asymmetric_ron_context():
        current = R.M._initial_step(boundary, state, t_e, NO_DIODES)
        energy = 0.0
        times, powers, branch_current = [], [], []
        for i in range(n):
            nxt = t_e + (i + 1) * h
            current = R.H.advance_fixed_diode_step(current, nxt, boundary, NO_DIODES)
            p = enabled_channel_power_w(boundary, current.state, current.mode, index)
            energy += h * p
            if keep:
                times.append(nxt - t_e)
                powers.append(p)
                branch_current.append(_branch_voltage(current.state, index, branch) / resistance)
    out = dict(step_s=h, steps=n, energy_j=energy)
    if keep:
        out.update(times=np.array(times), powers=np.array(powers),
                   branch_current=np.array(branch_current))
    return out


def conduction_fit(times, values):
    mask = times >= FIT_START_S
    slope, intercept = np.polyfit(times[mask], values[mask], 1)
    residual = values[mask] - (slope * times[mask] + intercept)
    return float(slope), float(intercept), float(np.sqrt(np.mean(residual ** 2)))


def structural_capacitance_f(boundary, event: HardEvent) -> float:
    ch = boundary.switch_capacitance.high_total_f
    cl = boundary.switch_capacitance.low_total_f
    # Phases 1-3: the ladder node carries two high-side switches (A50 S3.1).
    return ch + cl + (ch if event.phase_index < 3 else 0.0)


def energy_balance(boundary, steps, index, windows=()) -> dict:
    """Exact backward-Euler energy identity over the accepted orbit."""
    period = boundary.period_s
    names = R.M.variable_names(boundary)
    src, cur = names.index("src"), names.index("I_VSTEP")
    out = names.index("out")
    with R.asymmetric_ron_context():
        e = R.M.assemble_descriptor(boundary, steps[0].mode, steps[0].time_s).e
        totals = dict(source=0.0, dissipation=0.0, channel=0.0, load=0.0, numerical=0.0,
                      numerical_in_event_windows=0.0)
        for previous, step in zip(steps, steps[1:]):
            h = step.time_s - previous.time_s
            system = R.M.assemble_descriptor(boundary, step.mode, step.time_s)
            z1, dz = step.state, step.state - previous.state
            source_v = system.rhs[cur]
            p_src = -source_v * z1[cur]
            p_diss = float(z1 @ system.a @ z1) - 2.0 * z1[src] * z1[cur]
            numerical = 0.5 * float(dz @ e @ dz)
            totals["source"] += h * p_src
            totals["dissipation"] += h * p_diss
            totals["channel"] += h * enabled_channel_power_w(boundary, z1, step.mode, index)
            totals["load"] += h * z1[out] ** 2 / boundary.load_resistance_ohm
            totals["numerical"] += numerical
            if any(start < step.time_s <= end + 1e-18 for start, end in windows):
                totals["numerical_in_event_windows"] += numerical
        stored_change = 0.5 * float(steps[-1].state @ e @ steps[-1].state) - 0.5 * float(
            steps[0].state @ e @ steps[0].state)
    w = {k: v / period for k, v in totals.items()}
    w["other_resistive"] = w["dissipation"] - w["channel"] - w["load"]
    w["stored_energy_change_per_period"] = stored_change / period
    w["identity_residual"] = (w["source"] - w["dissipation"] - w["numerical"]
                              - w["stored_energy_change_per_period"])
    w["numerical_outside_event_windows"] = w["numerical"] - w["numerical_in_event_windows"]
    return {f"{k}_w": v for k, v in w.items()}


def dead_time_surrogate_exposure(boundary, result, steps, index) -> dict:
    """Current-time conducted by the ideal-clamp surrogate inside commanded
    dead-time windows (natural admissions only). Exported so a sourced
    reverse-conduction model can be inserted later; NOT a loss estimate."""
    intervals = []
    for v in result.turn_on:
        if v.natural_zvs:
            intervals.append(("high", v.phase_index, v.switch_on_time_s, v.window_end_s,
                              R.D.HIGH_SIDE_BRANCHES[v.phase_index],
                              boundary.high_side_on_resistance_ohm))
    for v in result.turn_off:
        if v.natural:
            intervals.append(("low", v.phase_index, v.switch_on_time_s, v.window_end_s,
                              R.D.LOW_SIDE_BRANCHES[v.phase_index],
                              boundary.low_side_on_resistance_ohm))
    t0, period = steps[0].time_s, boundary.period_s
    records, abs_charge, i2t = [], 0.0, 0.0
    for side, phase, start, end, pair, resistance in intervals:
        if start >= t0 + period - 1e-18:
            start, end = start - period, end - period
        q = s2 = duration = 0.0
        for previous, step in zip(steps, steps[1:]):
            if start < step.time_s <= end + 1e-18:
                dt = step.time_s - previous.time_s
                i = _branch_voltage(step.state, index, pair) / resistance
                q += dt * abs(i)
                s2 += dt * i * i
                duration += dt
        records.append(dict(side=side, phase_index=phase, admitted_duration_s=duration,
                            abs_charge_c=q, i2_dt_a2s=s2))
        abs_charge += q
        i2t += s2
    return dict(events=records, mean_abs_current_time_per_second_a=abs_charge / period,
                note="loss for a constant reverse drop Vsd would be ~Vsd * this value minus "
                     "the channel loss already metered in these intervals; no Vsd is assumed")
