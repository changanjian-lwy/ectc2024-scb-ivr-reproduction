"""A199: open-loop replay of a co-simulation window in LTspice, EPC's model on all 20 switches at all times.

A record made with cfg "snap_us" and "debug_edges_us" holds, at each phase-1 high-side turn-off command inside the
window, the plant's full state (bridge Module.snapshot) and every gate command applied to the plant. replay(rec, k,
periods) starts LTspice from snapshot k, replays the commands over `periods` phase-1 periods (plus TAIL) and compares:
- the state at the following snapshots (node voltages, phase and loop currents);
- each high-side turn-off: the plant's physical peak (gate_offs_last) against the largest phase current around it;
- each low-side turn-off command: the phase current there (lowoffs_last), and LTspice's valley after it;
- each high-side turn-on: V_DS at the command and at the channel's start, and the start's instant (turnons_last);
- each switch's largest V_DS over the section intervals inside the window (sections' vds_win_v);
- the phase currents at every applied edge, and where the energy goes over the first period (_loss).

LTspice circuit = the plant's (circuit.py: four phases, a loop inductance with damping per high side, flying
capacitors, output capacitor, load) with n_high / n_low flattened vendor devices per switch. Each gate has its own
driver branch: gate_r_on to +5 V while the command is high, gate_r_off to the source while it is low (gate.py's
assumption), written as one behavioural current source (V_drive - v_gs) x conductance. (With LTspice switch
elements in the gate branches the time step collapses below 1 fs within 5-100 ns of these netlists.) An interlock
hold (the plant freezes the gate at its level, record "gate_holds_last") sets that conductance to zero for the
hold, so the gate floats; a record with holds but without that list is refused.
The plant's switches have no on-resistance; its per-phase R stands for it (duty-weighted maximum R_DS(on), D62). The
vendor devices bring their own (typical), so the phase resistance in LTspice is rph: "match" = R minus the devices'
duty-weighted typical value, "zero", or "plant" (R as in the plant, so the devices' resistance counts twice).
Time: LTspice t = plant t - t0 + T_REL; every node is held for T_REL (D79: charge-defined capacitances start
uncharged under uic) and the inductor currents are set back by what the hold adds.

    PYTHONPATH=src python3 scripts/p24_replay.py RECORD.json --k 0 1 2 [--periods 2] [--rph match] [--out FILE.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scb_ivr.cosim.circuit import CircuitParams  # noqa: E402
from scb_ivr.p24_gate_model import load_device  # noqa: E402

NODES = ("a1", "a2", "a3", "x1", "x2", "x3", "x4", "out", "h1", "h2", "h3", "h4")     # the plant's node order (loop on)
UP = ("vin", "a1", "a2", "a3")          # the node feeding high side k's loop inductance
SRC = ("a1", "a2", "a3", "x4")          # high side k's source
T_REL = 0.2e-9
TAIL = 30e-9
ACT_I = 0.01                             # A per device: the plant's start-of-channel level (gate.py)
K2 = "k2=2.115e+00"                      # the vendor model's threshold parameter as written in the library
L_IDEAL = "Rser=0 Rpar=1e15"             # LTspice gives every inductor 1 mOhm in series (and a parallel damper)
                                         # unless told otherwise; 1 mOhm is twice the plant's whole phase resistance
HOLD_RON = 1e-3                          # ohm, as in D79's edge netlists (LTspice does not start with 1e-5 or less);
                                         # a held node that carries I amps therefore sits I mV off until the release


def load(path):
    rec = json.loads(Path(path).read_text())
    if not rec.get("snaps") or not rec.get("edges_log"):
        raise ValueError("the record needs cfg snap_us and debug_edges_us")
    return rec


def window(rec, k, periods):
    s0 = rec["snaps"][k]
    return s0, s0["t_s"], rec["snaps"][k + periods]["t_s"] + TAIL


def duty(rec, t0, t1):
    """Mean high-side on-time over the mean phase-1 period inside the window (from the applied commands)."""
    on, tons = {}, []
    for e in rec["edges_log"]:
        if e["j"] < 4 and t0 - 2e-6 <= e["t_s"] <= t1:
            if e["level"]:
                on[e["j"]] = e["t_s"]
            elif e["j"] in on:
                tons.append(e["t_s"] - on.pop(e["j"]))
    ts = [s["t_s"] for s in rec["snaps"] if t0 - 1e-12 <= s["t_s"] <= t1]
    return float(np.mean(tons[-8:])) / float(np.mean(np.diff(ts)))


def rph_value(rec, t0, t1, mode):
    c = rec["snap_circuit"]
    if mode == "plant":
        return c["R"], None
    if mode == "zero":
        return 0.0, None
    d = duty(rec, t0, t1)
    r = load_device(temp=c["gate_temp"], dk2=c["gate_dk2"], cg_scale=c["gate_cg_scale"]).rds_on()
    r_dw = d * r / c["n_high"] + (1 - d) * r / c["n_low"]
    return c["R"] - r_dw, {"duty": d, "rds_on_ohm": r, "duty_weighted_ohm": r_dw}


def _pwl(points):
    out, last = [], -1.0
    for t, v in points:
        t = max(t, last + 1e-15)
        out.append(f"{t:.9e} {v:.9g}")
        last = t
    return "PWL(" + " ".join(out) + ")"


def _ctl(rec, j, t0, t1, level0, held0=False):
    """Switch j's driver as two 0 / 1 V sources in LTspice time (1 ps edges): the command (low = the pull-down
    branch conducts) and the pull-up branch (command high and no interlock hold)."""
    ev = [(e["t_s"], "cmd", bool(e["level"])) for e in rec["edges_log"] if e["j"] == j and t0 - 1e-15 <= e["t_s"] <= t1]
    for h in rec.get("gate_holds_last") or []:
        if h["switch"] == j:
            ev += [(t, "hold", v) for t, v in ((h["t_hold_s"], True), (h["t_release_s"], False)) if t0 < t <= t1]
    cmd, hold = bool(level0), bool(held0)
    pc, pu = [(0.0, float(cmd))], [(0.0, float(cmd and not hold))]
    for t, kind, val in sorted(ev):
        tt = t - t0 + T_REL
        if kind == "cmd" and val != cmd:
            pc += [(tt, float(cmd)), (tt + 1e-12, float(val))]
        up0 = cmd and not hold
        cmd, hold = (val, hold) if kind == "cmd" else (cmd, val)
        if (cmd and not hold) != up0:
            pu += [(tt, float(up0)), (tt + 1e-12, float(cmd and not hold))]
    return _pwl(pc), _pwl(pu)


def netlist(rec, k, periods=2, rph="match", maxstep=5e-12, r_on_ls=None):
    import p24_ltspice as LT
    c = rec["snap_circuit"]
    if c["n"] != 4 or c["gate_l_cs"] or c["gate_cg_scale"] != 1.0:
        raise ValueError("replay: four phases, no L_cs, typical gate capacitance only")
    if sum((rec.get("gate_stats") or {}).get("il_holds") or [0]) and "gate_holds_last" not in rec:
        raise ValueError("replay: the record has interlock holds but not their times (gate_holds_last)")
    s0, t0, t1 = window(rec, k, periods)
    rphv, rinfo = rph_value(rec, t0, t1, rph)
    y = s0["y"]
    v = dict(zip(NODES, y[:12]))
    il, iloop = y[12:16], y[16:20]
    cp = CircuitParams(vin=c["vin"], t_ramp=c["t_ramp"], vin_step=c["vin_step"], t_vstep=c["t_vstep"], t_vslew=c["t_vslew"])
    brk = sorted({t0, t1} | {t for t in (c["t_ramp"], c["t_vstep"], c["t_vstep"] + c["t_vslew"]) if t0 < t < t1})
    v["vin"] = cp.vin_at(t0)
    pr, el = LT.flat_device()
    if c["gate_dk2"]:
        assert any(K2 in x for x in pr)
        pr = [x.replace(K2, f"k2={2.115 + c['gate_dk2']:.4f}") for x in pr]
    lines = [f"* A199 replay, snapshot {k}, plant t0 = {t0:.9e} s", f".temp {c['gate_temp']}"] + pr
    lines.append("Vin vin 0 " + _pwl([(0.0, cp.vin_at(t0))] + [(t - t0 + T_REL, cp.vin_at(t)) for t in brk]))
    g_drv = f"(V({{u}})/{{r_on:.6g}}+(1-V({{c}}))/{c['gate_r_off']:.6g})*({c['gate_v_on']:.6g}*V({{c}})-V({{g}},{{s}}))"
    r_on = {"h": c["gate_r_on"], "l": c["gate_r_on"] if r_on_ls is None else r_on_ls}     # r_on_ls: a diagnostic variant
    ic, g = dict(v), s0["gate"]
    del ic["vin"]

    def switch(tag, q, j, drain, src, n_dev):
        """One switch position: its devices, their driver branches and the command source."""
        vg = g[str(j)]["vgs"]
        vs = 0.0 if src == "0" else v[src]
        pc, pu = _ctl(rec, j, t0, t1, g[str(j)]["drv"], g[str(j)]["phase"] == "held")
        lines.extend([f"Vc{tag}{q} c{tag}{q} 0 " + pc, f"Vu{tag}{q} u{tag}{q} 0 " + pu])
        for m in "abc"[:n_dev]:
            inst, gn = f"{tag}{q}{m}", f"g{tag}{q}{m}"
            lines.extend(LT.instance(el, inst, gn, drain, src))
            lines.append(f"Bd_{inst} {src} {gn} I=" + g_drv.format(u=f"u{tag}{q}", c=f"c{tag}{q}", g=gn, s=src, r_on=r_on[tag]))
            ic[gn] = ic[f"{inst}_g"] = vs + vg
            ic[f"{inst}_d"], ic[f"{inst}_s"] = v[drain], vs

    for q in range(1, 5):
        up, h = UP[q - 1], f"h{q}"
        drift = (v[up] - v[h]) / c["loop_l"] * T_REL                       # the hold keeps both ends fixed
        lines.append(f"Ll{q} {up} {h} {c['loop_l']:.9e} ic={iloop[q - 1] - drift:.9g} {L_IDEAL}")
        if c["loop_rp"] > 0:
            lines.append(f"Rl{q} {up} {h} {c['loop_rp']:.9g}")
        switch("h", q, q - 1, h, SRC[q - 1], c["n_high"])
    for q in range(1, 5):
        switch("l", q, 3 + q, f"x{q}", "0", c["n_low"])
        vm = v["out"] + il[q - 1] * rphv
        drift = (v[f"x{q}"] - vm) / c["L"] * T_REL
        lines.append(f"Lp{q} x{q} m{q} {c['L']:.9e} ic={il[q - 1] - drift:.9g} {L_IDEAL}")
        lines.append(f"Rph{q} m{q} out {max(rphv, 1e-9):.9g}")
        ic[f"m{q}"] = vm
    lines.extend(f"Cs{q} a{q} x{q} {c['cs']:.9e}" for q in range(1, 4))
    lines.append(f"Co out 0 {c['co']:.9e}")
    if c["load_kind"] == "r":
        lines.append(f"Rload out 0 {c['r_load']:.9g}")
    i_cc = c["i_load"] if c["load_kind"] == "cc" else 0.0
    if i_cc or c["i_step"]:
        f = lambda t: (i_cc if t >= c["t_load"] else 0.0) + (c["i_step"] if t >= c["t_step"] else 0.0)
        pts = [(0.0, f(t0))]
        for t in sorted(t for t in (c["t_load"], c["t_step"]) if t0 < t < t1):
            pts += [(t - t0 + T_REL, f(t - 1e-15)), (t - t0 + T_REL + 1e-12, f(t))]
        lines.append("Iload out 0 " + _pwl(pts))
    items = [f"V({n})={val:.9g}" for n, val in ic.items()]
    lines += [".ic " + " ".join(items[q:q + 6]) for q in range(0, len(items), 6)]
    lines += [f"Vhold hctl 0 PWL(0 1 {T_REL:.4e} 1 {T_REL + 1e-13:.4e} 0)",
              f".model SWH SW(Ron={HOLD_RON:g} Roff=1e13 Vt=0.5 Vh=0)"]
    for n, val in ic.items():                                             # hold every node, the devices' internal ones too
        lines += [f"Shold_{n} {n} hv_{n} hctl 0 SWH", f"Vhv_{n} hv_{n} 0 {val:.12g}"]
    lines.append(f".tran 0 {T_REL + t1 - t0:.9e} 0 {maxstep:.3e} uic")
    save = [f"V({n})" for n in NODES + ("vin",)] + [f"I(Lp{q})" for q in range(1, 5)] + [f"I(Ll{q})" for q in range(1, 5)]
    for q in range(1, 5):
        save += [f"V(gh{q}a)", f"V(gl{q}a)", f"I(Bswitch_h{q}a)", f"I(Bswitch_l{q}a)"]
    lines.append(".save " + " ".join(save))
    return "\n".join(lines) + "\n", {"t0": t0, "t1": t1, "rph_ohm": rphv, "rph": rph, "rds": rinfo, "r_on_ls": r_on["l"]}


def compare(rec, k, periods, names, a, meta):
    c, t0, t1 = rec["snap_circuit"], meta["t0"], meta["t1"]
    low = [x.lower() for x in names]
    col = lambda n: a[:, low.index(n.lower())]
    t = a[:, 0] - T_REL + t0
    at = lambda x, tq: float(np.interp(tq, t, x))
    vn = {n: col(f"V({n})") for n in NODES + ("vin",)}
    ip = [col(f"I(Lp{q})") for q in range(1, 5)]
    ilp = [col(f"I(Ll{q})") for q in range(1, 5)]
    vds = [vn[f"h{q}"] - vn[SRC[q - 1]] for q in range(1, 5)] + [vn[f"x{q}"] for q in range(1, 5)]
    ich = [col(f"I(Bswitch_h{q}a)") for q in range(1, 5)]
    seg = lambda x, ta, tb: x[(t >= ta) & (t <= tb)]
    out = {"k": k, "t0_s": t0, "periods": periods, "rph": meta["rph"], "rph_ohm": meta["rph_ohm"], "rds": meta["rds"],
           "holds": [h for h in rec.get("gate_holds_last") or [] if t0 <= h["t_hold_s"] <= t1],
           "gates_moving_at_start": [j for j, x in rec["snaps"][k]["gate"].items() if x["phase"] != "idle"]}
    hold = {n: at(vn[n], t0 + 1e-13) - y for n, y in zip(NODES, rec["snaps"][k]["y"][:12])}
    out["start_err_v_max"] = max(abs(x) for x in hold.values())            # the initial state arrived as given
    out["start_err_i_max"] = max(abs(at(ip[q], t0 + 1e-13) - rec["snaps"][k]["y"][12 + q]) for q in range(4))
    st = []
    for q in range(1, periods + 1):                                        # the state one, two, ... periods later
        s = rec["snaps"][k + q]
        st.append({"periods": q, "t_s": s["t_s"],
                   "dv": {n: at(vn[n], s["t_s"]) - y for n, y in zip(NODES, s["y"][:12])},
                   "di": [at(ip[r], s["t_s"]) - s["y"][12 + r] for r in range(4)],
                   "di_loop": [at(ilp[r], s["t_s"]) - s["y"][16 + r] for r in range(4)],
                   "i_plant": s["y"][12:16], "vcs_plant": [s["y"][r] - s["y"][3 + r] for r in range(3)],
                   "dvcs": [(at(vn[f"a{r}"], s["t_s"]) - at(vn[f"x{r}"], s["t_s"])) - (s["y"][r - 1] - s["y"][2 + r])
                            for r in range(1, 4)]})
    out["state"] = st
    edges = [e for e in rec["edges_log"] if t0 - 1e-15 <= e["t_s"] <= t1 - 22e-9]
    pk = []
    for e in edges:                                                        # high-side turn-offs: the physical peak
        if e["j"] < 4 and not e["level"]:
            ph = e["j"] + 1
            pl = [x for x in rec["gate_offs_last"] if x["phase"] == ph and e["t_s"] - 1e-12 <= x["t_s"] <= e["t_s"] + 20e-9]
            w = seg(ip[ph - 1], e["t_s"] - 2e-9, e["t_s"] + 20e-9)
            pk.append({"t_s": e["t_s"], "phase": ph, "plant_a": pl[0]["i_max_a"] if pl else None, "lt_a": float(w.max()),
                       "plant_cmd_a": e["i"][ph - 1], "lt_cmd_a": at(ip[ph - 1], e["t_s"]),
                       "lt_vds_max_v": float(seg(vds[ph - 1], e["t_s"], e["t_s"] + 20e-9).max())})
    out["peaks"] = pk
    va = []
    for e in edges:                                                        # low-side turn-off commands: the valley side
        if e["j"] >= 4 and not e["level"]:
            ph = e["j"] - 3
            va.append({"t_s": e["t_s"], "phase": ph, "plant_a": e["i"][ph - 1], "lt_a": at(ip[ph - 1], e["t_s"]),
                       "lt_min_a": float(seg(ip[ph - 1], e["t_s"] - 5e-9, e["t_s"] + 20e-9).min())})
    out["valleys"] = va
    on = []
    for x in rec["turnons_last"]:                                          # high-side turn-ons
        if not (t0 <= x["t_s"] <= t1 - 22e-9):
            continue
        ph = x["phase"]
        m = (t >= x["t_s"]) & (ich[ph - 1] > ACT_I)
        t_lt = float(t[np.argmax(m)]) if m.any() else None
        on.append({"t_s": x["t_s"], "phase": ph, "plant_vds_cmd_v": x["vds_v"], "lt_vds_cmd_v": at(vds[ph - 1], x["t_s"]),
                   "plant_t_act_s": x.get("t_act_s"), "lt_t_act_s": t_lt, "plant_vds_act_v": x.get("vds_act_v"),
                   "lt_vds_act_v": at(vds[ph - 1], t_lt) if t_lt is not None else None,
                   "lt_vds_at_plant_act_v": at(vds[ph - 1], x["t_act_s"]) if x.get("t_act_s") else None})
    out["turnons"] = on
    out["edges"] = [{"t_s": e["t_s"], "j": e["j"], "level": int(e["level"]), "plant_i": e["i"][:4],
                     "lt_i": [at(ip[r], e["t_s"]) for r in range(4)]} for e in rec["edges_log"] if t0 - 1e-15 <= e["t_s"] <= t1]
    out["loss"] = _loss(rec, k, t, vn, ip, vds, col, c, meta)
    sec = [s for s in rec["sections"] if t0 <= s["t_s"] <= t1]
    out["vds_max"] = [{"t_a_s": sa["t_s"], "t_b_s": sb["t_s"], "plant_v": sb.get("vds_win_v"),
                       "lt_v": [float(seg(vds[j], sa["t_s"], sb["t_s"]).max()) for j in range(8)]}
                      for sa, sb in zip(sec, sec[1:])]
    out["vo"] = [{"t_s": s["t_s"], "plant_v": s["vo"], "lt_v": at(vn["out"], s["t_s"])} for s in sec]
    return out


def _loss(rec, k, t, vn, ip, vds, col, c, meta):
    """Where the energy goes in LTspice over the first period after the snapshot (uJ; channel = terminal V_DS times
    the channel current of one device times the number in parallel), next to what the plant books for a period:
    R i^2 with its lumped R (on LTspice's currents), its edge energy and its reverse-conduction energy (the section
    that closes inside the period)."""
    t0, ta = meta["t0"], rec["snaps"][k + 1]["t_s"]
    m = (t >= t0) & (t <= ta)
    tt = t[m]
    integ = lambda x: float(np.trapezoid(x[m], tt))
    n = [c["n_high"]] * 4 + [c["n_low"]] * 4
    ich = [col(f"I(Bswitch_h{q}a)") for q in range(1, 5)] + [col(f"I(Bswitch_l{q}a)") for q in range(1, 5)]
    e_sw = [1e6 * integ(vds[j] * ich[j] * n[j]) for j in range(8)]
    e_rph = [1e6 * meta["rph_ohm"] * integ(ip[q] ** 2) for q in range(4)]
    e_plant_r = [1e6 * c["R"] * integ(ip[q] ** 2) for q in range(4)]
    sec = [s for s in rec["sections"] if t0 < s["t_s"] <= ta]
    ls_on, hs_on = [], []
    ev = [e for e in rec["edges_log"] if t0 - 1e-15 <= e["t_s"] <= ta]
    for e in ev:                                   # the 40 ns after each high-side turn-off: the low side's turn-on
        if e["j"] < 4 and not e["level"] and e["t_s"] + 40e-9 <= t[-1]:
            q = e["j"]
            w = (t >= e["t_s"]) & (t <= e["t_s"] + 40e-9)
            ls_on.append({"phase": q + 1, "t_s": e["t_s"], "i_a": e["i"][q],
                          "e_uj": 1e6 * float(np.trapezoid((vds[4 + q] * ich[4 + q] * n[4 + q])[w], t[w])),
                          "rev_nvs": 1e9 * float(np.trapezoid(np.maximum(-vds[4 + q][w], 0.0), t[w])),
                          "r_only_nvs": 1e9 * float(np.trapezoid((ip[q] * c["R"])[w], t[w]))})
    on_t = {}
    for e in ev:                                   # each high-side on-time: the channel's drop while it conducts
        if e["j"] < 4:
            if e["level"]:
                on_t[e["j"]] = e["t_s"]
            elif e["j"] in on_t:
                q, ts = e["j"], on_t.pop(e["j"])
                w = (t >= ts) & (t <= e["t_s"])
                hs_on.append({"phase": q + 1, "t_s": ts, "e_uj": 1e6 * float(np.trapezoid((vds[q] * ich[q] * n[q])[w], t[w])),
                              "vds_nvs": 1e9 * float(np.trapezoid(vds[q][w], t[w]))})
    return {"period_s": ta - t0, "lt_channel_uj": e_sw, "lt_rph_uj": e_rph, "plant_r_uj": e_plant_r,
            "plant_edge_uj": [1e6 * x for x in sec[-1].get("edge_energy_j", [0.0] * 8)] if sec else None,
            "plant_rev_uj": [1e6 * x for x in sec[-1].get("rev_energy_j", [0.0] * 8)] if sec else None,
            "i_rms_a": [float(np.sqrt(integ(ip[q] ** 2) / (ta - t0))) for q in range(4)],
            "vo_mean_v": integ(vn["out"]) / (ta - t0), "ls_turn_on": ls_on, "hs_on_time": hs_on}


def replay(rec, k, periods=2, rph="match", tag="a199", keep_raw=False, maxstep=5e-12, r_on_ls=None):
    import p24_ltspice as LT
    net, meta = netlist(rec, k, periods, rph, maxstep, r_on_ls)
    name = f"{tag}_k{k}_{rph}" + ("" if r_on_ls is None else f"_ls{r_on_ls:g}".replace(".", "p"))
    res = LT.run(name, net, timeout=7200)
    if res["raw"] is None:
        raise RuntimeError("LTspice gave no waveform: " + res["log"][-400:])
    names, a = res["raw"]
    out = compare(rec, k, periods, names, a, meta)
    out["points"], out["r_on_ls"] = int(a.shape[0]), meta["r_on_ls"]
    if not keep_raw:
        (LT.WORK / f"{name}.raw").unlink(missing_ok=True)
    return out


def brief(o):
    """One line per replay: the largest differences (LTspice - plant)."""
    d = lambda xs: max((abs(x) for x in xs), default=float("nan"))
    s1 = o["state"][0]
    pk = [x["lt_a"] - x["plant_a"] for x in o["peaks"] if x["plant_a"] is not None]
    vd = [l - p for r in o["vds_max"] if r["plant_v"] for l, p in zip(r["lt_v"], r["plant_v"])]
    on = [x["lt_vds_act_v"] - x["plant_vds_act_v"] for x in o["turnons"] if x["plant_vds_act_v"] is not None and x["lt_vds_act_v"] is not None]
    ta = [(x["lt_t_act_s"] - x["plant_t_act_s"]) * 1e9 for x in o["turnons"] if x["plant_t_act_s"] and x["lt_t_act_s"]]
    return (f"k {o['k']:3d} t0 {o['t0_s'] * 1e6:9.3f} us | start {o['start_err_v_max'] * 1e3:.2f} mV {o['start_err_i_max']:.3f} A | "
            f"1 period: di {' '.join(f'{x:+.2f}' for x in s1['di'])} A, dVcs {' '.join(f'{x * 1e3:+.1f}' for x in s1['dvcs'])} mV, "
            f"dVo {s1['dv']['out'] * 1e3:+.3f} mV | peaks {' '.join(f'{x:+.2f}' for x in pk)} A | V_DS max {d(vd):.2f} V | "
            f"turn-on V {' '.join(f'{x:+.2f}' for x in on)} V, t {' '.join(f'{x:+.2f}' for x in ta)} ns | {o['points']} points")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("record")
    ap.add_argument("--k", type=int, nargs="+", required=True)
    ap.add_argument("--periods", type=int, default=2)
    ap.add_argument("--rph", default="match", choices=("match", "zero", "plant"))
    ap.add_argument("--out")
    ap.add_argument("--tag", default="a199")
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--r-on-ls", type=float, default=None, help="low-side turn-on resistance, ohm (diagnostic variant)")
    a = ap.parse_args(argv)
    rec = load(a.record)
    res = []
    for k in a.k:
        o = replay(rec, k, a.periods, a.rph, a.tag, a.keep_raw, r_on_ls=a.r_on_ls)
        res.append(o)
        print(brief(o), flush=True)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
