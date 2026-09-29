"""A65 (copy of A64) - post-processing of one LTspice run (raw file, double precision).

Everything here reads LTspice's own saved waveforms; nothing is re-simulated.

Per sample period k (quiet instant tau = QUIET_S + kT to the next one):
  E_in   = integral of V_src * I_src           (trapezoid on LTspice's points, as .meas INTEG)
  E_out  = integral of Vout^2 / R_load
  dE     = change of the energy stored in the LINEAR passives (divider caps,
           flying caps, Cout, source and phase inductors) between the two samples
  P_loss = (E_in - E_out) / T                  (BOUNDARY Section 4, source side)
  P_loss_corr = (E_in - E_out - dE) / T        (same, closed for any residual drift)

Convergence (BOUNDARY Section 3): the relative cycle-to-cycle change of every
capacitor voltage (divider, flying, output, and the eight switch-branch
voltages that carry the vendor Coss) and every inductor current, at the quiet
samples. Relative to max(|value|, floor), floors 0.1 V / 1 A (PROJECT_DECISION:
switch branches that are ON sit at I*Ron ~ tens of mV).

Last-period extras: gate-drive energy per device group (device A times the
group count; parallel devices share nodes and drive and are identical by
symmetry -- checked once with every device saved), per-switch-group
integral of Vds*Id, passive resistive loss, and per-edge channel timing.
"""
from __future__ import annotations

import numpy as np

import a65_netlist as A

VOLT_FLOOR = 0.1
AMP_FLOOR = 1.0
#: incoming switch "has reached ~0 V": branch voltage <= this (PROJECT_DECISION)
VDS_ZERO_V = 0.5
#: reverse (third-quadrant, channel off) conduction: branch voltage below this
VDS_REVERSE_V = -0.5


def vth_knee(temp_c: float) -> float:
    """Vendor model's channel knee k2(T) = 2.115*(1 - 8e-4*(T-25)) V.

    At Vgs = k2 the model's channel conductance is ln2/32 ~ 2 % of its 5 V
    value. Used as the channel on/off instant (PROJECT_DECISION).
    """
    return 2.115 * (1 - 8.0e-4 * (temp_c - 25.0))


def interp(t: np.ndarray, y: np.ndarray, at: float) -> float:
    i = int(np.searchsorted(t, at))
    if i <= 0:
        return float(y[0])
    if i >= len(t):
        return float(y[-1])
    t0, t1 = t[i - 1], t[i]
    if t1 == t0:
        return float(y[i])
    w = (at - t0) / (t1 - t0)
    return float(y[i - 1] * (1 - w) + y[i] * w)


def integrate(t: np.ndarray, y: np.ndarray, t1: float, t2: float) -> float:
    """Trapezoid of y over [t1, t2] on the solver's points, with interpolated ends."""
    i1 = int(np.searchsorted(t, t1, side="right"))
    i2 = int(np.searchsorted(t, t2, side="left"))
    tt = np.concatenate([[t1], t[i1:i2], [t2]])
    yy = np.concatenate([[interp(t, y, t1)], y[i1:i2], [interp(t, y, t2)]])
    return float(np.sum(0.5 * (yy[1:] + yy[:-1]) * np.diff(tt)))


def state_at(d: dict, at: float) -> dict:
    t = d["time"]
    out = {name: interp(t, d[f"V({name})"], at) for name in A.NODE_STATES}
    for name, element in A.INDUCTOR_STATES.items():
        out[name] = interp(t, d[f"I({element})"], at)
    return out


def derived(s: dict) -> dict:
    """Capacitor voltages and inductor currents that define the state."""
    return {
        "vdiv4": s["vin"] - s["tap3"], "vdiv3": s["tap3"] - s["tap2"],
        "vdiv2": s["tap2"] - s["tap1"], "vdiv1": s["tap1"],
        "vc1": s["a1"] - s["x1"], "vc2": s["a2"] - s["x2"], "vc3": s["a3"] - s["x3"],
        "vout": s["out"],
        "vsh1": s["vin"] - s["a1"], "vsh2": s["a1"] - s["a2"], "vsh3": s["a2"] - s["a3"],
        "vsh4": s["a3"] - s["x4"],
        "vsl1": s["x1"], "vsl2": s["x2"], "vsl3": s["x3"], "vsl4": s["x4"],
        "i_lsrc": s["LPAR_IN"], "i_l1": s["L1"], "i_l2": s["L2"], "i_l3": s["L3"], "i_l4": s["L4"],
    }


def stored_energy(s: dict, b: dict) -> float:
    """Energy in the linear passives (J). Vendor Coss energy is not included."""
    q = derived(s)
    cdiv = b["divider_capacitance_f"]
    e = 0.5 * cdiv * sum(q[k] ** 2 for k in ("vdiv1", "vdiv2", "vdiv3", "vdiv4"))
    e += 0.5 * sum(c * q[k] ** 2 for c, k in zip(b["flying_capacitances_f"], ("vc1", "vc2", "vc3")))
    e += 0.5 * b["output_capacitance_f"] * q["vout"] ** 2
    e += 0.5 * b["source_inductance_h"] * q["i_lsrc"] ** 2
    e += 0.5 * b["phase_inductance_h"] * sum(q[f"i_l{k}"] ** 2 for k in range(1, 5))
    return float(e)


def relative_change(prev: dict, cur: dict) -> tuple[float, str]:
    a, b = derived(prev), derived(cur)
    worst, which = 0.0, ""
    for key in a:
        floor = AMP_FLOOR if key.startswith("i_") else VOLT_FLOOR
        rel = abs(b[key] - a[key]) / max(abs(b[key]), abs(a[key]), floor)
        if rel > worst:
            worst, which = rel, key
    return worst, which


def crossings(t, y, level, t_from, t_to, direction):
    """Times (linear interpolation) where y crosses level in [t_from, t_to]."""
    i1 = max(int(np.searchsorted(t, t_from)) - 1, 0)
    i2 = min(int(np.searchsorted(t, t_to)) + 1, len(t))
    tt, yy = t[i1:i2], y[i1:i2] - level
    if direction > 0:
        idx = np.nonzero((yy[:-1] < 0) & (yy[1:] >= 0))[0]
    else:
        idx = np.nonzero((yy[:-1] > 0) & (yy[1:] <= 0))[0]
    out = []
    for i in idx:
        tc = tt[i] - yy[i] * (tt[i + 1] - tt[i]) / (yy[i + 1] - yy[i])
        if t_from <= tc <= t_to:
            out.append(float(tc))
    return out


def branch_v(d: dict, side: str, phase: int) -> np.ndarray:
    drain, source = (A.HIGH_BRANCHES if side == "high" else A.LOW_BRANCHES)[phase - 1]
    v = d[f"V({drain})"]
    return v - d[f"V({source})"] if source != "0" else v


def gate_vgs(d: dict, side: str, phase: int) -> np.ndarray:
    n = f"x{side[0]}{phase}a"
    return d[f"V({n}:gate)"] - d[f"V({n}:source)"]


def analyze(d: dict, meta: dict, a59: dict) -> dict:
    b = a59["boundary"]
    T = A.PERIOD_S
    t = d["time"]
    samples = meta["sample_times_s"]
    rload = meta["rload_ohm"]
    states = [state_at(d, s) for s in samples]
    vsrc = b["vin_target_v"]
    p_in_inst = -vsrc * d["I(V_SRC)"]
    p_out_inst = d["V(out)"] ** 2 / rload
    periods = []
    for k in range(1, len(samples)):
        t1, t2 = samples[k - 1], samples[k]
        e_in = integrate(t, p_in_inst, t1, t2)
        e_out = integrate(t, p_out_inst, t1, t2)
        de = stored_energy(states[k], b) - stored_energy(states[k - 1], b)
        rel, which = relative_change(states[k - 1], states[k])
        i_sum = integrate(t, sum(d[f"I(LIND{j})"] for j in range(1, 5)), t1, t2) / T
        v_out = integrate(t, d["V(out)"], t1, t2) / T
        periods.append({
            "k": k, "t_from_s": t1, "t_to_s": t2,
            "p_in_w": e_in / T, "p_out_w": e_out / T,
            "p_loss_w": (e_in - e_out) / T, "stored_energy_rate_w": de / T,
            "p_loss_corr_w": (e_in - e_out - de) / T,
            "rel_change": rel, "rel_change_worst": which,
            "i_lsum_mean_a": i_sum, "vout_mean_v": v_out,
            # net mean current into Cout: 0 on a periodic orbit (regulation residual)
            "cout_net_current_a": i_sum - integrate(t, d["V(out)"] / rload, t1, t2) / T,
            "max_abs_phase_current_a": float(max(np.max(np.abs(d[f"I(LIND{j})"][(t >= t1) & (t <= t2)]))
                                                 for j in range(1, 5))),
        })
    t1, t2 = samples[-2], samples[-1]
    last = {"t_from_s": t1, "t_to_s": t2}
    # passive resistive loss (source R, inductor Rser); divider leakage (1 GOhm) is < 1 uW
    last["p_rsrc_w"] = integrate(t, d["I(V_SRC)"] ** 2 * b["source_resistance_ohm"], t1, t2) / T
    last["p_rlind_w"] = sum(integrate(t, d[f"I(LIND{k})"] ** 2 * b["phase_inductor_resistance_ohm"],
                                      t1, t2) for k in range(1, 5)) / T
    # switch-group Vds*Id (drain/source terminals) -- sums with passives to P_in - P_out
    groups = {}
    for side, count in (("high", A.NHS), ("low", A.NLS)):
        for p in range(1, 5):
            vds = branch_v(d, side, p)
            idr = d[f"I(V_A{side[0].upper()}{p})"]
            groups[f"{side[0]}{p}"] = integrate(t, vds * idr, t1, t2) / T
    last["p_switch_groups_w"] = groups
    last["p_switch_sum_w"] = sum(groups.values())
    # gate drive: energy delivered by each PULSE source (device A x group count)
    gate = {}
    for side, count in (("high", A.NHS), ("low", A.NLS)):
        for p in range(1, 5):
            name = f"{side[0].upper()}{p}A"
            src = (A.HIGH_BRANCHES if side == "high" else A.LOW_BRANCHES)[p - 1][1]
            vcmd = d[f"V(c{name.lower()})"] - (d[f"V({src})"] if src != "0" else 0.0)
            e = integrate(t, -vcmd * d[f"I(V_G{name})"], t1, t2)
            gate[f"{side[0]}{p}"] = {"per_device_j": e, "devices": count, "group_w": e * count / T}
    last["gate"] = gate
    last["p_gate_total_w"] = sum(v["group_w"] for v in gate.values())
    last["edges"] = edge_timing(d, meta, a59)
    last["decomposition"] = decompose(d, meta, last)
    last["state_decomposition"] = decompose_states(d, meta)
    return {"periods": periods, "samples": [dict(zip(s.keys(), s.values())) for s in states],
            "last": last}


def decompose(d: dict, meta: dict, last: dict) -> dict:
    """Split each switch group's Vds*Id energy into full-gate conduction and edge excess.

    R_eff of a group = integral(Vds*Id)/integral(Id^2) over the middle half of
    its commanded ON interval (gate fully on). Edge excess = integral of
    (Vds*Id - R_eff*Id^2) over the edge window [outgoing command-off,
    incoming command-on + 5 ns], for the incoming and the outgoing group. It
    holds overlap, Coss, third-quadrant and under-driven-channel loss, plus
    the change of the two groups' Coss energy across the edge (which cancels
    between the rise and fall edge of a phase). P_conduction_equiv = sum over
    groups of R_eff * integral(Id^2) over the period.
    """
    T = A.PERIOD_S
    t = d["time"]
    t_lo, t_hi = meta["sample_times_s"][-2], meta["sample_times_s"][-1]
    origin = meta["origin_s"]
    windows = A.gate_windows(meta["ton_cmd_s"], meta["dead_time_rise_s"], meta["dead_time_fall_s"], T)
    reff, cond = {}, {}
    for (side, p), (start, end) in windows.items():
        width = end - start
        s = start - origin
        while s < t_lo:
            s += T
        while s >= t_hi:
            s -= T
        a, b = s + 0.25 * width, s + 0.75 * width
        if b > t_hi:  # use the previous occurrence when the middle leaves the last period
            a, b = a - T, b - T
        vds = branch_v(d, side, p)
        idr = d[f"I(V_A{side[0].upper()}{p})"]
        key = f"{side[0]}{p}"
        reff[key] = integrate(t, vds * idr, a, b) / integrate(t, idr * idr, a, b)
        cond[key] = reff[key] * integrate(t, idr * idr, t_lo, t_hi) / T
    edge_excess = []
    for e in last["edges"]:
        p = e["phase"]
        w1, w2 = e["cmd_outgoing_off_s"], e["cmd_incoming_on_s"] + 5e-9
        row = {"phase": p, "edge": e["edge"]}
        for role, side in (("incoming", e["incoming"]),
                           ("outgoing", "low" if e["incoming"] == "high" else "high")):
            vds = branch_v(d, side, p)
            idr = d[f"I(V_A{side[0].upper()}{p})"]
            key = f"{side[0]}{p}"
            row[f"excess_{role}_j"] = integrate(t, vds * idr - reff[key] * idr * idr, w1, w2)
        row["excess_edge_j"] = row["excess_incoming_j"] + row["excess_outgoing_j"]
        edge_excess.append(row)
    p_edges = sum(r["excess_edge_j"] for r in edge_excess) / T
    by_edge = {k: sum(r["excess_edge_j"] for r in edge_excess if r["edge"] == k) / T for k in ("rise", "fall")}
    return {"r_eff_ohm": reff, "p_conduction_equiv_w": sum(cond.values()),
            "p_conduction_equiv_by_group_w": cond, "p_edge_excess_w": p_edges,
            "p_edge_excess_by_edge_type_w": by_edge, "edge_excess": edge_excess,
            "residual_w": last["p_switch_sum_w"] - sum(cond.values()) - p_edges}


def edge_timing(d: dict, meta: dict, a59: dict) -> list[dict]:
    """Command vs channel timing for the 8 edges of the last sample period."""
    T = A.PERIOD_S
    t = d["time"]
    samples = meta["sample_times_s"]
    t_lo, t_hi = samples[-2], samples[-1]
    origin = meta["origin_s"]
    ton, dr, df = meta["ton_cmd_s"], meta["dead_time_rise_s"], meta["dead_time_fall_s"]
    vth = vth_knee(meta["case"]["temp_c"])
    windows = A.gate_windows(ton, dr, df, T)
    out = []
    for p in range(1, 5):
        for edge in ("rise", "fall"):
            if edge == "rise":  # low off -> high on (the high-side ZVS edge)
                incoming, outgoing = "high", "low"
                t_in_cmd_tau = windows[("high", p)][0]
                t_out_cmd_tau = windows[("low", p)][1]
            else:               # high off -> low on (the low-side edge)
                incoming, outgoing = "low", "high"
                t_in_cmd_tau = windows[("low", p)][0]
                t_out_cmd_tau = windows[("high", p)][1]
            # place the edge inside the last sample period (netlist time)
            t_out_cmd = t_out_cmd_tau - origin
            while t_out_cmd < t_lo:
                t_out_cmd += T
            while t_out_cmd >= t_hi:
                t_out_cmd -= T
            t_in_cmd = t_out_cmd + ((t_in_cmd_tau - t_out_cmd_tau) % T)
            vgs_out = gate_vgs(d, outgoing, p)
            vgs_in = gate_vgs(d, incoming, p)
            vds_in = branch_v(d, incoming, p)
            vds_out = branch_v(d, outgoing, p)
            span_end = t_in_cmd + 8e-9
            off = crossings(t, vgs_out, vth, t_out_cmd, span_end, -1)
            on = crossings(t, vgs_in, vth, t_out_cmd, span_end, +1)
            t_off = off[0] if off else None
            t_on = on[0] if on else None
            zero = crossings(t, vds_in, VDS_ZERO_V, t_out_cmd, span_end, -1)
            t_zero = zero[0] if zero else None
            rec = {
                "phase": p, "edge": edge, "incoming": incoming,
                "cmd_outgoing_off_s": t_out_cmd, "cmd_incoming_on_s": t_in_cmd,
                "command_dead_time_s": t_in_cmd - t_out_cmd,
                "channel_off_s": t_off, "channel_on_s": t_on,
                "channel_dead_time_s": (t_on - t_off) if (t_on is not None and t_off is not None) else None,
                "turn_off_delay_s": (t_off - t_out_cmd) if t_off is not None else None,
                "turn_on_delay_s": (t_on - t_in_cmd) if t_on is not None else None,
                "vds_in_at_cmd_off_v": interp(t, vds_in, t_out_cmd),
                "vds_in_at_channel_on_v": interp(t, vds_in, t_on) if t_on is not None else None,
                "vds_in_reaches_0p5V_s": t_zero,
                "vds_in_zero_before_channel_on": (t_zero is not None and t_on is not None and t_zero <= t_on),
                "vds_in_min_v": float(np.min(vds_in[(t >= t_out_cmd) & (t <= span_end)])),
                "vds_out_max_v": float(np.max(vds_out[(t >= t_out_cmd) & (t <= span_end)])),
            }
            # third-quadrant (reverse) conduction of the incoming switch before its channel is on
            if t_on is not None:
                mask = (t >= t_out_cmd) & (t <= t_on)
                tt = t[mask]
                rev = vds_in[mask] < VDS_REVERSE_V
                rec["reverse_before_on_s"] = float(np.sum(np.diff(tt)[rev[:-1]])) if len(tt) > 1 else 0.0
            # hard-switching energy: incoming group Vds*Id from its channel-on to Vds <= 0.5 V
            idr_in = d[f"I(V_A{incoming[0].upper()}{p})"]
            idr_out = d[f"I(V_A{outgoing[0].upper()}{p})"]
            if t_on is not None:
                end_hard = t_zero if (t_zero is not None and t_zero > t_on) else t_on
                rec["hard_window_s"] = end_hard - t_on
                rec["hard_energy_incoming_j"] = integrate(t, vds_in * idr_in, t_on, end_hard) if end_hard > t_on else 0.0
            # full edge window: outgoing command-off to incoming command-on + 5 ns
            w1, w2 = t_out_cmd, t_in_cmd + 5e-9
            rec["edge_window_energy_incoming_j"] = integrate(t, vds_in * idr_in, w1, w2)
            rec["edge_window_energy_outgoing_j"] = integrate(t, vds_out * idr_out, w1, w2)
            rec["inductor_current_at_cmd_off_a"] = interp(t, d[f"I(LIND{p})"], t_out_cmd)
            out.append(rec)
    return out


_COSS = {}


def coss_table():
    """(V grid, C per device) of the vendor model at Vgs = 0, or None if not measured yet."""
    if "table" not in _COSS:
        path = A.HERE / "runs" / "static_epc2067_coss.json"
        if path.exists():
            import json  # noqa: PLC0415
            rec = json.loads(path.read_text())
            _COSS["table"] = (np.array(rec["v_grid_v"]), np.array(rec["c_per_device_f"]))
        else:
            return None
    return _COSS["table"]


#: gate-state thresholds for the loss decomposition (PROJECT_DECISION)
V_FULL_GATE = 4.5          # internal Vgs >= this: channel fully enhanced
K3 = 0.09                  # vendor model softplus width (k3)
OVERLAP_V = 1.0            # |Vds| > this during a gate transition: V*I overlap
R_A59_DEVICE_OHM = 1.55e-3


def decompose_states(d: dict, meta: dict) -> dict:
    """Split every switch group's terminal energy (Vds*Id) by gate state.

    For each group (representative device A's INTERNAL Vgs, the branch Vds and
    the group's metered drain current), every instant of the last period is
    put in exactly one class:

      third_quadrant       Vds < -0.5 V and Vgs < k2(T): reverse conduction
                           with the channel off (the "body-diode" path)
      conduction           Vgs >= 4.5 V: channel fully enhanced
      turn_on / turn_off   k2 - 3*k3 <= Vgs < 4.5 V, gate commanded ON / OFF
                           (rising / falling gate), each split into
                             *_overlap      |Vds| > 1 V   (V*I overlap)
                             *_underdriven  |Vds| <= 1 V  (conducting at
                                             partial enhancement)
      off_state            Vgs < k2 - 3*k3 (channel off, Vds >= -0.5 V):
                           terminal energy into the device's own Coss; over a
                           period it is the own-Coss energy that a hard
                           turn-on later dissipates inside the device (zero
                           for a loss-free charge/discharge)

    The classes sum exactly to the group's integral of Vds*Id. Also returned:
    the vendor full-gate resistance per device (from the conduction class),
    and the A59-style conduction sum((1.55 mOhm/n) * Id^2) over each group's
    commanded ON time -- what A59's ideal-switch channel meter would read on
    these same currents.
    """
    T = A.PERIOD_S
    t = d["time"]
    t_lo, t_hi = meta["sample_times_s"][-2], meta["sample_times_s"][-1]
    origin = meta["origin_s"]
    temp = meta["case"]["temp_c"]
    k2 = vth_knee(temp)
    v_start = k2 - 3 * K3
    windows = A.gate_windows(meta["ton_cmd_s"], meta["dead_time_rise_s"], meta["dead_time_fall_s"], T)
    classes = ("conduction", "turn_on_overlap", "turn_on_underdriven", "turn_off_overlap",
               "turn_off_underdriven", "third_quadrant", "off_state")
    coss = coss_table()
    groups, totals = {}, {c: 0.0 for c in classes}
    totals_d = {c: 0.0 for c in classes}
    a59_style = 0.0
    for (side, p), (start, end) in windows.items():
        n = A.NHS if side == "high" else A.NLS
        vds = branch_v(d, side, p)
        idr = d[f"I(V_A{side[0].upper()}{p})"]
        vgs = gate_vgs(d, side, p)
        cmd_on = ((t + origin - start) % T) < (end - start)
        pw = vds * idr
        # dissipative power: terminal power minus the rate of change of the
        # group's own Coss energy, n * Vds * Coss(Vds) * dVds/dt (vendor-model
        # Coss(V) measured by `run_a65.py --stages coss`). Integrates to the
        # same total over a period; moves the reactive Coss energy out of the
        # turn-off / off-state classes.
        if coss is not None:
            c_of_v = np.interp(np.clip(vds, 0.0, coss[0][-1]), coss[0], coss[1])
            pd = vds * (idr - n * c_of_v * np.gradient(vds, t))
        else:
            pd = None
        rev = (vds < VDS_REVERSE_V) & (vgs < k2)
        full = (vgs >= V_FULL_GATE) & ~rev
        part = (vgs >= v_start) & (vgs < V_FULL_GATE) & ~rev
        off = (vgs < v_start) & ~rev
        ovl = np.abs(vds) > OVERLAP_V
        masks = {
            "conduction": full,
            "turn_on_overlap": part & cmd_on & ovl, "turn_on_underdriven": part & cmd_on & ~ovl,
            "turn_off_overlap": part & ~cmd_on & ovl, "turn_off_underdriven": part & ~cmd_on & ~ovl,
            "third_quadrant": rev, "off_state": off,
        }
        g = {c: integrate(t, pw * m, t_lo, t_hi) / T for c, m in masks.items()}
        if pd is not None:
            g["dissipative_w"] = {c: integrate(t, pd * m, t_lo, t_hi) / T for c, m in masks.items()}
            for c in classes:
                totals_d[c] += g["dissipative_w"][c]
        i2_full = integrate(t, idr * idr * full, t_lo, t_hi)
        g["r_full_gate_per_device_ohm"] = (n * integrate(t, pw * full, t_lo, t_hi) / i2_full
                                           if i2_full > 0 else None)
        g["a59_style_conduction_w"] = integrate(t, (R_A59_DEVICE_OHM / n) * idr * idr * cmd_on, t_lo, t_hi) / T
        # same, but over the time the vendor channel actually conducts (Vgs >= k2,
        # not third quadrant): same currents, same conduction intervals, ideal R
        ch_on = (vgs >= k2) & ~rev
        g["a59_style_conduction_channel_on_w"] = integrate(t, (R_A59_DEVICE_OHM / n) * idr * idr * ch_on,
                                                           t_lo, t_hi) / T
        g["vendor_channel_on_w"] = integrate(t, pw * ch_on, t_lo, t_hi) / T
        if pd is not None:
            g["vendor_channel_on_dissipative_w"] = integrate(t, pd * ch_on, t_lo, t_hi) / T
        g["third_quadrant_time_s"] = integrate(t, rev.astype(float), t_lo, t_hi)
        groups[f"{side[0]}{p}"] = g
        for c in classes:
            totals[c] += g[c]
        a59_style += g["a59_style_conduction_w"]
    by_side = {s: {c: sum(groups[f"{s[0]}{p}"][c] for p in range(1, 5)) for c in classes}
               for s in ("high", "low")}
    by_side_d = ({s: {c: sum(groups[f"{s[0]}{p}"]["dissipative_w"][c] for p in range(1, 5)) for c in classes}
                  for s in ("high", "low")} if coss is not None else None)
    return {"thresholds": {"v_full_gate_v": V_FULL_GATE, "v_channel_start_v": v_start, "k2_v": k2,
                           "overlap_v": OVERLAP_V, "reverse_v": VDS_REVERSE_V},
            "coss_corrected": coss is not None,
            "dissipative_totals_w": totals_d if coss is not None else None,
            "dissipative_sum_w": sum(totals_d.values()) if coss is not None else None,
            "dissipative_by_side_w": by_side_d,
            "totals_w": totals, "sum_w": sum(totals.values()), "by_side_w": by_side,
            "groups": groups, "a59_style_conduction_w": a59_style,
            "a59_style_conduction_channel_on_w": sum(g["a59_style_conduction_channel_on_w"] for g in groups.values()),
            "vendor_conduction_like_w": (totals["conduction"] + totals["turn_on_underdriven"]
                                         + totals["turn_off_underdriven"])}


def channel_summary(edges: list[dict]) -> dict:
    """Mean / min / max channel dead time and delays per edge type over the 4 phases."""
    out = {}
    for edge in ("rise", "fall"):
        rows = [e for e in edges if e["edge"] == edge]
        cdt = [e["channel_dead_time_s"] for e in rows if e["channel_dead_time_s"] is not None]
        out[edge] = {
            "channel_dead_time_mean_s": float(np.mean(cdt)) if len(cdt) == len(rows) else None,
            "channel_dead_time_min_s": float(np.min(cdt)) if cdt else None,
            "channel_dead_time_max_s": float(np.max(cdt)) if cdt else None,
            "turn_off_delay_mean_s": float(np.mean([e["turn_off_delay_s"] for e in rows
                                                    if e["turn_off_delay_s"] is not None])),
            "turn_on_delay_mean_s": float(np.mean([e["turn_on_delay_s"] for e in rows
                                                   if e["turn_on_delay_s"] is not None])),
            "vds_in_at_channel_on_v": [e["vds_in_at_channel_on_v"] for e in rows],
            "zvs_count": int(sum(bool(e["vds_in_zero_before_channel_on"]) for e in rows)),
        }
    return out


__all__ = ["analyze", "state_at", "derived", "stored_energy", "relative_change", "vth_knee",
           "integrate", "interp", "edge_timing", "channel_summary"]
