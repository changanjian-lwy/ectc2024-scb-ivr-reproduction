"""LSCB DC-capacitor ladder on one P24 module, open-loop LTspice power stage (extension lscb_ladder, A180).

LSCB = Tong et al., "A 2D-Extendable 48V-1V Ladder-Series-Capacitor Buck Converter for Computing Power Delivery",
VLSI 2026: four capacitors C_DC in series across Vin make Vin/4 domains, and a switch S_DC (with a body diode) from
each ladder node to the series node between two cells holds the flying capacitors near k Vin/4 (off in steady state,
on in its transient and idle states).

P24's module (cosim/circuit.py) has the same series chain without LSCB's extra node between cells:
vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4, Csk a_k-x_k (k < 4), SLk x_k-0, Lk x_k-out. Clamp k joins ladder node d(4-k)
(nominally (4-k) Vin/4 = Vcs_k) to a_k:
- "diode": a diode of vf and r, anode at the ladder - it can only stop Vcs_k falling more than vf below the ladder;
- "active": the same diode plus a switch of r closed while SL_k is commanded on and the window is open. A switch is
  safe only then (a_k = Vcs_k + x_k); with SH_k on it would short Vcs_(k-1) to the ladder. LSCB adds the extra node
  for exactly this reason.
Every clamp current is reported positive from the ladder into a_k.

Power stage: switches of r_on, linear Coss (c_high / c_low as the cosim's linear default), reverse conduction as a
diode per switch (EPC2067 Fig. 8 fit 2.089 V + 6.01 mOhm per device / n devices), R per phase in the inductor, the
cosim's Co and resistive load. Drive (precomputed PWL gates, t_edge transitions): fixed period T, phases interleaved by
T/4, dead time t_dead on both edges, Ton = ton0 vin0 / vin(t_period_start) (ideal feed-forward, clamped 0.5-2 ton0)
on line-step rows, ton0 fixed on the start-up row. No controller, no valley timing, no package loop: this is the cheap
first check before any cosim work.
"""
from __future__ import annotations

import numpy as np

PARAMS = dict(
    vin=48.0, L=2.9333333e-9, R=0.54e-3, cs=6e-6, co=4.672e-3, rload=4e-3,   # P24 module, A124 / final cfg circuit
    c_high=2 * 1860e-12, c_low=3 * 1860e-12,                                    # cosim linear Coss (CircuitParams)
    rev_vf=2.0894, rev_r=6.0134e-3, n_high=2, n_low=3,                         # fit_fig8(), EPC2067 per device
    r_on=0.1e-3, t_dead=4.5e-9, t_edge=0.2e-9, ton0=38.6e-9, T=452e-9,       # T set by the A180 smoke run
    t_step=40e-6, t_end=80e-6, t_win=20e-6, t_ramp=137.22e-6, t_su_end=150e-6,
    cdc_esr=1e-3, r_bal=1e6, maxstep=0.5e-9, vo0=1.0035, il0=62.7,                        # vo0 / il0 from the smoke run
)

VARIANTS = {
    "base": None,
    "d07_c20": dict(kind="diode", vf=0.7, r=5e-3, cdc=20e-6),     # LSCB's Si body diode, passive
    "d30_c20": dict(kind="diode", vf=3.0, r=5e-3, cdc=20e-6),     # a clamp whose off-state drop exceeds the GaN LS's
    "act_c06": dict(kind="active", vf=3.0, r=5e-3, cdc=6e-6),     # switched clamp in a window after the disturbance
    "act_c20": dict(kind="active", vf=3.0, r=5e-3, cdc=20e-6),
    "act_c60": dict(kind="active", vf=3.0, r=5e-3, cdc=60e-6),
    "actall_c20": dict(kind="active", vf=3.0, r=5e-3, cdc=20e-6, always=True),
}

ROWS = {
    "up1": dict(kind="step", dv=4.8, slew=1e-6),
    "up5": dict(kind="step", dv=4.8, slew=5e-6),
    "dn1": dict(kind="step", dv=-4.8, slew=1e-6),
    "su": dict(kind="startup"),
}


def _g(x):
    return f"{x:.9g}"


def vin_wave(row, p=None):
    """(times, values) of the input source for a row."""
    p = {**PARAMS, **(p or {})}
    r = ROWS[row]
    if r["kind"] == "step":
        ts = p["t_step"]
        return [0.0, ts, ts + r["slew"]], [p["vin"], p["vin"], p["vin"] + r["dv"]]
    return [0.0, p["t_ramp"]], [0.0, p["vin"]]


def gate_intervals(row, p=None):
    """Per phase k (1..4): list of (t_on, t_off_hs, t_on_ls, t_off_ls) per period."""
    p = {**PARAMS, **(p or {})}
    T, ton0, td = p["T"], p["ton0"], p["t_dead"]
    step = ROWS[row]["kind"] == "step"
    t_end = p["t_end"] if step else p["t_su_end"]
    tv, vv = vin_wave(row, p)
    res = {}
    for k in range(1, 5):
        iv, t0 = [], (k - 1) * T / 4 + 5e-9
        while t0 < t_end:
            ton = min(max(ton0 * p["vin"] / max(float(np.interp(t0, tv, vv)), 1.0), 0.5 * ton0), 2 * ton0) if step else ton0
            iv.append((t0, t0 + ton, t0 + ton + td, t0 + T - td))
            t0 += T
        res[k] = iv
    return res


def _pwl(name, node, pulses, tr):
    """PWL source from 0 to 1 over the (start, end) intervals, tr edges, continuation lines of 8 points."""
    pts = [(0.0, 0.0)]
    for a, b in pulses:
        pts += [(a, 0.0), (a + tr, 1.0), (b, 1.0), (b + tr, 0.0)]
    body = " ".join(f"{_g(t)} {v:g}" for t, v in pts)
    words = body.split(" ")
    lines = [f"V{name} {node} 0 PWL("]
    for i in range(0, len(words), 16):
        lines.append("+ " + " ".join(words[i:i + 16]))
    lines[-1] += ")"
    return lines


def netlist(var, row, p=None):
    """LTspice netlist text for variant `var` on row `row` (without options / .end)."""
    p = {**PARAMS, **(p or {})}
    v, r = VARIANTS[var], ROWS[row]
    vin = p["vin"]
    step = r["kind"] == "step"
    t_end = p["t_end"] if step else p["t_su_end"]
    out = [f"* A180 lscb_ladder {var} {row}"]
    tv, vv = vin_wave(row, p)
    out.append("Vin vin 0 PWL(" + " ".join(f"{_g(a)} {_g(b)}" for a, b in zip(tv, vv)) + ")")
    gates = gate_intervals(row, p)
    tr = p["t_edge"]
    for k in range(1, 5):
        out += _pwl(f"gh{k}", f"gh{k}", [(a, b) for a, b, _, _ in gates[k]], tr)
        out += _pwl(f"gl{k}", f"gl{k}", [(c, d) for _, _, c, d in gates[k]], tr)
    up = {1: "vin", 2: "a1", 3: "a2", 4: "a3"}
    dn = {1: "a1", 2: "a2", 3: "a3", 4: "x4"}
    for k in range(1, 5):
        out += [f"SH{k} {up[k]} {dn[k]} gh{k} 0 SWM", f"DH{k} {dn[k]} {up[k]} DRH", f"CH{k} {up[k]} {dn[k]} {_g(p['c_high'])}",
                f"SL{k} x{k} 0 gl{k} 0 SWM", f"DL{k} 0 x{k} DRL", f"CL{k} x{k} 0 {_g(p['c_low'])}",
                f"L{k} x{k} out {_g(p['L'])} Rser={_g(p['R'])}"]
        if k < 4:
            out.append(f"CS{k} a{k} x{k} {_g(p['cs'])}")
    out += [f"CO out 0 {_g(p['co'])}", f"RL out 0 {_g(p['rload'])}"]
    out += [f".model SWM SW(Ron={_g(p['r_on'])} Roff=1e7 Vt=0.5 Vh=-0.2)",
            f".model DRH D(Ron={_g(p['rev_r'] / p['n_high'])} Roff=1e9 Vfwd={_g(p['rev_vf'])} epsilon=0.02)",
            f".model DRL D(Ron={_g(p['rev_r'] / p['n_low'])} Roff=1e9 Vfwd={_g(p['rev_vf'])} epsilon=0.02)"]
    save = ["V(vin)", "V(out)"] + [f"V(a{k})" for k in (1, 2, 3)] + [f"V(x{k})" for k in (1, 2, 3, 4)] + \
           [f"I(L{k})" for k in (1, 2, 3, 4)] + ["I(Vin)"]
    if v is not None:
        c = v["cdc"]
        for k, (hi, lo) in enumerate((("d1", "0"), ("d2", "d1"), ("d3", "d2"), ("vin", "d3")), 1):
            out += [f"CD{k} {hi} {lo} {_g(c)} Rser={_g(p['cdc_esr'])}", f"RB{k} {hi} {lo} {_g(p['r_bal'])}"]
        out.append(f".model DCL D(Ron={_g(v['r'])} Roff=1e9 Vfwd={_g(v['vf'])} epsilon=0.02)")
        if v["kind"] == "active":
            out.append(f".model SWC SW(Ron={_g(v['r'])} Roff=1e7 Vt=0.5 Vh=-0.2)")
            w0, w1 = (-1.0, 1.0) if v.get("always") else \
                     ((p["t_step"], p["t_step"] + p["t_win"]) if step else (0.0, p["t_ramp"] + 2e-6))
        for k in (1, 2, 3):
            d = f"d{4 - k}"
            out.append(f"DC{k} {d} a{k} DCL")
            save.append(f"I(DC{k})")
            if v["kind"] == "active":                         # closed only inside SL_k's on-intervals in the window
                out.append(f"SC{k} {d} a{k} gc{k} 0 SWC")
                out += _pwl(f"gc{k}", f"gc{k}", [(c, e) for _, _, c, e in gates[k] if c >= w0 and e <= w1], tr)
                save.append(f"I(SC{k})")
        save += ["V(d1)", "V(d2)", "V(d3)"]
    if step:                                                  # start near the steady state; the start-up row from zero
        ic = [f"V(a1)={_g(0.75 * vin)}", f"V(a2)={_g(0.5 * vin)}", f"V(a3)={_g(0.25 * vin)}", "V(x1)=0", "V(x2)=0",
              "V(x3)=0", f"V(out)={_g(p['vo0'])}"]
        if v is not None:
            ic += [f"V(d1)={_g(0.25 * vin)}", f"V(d2)={_g(0.5 * vin)}", f"V(d3)={_g(0.75 * vin)}"]
        out.append(".ic " + " ".join(ic))
        out.append(".ic " + " ".join(f"I(L{k})={_g(p['il0'])}" for k in (1, 2, 3, 4)))
    out.append(".save " + " ".join(save))
    out.append(f".tran 0 {_g(t_end)} 0 {_g(p['maxstep'])}")
    return "\n".join(out) + "\n"


def _col(names, arr, name):
    idx = {n.lower(): i for i, n in enumerate(names)}
    j = idx.get(name.lower())
    return None if j is None else arr[:, j]


def _mean(t, y, a, b):
    m = (t >= a) & (t <= b)
    return float(np.trapezoid(y[m], t[m]) / (t[m][-1] - t[m][0]))


def waves(names, arr):
    """Time, input, output, flying-capacitor voltages, rails, phase currents, clamp currents (or None), ladder."""
    c = lambda n: _col(names, arr, n)
    t, vin = arr[:, 0], c("V(vin)")
    vcs = [c(f"V(a{k})") - c(f"V(x{k})") for k in (1, 2, 3)]
    rails = [vin - vcs[0], vcs[0] - vcs[1], vcs[1] - vcs[2], vcs[2]]
    il = [c(f"I(L{k})") for k in (1, 2, 3, 4)]
    clamp = None
    if c("I(DC1)") is not None:
        clamp = []
        for k in (1, 2, 3):
            i = c(f"I(DC{k})")
            s = c(f"I(SC{k})")
            clamp.append(i + s if s is not None else i)
    ladder = [c(f"V(d{k})") for k in (1, 2, 3)] if c("V(d1)") is not None else None
    return dict(t=t, vin=vin, vo=c("V(out)"), vcs=vcs, rails=rails, il=il, clamp=clamp, ladder=ladder,
                pin=-vin * c("I(Vin)"), a=[c(f"V(a{k})") for k in (1, 2, 3)])


def metrics(names, arr, row, p=None):
    """Steady window before the step (or the last 2 us of the start-up ramp) and the disturbance window after it."""
    p = {**PARAMS, **(p or {})}
    w = waves(names, arr)
    t = w["t"]
    step = ROWS[row]["kind"] == "step"
    a, b = (p["t_step"] - 10e-6, p["t_step"]) if step else (p["t_ramp"] - 2e-6, p["t_ramp"])
    m = (t >= a) & (t < b)
    pre = dict(rails=[_mean(t, r, a, b) for r in w["rails"]], il_avg=[_mean(t, i, a, b) for i in w["il"]],
               il_peak=[float(np.max(i[m])) for i in w["il"]], vo=_mean(t, w["vo"], a, b),
               loss_w=_mean(t, w["pin"] - w["vo"] ** 2 / p["rload"], a, b))
    avg = np.array(pre["il_avg"])
    pre["spread_pct"] = float((avg.max() - avg.min()) / np.mean(np.abs(avg)) * 100)
    if w["clamp"] is not None:
        drops = [w["ladder"][2 - (k - 1)] - w["a"][k - 1] for k in (1, 2, 3)]     # d(4-k) - a_k
        pre["clamp_avg_a"] = [_mean(t, i, a, b) for i in w["clamp"]]
        pre["clamp_loss_w"] = float(sum(_mean(t, dv * i, a, b) for dv, i in zip(drops, w["clamp"])))
    res = dict(row=row, pre=pre)
    if step:
        a2, b2 = p["t_step"], t[-1]
        m2 = (t >= a2) & (t <= b2)
        post = dict(rail_max=[float(np.max(r[m2])) for r in w["rails"]], rail_min=[float(np.min(r[m2])) for r in w["rails"]],
                    il_peak=[float(np.max(i[m2])) for i in w["il"]], il_min=[float(np.min(i[m2])) for i in w["il"]],
                    vo_max=float(np.max(w["vo"][m2])), vo_min=float(np.min(w["vo"][m2])),
                    vin_end=float(w["vin"][-1]))
        nominal = post["vin_end"] / 4
        post["rail1_exc"] = (post["rail_max"][0] - pre["rails"][0]) if ROWS[row]["dv"] > 0 else \
                            (post["rail_min"][0] - pre["rails"][0])
        post["rail_dev_max"] = float(max(max(abs(x - nominal) for x in post["rail_max"]),
                                         max(abs(x - nominal) for x in post["rail_min"])))
        post["rails_end"] = [_mean(t, r, b2 - 2e-6, b2) for r in w["rails"]]
        if w["clamp"] is not None:
            drops = [w["ladder"][2 - (k - 1)] - w["a"][k - 1] for k in (1, 2, 3)]
            post["clamp_peak_a"] = [float(np.max(np.abs(i[m2]))) for i in w["clamp"]]
            post["clamp_charge_uc"] = [float(np.trapezoid(i[m2], t[m2]) * 1e6) for i in w["clamp"]]
            post["clamp_energy_uj"] = float(sum(np.trapezoid((dv * i)[m2], t[m2]) for dv, i in zip(drops, w["clamp"])) * 1e6)
        res["post"] = post
    else:
        res["startup"] = dict(il_peak=[float(np.max(i)) for i in w["il"]], il_min=[float(np.min(i)) for i in w["il"]],
                              rail_dev_end=float(max(abs(x - p["vin"] / 4) for x in pre["rails"])),
                              rails_mid=[float(np.interp(p["t_ramp"] / 2, t, r)) for r in w["rails"]],
                              vin_mid=float(np.interp(p["t_ramp"] / 2, t, w["vin"])))
        if w["clamp"] is not None:
            drops = [w["ladder"][2 - (k - 1)] - w["a"][k - 1] for k in (1, 2, 3)]
            res["startup"]["clamp_energy_uj"] = float(sum(np.trapezoid(dv * i, t) for dv, i in zip(drops, w["clamp"])) * 1e6)
            res["startup"]["clamp_peak_a"] = [float(np.max(np.abs(i))) for i in w["clamp"]]
    return res
