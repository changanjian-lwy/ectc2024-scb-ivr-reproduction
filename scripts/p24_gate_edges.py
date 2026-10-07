"""D79: single gate-driven edges of the P24 module, the co-simulation plant (cosim/gate.py) against LTspice with EPC's
own model on every switch (scripts/p24_ltspice.py; vendor library outside the repo).

Edge states are A145's (flying capacitors 36 / 24 / 12 V, 48 V input, loop l_ph with Q damping on every high side,
phases 2-4 on their low sides at 40 A):
- "on": SH1 off at V_DS = dv with phase 1 at i1 = 0 (the valley), turned on through r_on (5 V drive);
- "off": SH1 conducting i0 (its loop carrying i0), turned off through r_off (0 V).
Both simulators: 2 + 3 devices per high / low side, each high-side device with its own resistor; L_cs per device
between its source pin and the power node (the driver returns at the power node); in LTspice the loop inductance is
reduced by L_cs / 2 so the power loop is the same.

edge_plant(...) / edge_lt(...) return the same metrics: SH1 V_DS trace, t_50 (V_DS halfway, from the command), the
channel current's peak and maximum slope, SH2's (on) or SH1's (off) peak V_DS, the channel energy.
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A145_p24_finite_switching_edges"))
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import a145_edge as E  # noqa: E402
from a144_edge import VCS, q_rp  # noqa: E402

from scb_ivr.cosim.circuit import Sim  # noqa: E402
from scb_ivr.cosim.plant import FastPlant  # noqa: E402

T_ON = 2e-9
T_REL = 0.2e-9          # LTspice: every node held at its initial value until then (charge-defined capacitors start
                        # uncharged under uic, D79), so LTspice time = plant time + T_REL
OUT = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"


def gparams(l_ph, q, r_on, r_off, lcs=0.0, temp=25.0, dk2=0.0, cg=1.0, edge_off=0.0, edge_on=0.0):
    rp = q_rp(l_ph * 1e-12, q) if (q and l_ph) else 0.0
    p = E.params(l_ph, rp, 10e-12)
    return dataclasses.replace(p, gate_dev="EPC2067", gate_switches=(0, 1, 2, 3), gate_r_on=r_on, gate_r_off=r_off,
                               gate_l_cs=lcs, gate_temp=temp, gate_dk2=dk2, gate_cg_scale=cg,
                               edge_didt_off=edge_off * 1e9, edge_didt_on=edge_on * 1e9), rp


def _state(p, case, dv, i1, i0):
    s = Sim(p)
    if case == "on":
        y = E.y0(p, 0.0)
        y[s.idx["h1"]] = p.vin
        a1 = p.vin - dv
        y[s.idx["a1"]], y[s.idx["x1"]] = a1, a1 - VCS[0]
        if s.nlp:
            y[s.idx["h2"]] = a1
            y[s.nv + 4 + s.na] = 0.0
        y[s.nv] = i1
        return y, [False] * 4, [False, True, True, True]
    return E.y0(p, i0), [True, False, False, False], [False, True, True, True]


def _metrics(t, vds1, ich, vpk_other, e_ch, case, v0, pw=None):
    """t from the command; vds1 SH1's V_DS; ich the channel current (switch)."""
    tgt = 0.5 * v0 if case == "on" else None
    if case == "on":
        k = np.argmax(vds1 < tgt)
    else:
        k = np.argmax(vds1 > 6.0)                       # turn-off: V_DS through 6 V (half a 12 V rail)
    t50 = float(t[k]) if k > 0 else None
    if case == "on":                                    # the edge: until V_DS first reaches the hand-over level
        ke = int(np.argmax(vds1 <= 0.2)) or len(t)
    else:                                               # until the channel is off after V_DS left zero
        k1 = int(np.argmax(vds1 > 1.0))
        ke = k1 + int(np.argmax(np.abs(ich[k1:]) < 0.02)) if k1 else len(t)
        ke = ke if ke > k1 else len(t)
    t, ich = t[:ke + 1], ich[:ke + 1]
    if pw is not None:                                  # energy over the same interval (LTspice)
        e_ch = float(np.trapezoid(pw[:ke + 1], t))
    di = np.diff(ich) / np.diff(t)
    return dict(t50_ns=None if t50 is None else t50 * 1e9, ich_pk_a=float(np.max(np.abs(ich))),
                didt_max_a_ns=float(np.max(np.abs(di))) * 1e-9, vpk_v=float(vpk_other), e_ch_nj=e_ch * 1e9)


def vin_for(case, dv):
    """Input of the edge state: 48 V, or for a turn-on above 12.5 V the +4.8 V line step's 52.8 V (rail 1 = 16.8 V,
    x1 = vin - dv - 36 near zero)."""
    return 52.8 if (case == "on" and dv > 12.5) else 48.0


def edge_plant(case, l_ph, r, dv=3.8, i1=0.0, i0=143.0, q=7, lcs=0.0, t_win=40e-9, **kw):
    p, _ = gparams(l_ph, q, r if case == "on" else 1.0, r if case == "off" else 4.5, lcs=lcs, **kw)
    p = dataclasses.replace(p, vin=vin_for(case, dv))
    y, gh, gl = _state(p, case, dv, i1, i0)
    pl = FastPlant(p, y, gh=gh, gl=gl)
    pl.integrate_to(T_ON, lambda: None)
    if case == "off":                                   # the gate starts fully charged
        pl.gm.st[0]["vgs"] = p.gate_v_on; pl.gm.st[0]["drv"] = True; pl.gm.st[0]["t"] = pl.t
    pl.set_gate(0, case == "on")
    ts, v1, v2, ich, e0 = [], [], [], [], pl.gm.stats["e_total_j"][0]
    gs = pl.gm.st[0]

    def on_step():
        ts.append(pl.t - T_ON); v1.append(float(pl.vds(0))); v2.append(float(pl.vds(1)))
        if gs["phase"] == "active":
            ich.append(pl.gm.nsw[0] * pl.gm.fd.i_ch(gs["vgs"], gs["vds"]))
        elif case == "off":                             # conducting: the switch carries its loop current
            ich.append(float(pl.y[pl.nv + 4 + pl.sim.na]) if pl.eff(0) else 0.0)
        else:                                           # turn-on: after the hand-over not part of the edge
            ich.append(np.nan if pl.eff(0) else 0.0)
    pl.integrate_to(T_ON + t_win, on_step)
    t, v1, v2, ich = np.array(ts), np.array(v1), np.array(v2), np.array(ich)
    ich = np.where(np.isnan(ich), np.nan, ich)
    m = np.isfinite(ich)
    out = _metrics(t[m], v1[m], ich[m], (v2.max() if case == "on" else v1.max()),
                   pl.gm.stats["e_total_j"][0] - e0, case, dv if case == "on" else 0.0)
    if case == "on":                                    # the channel's 10-90 % rise over the active edge
        out["didt_1090_a_ns"], out["t_rise_ns"] = slope_1090(t[m], ich[m])
    else:                                               # V_DS 10-90 % of the rail (1.2 -> 10.8 V)
        k1, k2 = int(np.argmax(v1 > 1.2)), int(np.argmax(v1 > 10.8))
        out["t_vrise_ns"] = float((t[k2] - t[k1]) * 1e9) if k2 > k1 else None
    st = pl.gm.summary()
    out.update(delay_ns=(st["delay_on_s"][1] if case == "on" else st["delay_off_s"][1]) * 1e9,
               active_ns=((st["active_on_s"][1] if case == "on" else st["active_off_s"][1]) or 0.0) * 1e9,
               newton_max=st["newton_max"], steps=st["steps"])
    return out, (t, v1, v2)


def lt_netlist(case, l_ph, r, dv=3.8, i1=0.0, i0=143.0, q=7, lcs=0.0, t_win=40e-9, temp=25.0, dk2=0.0,
               r_hs_off=1.0, r_ls=0.0, lg=0.0, mis=0.0):
    """... lg: gate-loop inductance (H) in series with each SH1 gate resistor; mis: SH1b's threshold shift (V)."""
    import p24_ltspice as LT
    rp = q_rp(l_ph * 1e-12, q) if (q and l_ph) else 0.0
    pr, el = LT.flat_device()
    if dk2:
        pr = [x.replace("k2=2.115e+00", f"k2={2.115 + dk2:.4f}") for x in pr]
    l_eff = l_ph * 1e-12 - lcs / 2
    vin = vin_for(case, dv)
    lines = ["* D79 single edge", f".temp {temp}"] + pr + [f"Vin vin 0 {vin}"]
    if case == "on":
        a1 = vin - dv
        v = dict(a1=a1, x1=a1 - VCS[0], a2=VCS[1], x2=0.0, a3=VCS[2], x3=0.0, x4=0.0, out=1.0, h1=vin, h2=a1,
                 h3=VCS[1], h4=VCS[2])
        il, iloop1 = [i1, 40.0, 40.0, 40.0], 0.0
    else:
        v = dict(a1=48.0, x1=48.0 - VCS[0], a2=VCS[1], x2=0.0, a3=VCS[2], x3=0.0, x4=0.0, out=1.0, h1=48.0, h2=48.0,
                 h3=VCS[1], h4=VCS[2])
        il, iloop1 = [i0, 40.0, 40.0, 40.0], i0
    up = ["vin", "a1", "a2", "a3"]; src = ["a1", "a2", "a3", "x4"]
    ic = dict(v)
    for k in range(4):
        lines.append(f"Ll{k + 1} {up[k]} h{k + 1} {l_eff:.6e} ic={iloop1 if k == 0 else 0.0}")
        if rp:
            lines.append(f"Rl{k + 1} {up[k]} h{k + 1} {rp:.6e}")
        for mdev in "ab":
            inst = f"h{k + 1}{mdev}"
            sp = f"cs{k + 1}{mdev}" if lcs else src[k]
            if lcs:
                lines.append(f"Lcs{k + 1}{mdev} {sp} {src[k]} {lcs:.6e} ic={(iloop1 / 2) if k == 0 else 0.0}")
                ic[sp] = v[src[k]]
            g = f"g{k + 1}{mdev}"
            k2i = (2.115 + dk2 + mis) if (k == 0 and mdev == "b" and mis) else None
            lines += LT.instance(el, inst, g, f"h{k + 1}", sp, k2=k2i)
            if k == 0 and lg:
                lines += [f"Rgd{k + 1}{mdev} dr1 gl{k + 1}{mdev}x {max(r, 1e-3):.6e}",
                          f"Lgd{k + 1}{mdev} gl{k + 1}{mdev}x {g} {lg:.6e}"]
                ic[f"gl{k + 1}{mdev}x"] = v[src[k]] + (5.0 if case == "off" else 0.0)
            elif k == 0:
                lines.append(f"Rgd{k + 1}{mdev} dr1 {g} {max(r, 1e-3):.6e}")
            else:
                lines.append(f"Rgo{k + 1}{mdev} {g} {src[k]} {r_hs_off:.6e}")
            von = (5.0 if (k == 0 and case == "off") else 0.0)
            ic[g] = v[src[k]] + von
            ic[f"{inst}_g"], ic[f"{inst}_d"], ic[f"{inst}_s"] = v[src[k]] + von, v[f"h{k + 1}"], v[src[k]]
    v0, v1 = (0.0, 5.0) if case == "on" else (5.0, 0.0)
    lines.append(f"Vdr1 dr1 a1 PWL(0 {v0} {T_REL + T_ON:.4e} {v0} {T_REL + T_ON + 1e-12:.4e} {v1})")
    ic["dr1"] = v["a1"] + v0
    for k in range(4):
        on = k > 0
        for mdev in "abc":
            inst = f"l{k + 1}{mdev}"
            g = f"gl{k + 1}{mdev}"
            lines += LT.instance(el, inst, g, f"x{k + 1}", "0")
            if r_ls > 0:                                # the low-side driver through r_ls (dv/dt immunity check)
                lines += [f"Vgl{k + 1}{mdev} vgl{k + 1}{mdev} 0 {5.0 if on else 0.0}",
                          f"Rgl{k + 1}{mdev} vgl{k + 1}{mdev} {g} {r_ls:.6e}"]
                ic[g] = 5.0 if on else 0.0
            else:
                lines.append(f"Vgl{k + 1}{mdev} {g} 0 {5.0 if on else 0.0}")
            ic[f"{inst}_g"], ic[f"{inst}_d"], ic[f"{inst}_s"] = (5.0 if on else 0.0), v[f"x{k + 1}"], 0.0
        drift = (v[f"x{k + 1}"] - 1.0) / 2.9333333e-9 * T_REL       # the hold keeps x_k - m_k fixed
        lines.append(f"Lp{k + 1} x{k + 1} m{k + 1} 2.9333333e-9 ic={il[k] - drift:.9g}")
        lines.append(f"Rph{k + 1} m{k + 1} out 0.54e-3")
        ic[f"m{k + 1}"] = 1.0
    for k in range(3):
        lines.append(f"Cs{k + 1} a{k + 1} x{k + 1} 6e-6")
    lines += ["Co out 0 4.672e-3", "Rload out 0 4e-3"]
    items = [f"V({n})={val:.6g}" for n, val in ic.items()]
    lines += [".ic " + " ".join(items[k:k + 8]) for k in range(0, len(items), 8)]   # short lines
    lines += [f"Vhold hctl 0 PWL(0 1 {T_REL:.4e} 1 {T_REL + 1e-13:.4e} 0)",
              ".model SWH SW(Ron=1m Roff=1e13 Vt=0.5 Vh=0)"]
    for n, val in ic.items():                           # hold every node, the devices' internal ones too
        if n == "dr1":
            continue
        lines += [f"Shold_{n} {n} hv_{n} hctl 0 SWH", f"Vhv_{n} hv_{n} 0 {val:.9g}"]
    lines.append(f".tran 0 {T_REL + T_ON + t_win:.4e} 0 5e-12 uic")
    lines.append(".save V(h1) V(a1) V(h2) V(a2) I(Bswitch_h1a) I(Bswitch_h1b) V(h1a_g) V(h1a_s) V(h1b_g) V(h1b_s) "
                 "V(l1a_g) V(h2a_g) V(h2a_s)")
    return "\n".join(lines) + "\n"


def edge_lt(case, l_ph, r, dv=3.8, i1=0.0, i0=143.0, q=7, lcs=0.0, t_win=40e-9, tag="", **kw):
    import p24_ltspice as LT
    net = lt_netlist(case, l_ph, r, dv, i1, i0, q, lcs, t_win, **kw)
    name = f"d79_{case}_{l_ph}_{r}_{dv}_{i0}_{lcs * 1e12:.0f}{tag}".replace(".", "p")
    res = LT.run(name, net)
    names, a = res["raw"]
    low = [x.lower() for x in names]
    col = lambda n: a[:, low.index(n.lower())]
    t = a[:, 0] - T_REL - T_ON
    v1 = col("V(h1)") - col("V(a1)")
    v2 = col("V(h2)") - col("V(a2)")
    ich = col("I(Bswitch_h1a)") + col("I(Bswitch_h1b)")
    m = t >= 0
    pw = v1 * ich
    out = _metrics(t[m], v1[m], ich[m], (v2[m].max() if case == "on" else v1[m].max()), 0.0, case,
                   dv if case == "on" else 0.0, pw=pw[m])
    vg = col("V(h1a_g)") - col("V(h1a_s)")
    from scb_ivr.p24_gate_model import load_device
    d = load_device(temp=kw.get("temp", 25.0), dk2=kw.get("dk2", 0.0))
    if case == "on":
        v_act = d.vgs_for(0.01, dv)
        k = np.argmax((vg > v_act) & m)
    else:
        v_act = d.vgs_for(i0 / 2, 0.2)
        k = np.argmax((vg < v_act) & m)
    out["delay_ns"] = float(t[k]) * 1e9
    ia, ib = col("I(Bswitch_h1a)"), col("I(Bswitch_h1b)")   # per device (a mismatch case: b's threshold shifted)
    va = col("V(h1a_g)") - col("V(h1a_s)"); vb = col("V(h1b_g)") - col("V(h1b_s)")
    out["ia_pk"], out["ib_pk"] = float(np.abs(ia[m]).max()), float(np.abs(ib[m]).max())
    out["ea_nj"] = float(np.trapezoid((v1 * ia)[m], t[m])) * 1e9
    out["eb_nj"] = float(np.trapezoid((v1 * ib)[m], t[m])) * 1e9
    out["vgs_sh1_max"], out["vgs_sh1_min"] = float(max(va[m].max(), vb[m].max())), float(min(va[m].min(), vb[m].min()))
    tail = t[m] > (out["t50_ns"] or 0) * 1e-9 + 3e-9 if case == "off" else None
    if tail is not None:                                # re-turn-on after the turn-off: gate back above 1 V
        out["vgs_sh1_tail_max"] = float(max(va[m][tail].max(), vb[m][tail].max()))
    gl1 = col("V(l1a_g)")                               # SL1's internal gate (source = ground)
    gh2 = col("V(h2a_g)") - col("V(h2a_s)")
    out["vgs_sl1_max"], out["vgs_sl1_min"] = float(gl1[m].max()), float(gl1[m].min())
    out["vgs_sh2_max"], out["vgs_sh2_min"] = float(gh2[m].max()), float(gh2[m].min())
    return out, (t[m], v1[m], v2[m])


CASES = [("on", 50, 4.5, 3.8, 143.0, 0.0), ("on", 50, 4.5, 12.0, 143.0, 0.0), ("on", 125, 10.0, 12.0, 143.0, 0.0),
         ("on", 150, 7.0, 17.0, 143.0, 0.0), ("off", 50, 1.2, 3.8, 143.0, 0.0), ("off", 150, 1.2, 3.8, 200.0, 0.0),
         ("off", 100, 0.0, 3.8, 143.0, 0.0), ("on", 100, 4.5, 12.0, 143.0, 20e-12), ("off", 100, 1.2, 3.8, 143.0, 20e-12)]


def validate(cases=CASES):
    rows = []
    for case, l, r, dv, i0, lcs in cases:
        a, _ = edge_plant(case, l, r, dv=dv, i0=i0, lcs=lcs)
        b, _ = edge_lt(case, l, r, dv=dv, i0=i0, lcs=lcs)
        rows.append(dict(case=case, l_ph=l, r=r, dv=dv, i0=i0, lcs_ph=lcs * 1e12, plant=a, lt=b))
        print(f"{case:3s} L{l:3d} R{r:4.1f} dv{dv:4.1f} i0{i0:5.0f} Lcs{lcs * 1e12:3.0f} | delay {a['delay_ns']:5.2f}/{b['delay_ns']:5.2f}"
              f" t50 {a['t50_ns'] or 0:5.2f}/{b['t50_ns'] or 0:5.2f} di/dt {a['didt_max_a_ns']:5.1f}/{b['didt_max_a_ns']:5.1f}"
              f" Vpk {a['vpk_v']:5.2f}/{b['vpk_v']:5.2f} E {a['e_ch_nj']:6.1f}/{b['e_ch_nj']:6.1f}")
    return rows


if __name__ == "__main__":
    rows = validate()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "D79_gate_validation.json").write_text(json.dumps(rows, indent=1))


# ---- D79 Section 3-5: resistor maps, the linear ramp at equal slope, spread ----

def ramp_edge(case, l_ph, didt, dv=3.8, i1=0.0, i0=143.0, q=7, t_win=40e-9):
    """The same edge with A145's linear ramp (turn-on or turn-off at didt A/ns, the other edge 72 A/ns)."""
    p, _ = gparams(l_ph, q, 1.0, 1.0)
    p = dataclasses.replace(p, gate_dev="", gate_switches=(), vin=vin_for(case, dv),
                            edge_didt_on=(didt if case == "on" else 36.0) * 1e9,
                            edge_didt_off=(didt if case == "off" else 72.0) * 1e9)
    y, gh, gl = _state(p, case, dv, i1, i0)
    pl = FastPlant(p, y, gh=gh, gl=gl)
    pl.integrate_to(T_ON, lambda: None)
    pl.set_gate(0, case == "on")
    v1, v2 = [], []
    pl.integrate_to(T_ON + t_win, lambda: (v1.append(float(pl.vds(0))), v2.append(float(pl.vds(1)))))
    return float(max(v2) if case == "on" else max(v1)), pl.edge_stats["e_total_j"][0] * 1e9


def slope_1090(t, ich, lo=0.1, hi=0.9):
    """Average slope of |i| between 10 % and 90 % of its edge extreme (A/ns), and that time."""
    a = np.abs(ich)
    pk = np.nanmax(a)
    k1 = int(np.argmax(a >= lo * pk)); k2 = int(np.argmax(a >= hi * pk))
    if k2 <= k1:
        return None, None
    return float((hi - lo) * pk / (t[k2] - t[k1]) * 1e-9), float((t[k2] - t[k1]) * 1e9)


def on_row(l_ph, r, dv, **kw):
    a, (t, v1, v2) = edge_plant("on", l_ph, r, dv=dv, **kw)
    return a


def equal_slope_ramp(l_ph, dv, target_v, lo=4.0, hi=400.0):
    """The linear turn-on slope (A/ns) whose SH2 peak equals target_v (bisection in log slope)."""
    vlo, _ = ramp_edge("on", l_ph, lo, dv=dv)
    vhi, _ = ramp_edge("on", l_ph, hi, dv=dv)
    if not (vlo <= target_v <= vhi):
        return None
    for _ in range(18):
        m = math.sqrt(lo * hi)
        vm, _ = ramp_edge("on", l_ph, m, dv=dv)
        lo, hi = (m, hi) if vm < target_v else (lo, m)
    return math.sqrt(lo * hi)


LS = (50, 75, 100, 125, 150)
R_ON = (1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 14.0)
DV = (3.8, 12.0, 17.0)
R_OFF = (0.0, 0.5, 1.2, 2.0, 3.0, 5.0)
I0 = (143.0, 200.0, 260.0)
# datasheet V_GS(TH) 0.7 / 1.0 / 2.5 V (min / typ / max); EPC's model is the typical device (its transfer curve
# matches Fig. 2's typical one), so the spread shifts its curve by -0.3 / +1.5 V; C_ISS max / typ = 3267 / 2178
SPREAD = {"nominal": {}, "hot125": {"temp": 125.0}, "vth_min": {"dk2": -0.3}, "vth_max": {"dk2": 1.5},
          "ciss_max": {"cg": 1.5}}


def _job(arg):
    kind, kw = arg
    try:
        if kind == "on":
            r, _ = edge_plant("on", kw["l"], kw["r"], dv=kw["dv"], lcs=kw.get("lcs", 0.0), **kw.get("spread", {}))
        elif kind == "off":
            r, _ = edge_plant("off", kw["l"], kw["r"], i0=kw["i0"], lcs=kw.get("lcs", 0.0), **kw.get("spread", {}))
        elif kind == "ramp_eq":
            g, _ = edge_plant("on", kw["l"], kw["r"], dv=kw["dv"])
            r = dict(gate=g, ramp_eq_a_ns=equal_slope_ramp(kw["l"], kw["dv"], g["vpk_v"]),
                     ramp_at_1090=ramp_edge("on", kw["l"], g["didt_1090_a_ns"], dv=kw["dv"]))
        r = {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in r.items()} if kind != "ramp_eq" else r
        return dict(kind=kind, **{k: v for k, v in kw.items() if k != "spread"}, spread=kw.get("tag", "nominal"), res=r)
    except Exception as e:                              # recorded, not hidden
        return dict(kind=kind, **{k: v for k, v in kw.items() if k != "spread"}, error=repr(e))


def sweep_jobs():
    jobs = [("on", dict(l=l, r=r, dv=dv)) for l in LS for r in R_ON for dv in DV]
    jobs += [("off", dict(l=l, r=r, i0=i0)) for l in LS for r in R_OFF for i0 in I0]
    jobs += [("on", dict(l=100, r=4.5, dv=12.0, lcs=x * 1e-12, tag=f"lcs{x}")) for x in (10, 25, 50)]
    jobs += [("off", dict(l=100, r=1.2, i0=200.0, lcs=x * 1e-12, tag=f"lcs{x}")) for x in (10, 25, 50)]
    for tag, sp in SPREAD.items():
        if tag == "nominal":
            continue
        for l, r, dv in ((50, 4.5, 3.8), (100, 4.5, 17.0), (150, 7.0, 17.0)):
            jobs.append(("on", dict(l=l, r=r, dv=dv, spread=sp, tag=tag)))
        for l, r, i0 in ((50, 1.2, 143.0), (150, 1.2, 200.0)):
            jobs.append(("off", dict(l=l, r=r, i0=i0, spread=sp, tag=tag)))
    jobs += [("ramp_eq", dict(l=l, r=r, dv=dv)) for l in (50, 100, 150) for r in (2.0, 4.5, 10.0) for dv in (3.8, 17.0)]
    return jobs


def sweep(jobs_n=6):
    from multiprocessing import Pool
    jobs = sweep_jobs()
    with Pool(jobs_n) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "D79_gate_sweep.json").write_text(json.dumps(rows, indent=1, default=float))
    return rows


CAND = {"S50": (50, 2.0, 0.3), "S50b": (50, 2.5, 0.3), "S75": (75, 3.0, 0.3), "S75b": (75, 3.5, 0.3),
        "S100": (100, 3.0, 0.5)}                                                                       # D79 Section 5


def sweep2_jobs():
    jobs = []
    for tag, sp in SPREAD.items():
        for name, (l, ron, roff) in CAND.items():
            for dv in (3.8, 12.0, 17.0):
                jobs.append(("on", dict(l=l, r=ron, dv=dv, spread=sp, tag=f"{name}_{tag}")))
            for i0 in (143.0, 200.0, 260.0):
                jobs.append(("off", dict(l=l, r=roff, i0=i0, spread=sp, tag=f"{name}_{tag}")))
    for name, (l, ron, roff) in CAND.items():                 # driver resistance +-30 % and L_cs 10 / 25 pH
        for f in (0.7, 1.3):
            jobs.append(("on", dict(l=l, r=ron * f, dv=17.0, tag=f"{name}_r{f}")))
            jobs.append(("off", dict(l=l, r=roff * f, i0=200.0, tag=f"{name}_r{f}")))
        for x in (10, 25):
            jobs.append(("on", dict(l=l, r=ron, dv=17.0, lcs=x * 1e-12, tag=f"{name}_lcs{x}")))
            jobs.append(("off", dict(l=l, r=roff, i0=200.0, lcs=x * 1e-12, tag=f"{name}_lcs{x}")))
    return jobs


def sweep2(jobs_n=6):
    from multiprocessing import Pool
    with Pool(jobs_n) as pool:
        rows = pool.map(_job, sweep2_jobs(), chunksize=1)
    (OUT / "D79_gate_candidates.json").write_text(json.dumps(rows, indent=1, default=float))
    return rows


def mismatch_and_gate_loop():
    """LTspice at S50 (50 pH, 2.5 / 0.3 ohm): SH1's two devices with thresholds 0.5 V apart (turn-on 17 V, turn-off
    200 A), and a gate-loop inductance of 0.5 / 1 / 2 nH per device (turn-on 3.8 V and 17 V, turn-off 200 A)."""
    rows = []
    l, ron, roff = CAND["S50b"]
    for case, kw in (("on", dict(dv=17.0)), ("off", dict(i0=200.0))):
        r = ron if case == "on" else roff
        for mis in (0.0, 0.5):
            out, _ = edge_lt(case, l, r, mis=mis, tag=f"_mis{mis}", **kw)
            rows.append(dict(kind="mismatch", case=case, mis_v=mis, **kw, res=out))
            print(rows[-1]["case"], mis, {k: round(out[k], 2) for k in ("vpk_v", "ia_pk", "ib_pk", "ea_nj", "eb_nj")})
    for case, kw in (("on", dict(dv=3.8)), ("on", dict(dv=17.0)), ("off", dict(i0=200.0)), ("off", dict(i0=143.0))):
        r = ron if case == "on" else roff
        for lg in (0.0, 0.5e-9, 1e-9, 2e-9):
            out, _ = edge_lt(case, l, r, lg=lg, tag=f"_lg{lg * 1e9:g}", **kw)
            rows.append(dict(kind="gate_loop", case=case, lg_nh=lg * 1e9, **kw, res=out))
            print(case, kw, lg * 1e9, {k: round(out[k], 2) for k in ("vpk_v", "e_ch_nj", "vgs_sh1_max", "vgs_sh1_min")},
                  round(out.get("vgs_sh1_tail_max", float("nan")), 2))
    (OUT / "D79_mismatch_gate_loop.json").write_text(json.dumps(rows, indent=1, default=float))
    return rows


def dvdt_check():
    """LTspice: the off devices' internal gate swing (SL1 and SH2) during SH1's edges at the candidates, with the
    high sides held off through the candidate's r_off and the low sides through 0.3 ohm."""
    rows = []
    for name, (l, ron, roff) in CAND.items():
        for case, kw in (("on", dict(dv=17.0)), ("on", dict(dv=3.8)), ("off", dict(i0=200.0))):
            r = ron if case == "on" else roff
            out, _ = edge_lt(case, l, r, r_hs_off=max(roff, 1e-3), r_ls=0.3, tag="_dvdt", **kw)
            rows.append(dict(cand=name, case=case, **kw, **{k: out[k] for k in ("vpk_v", "vgs_sl1_max", "vgs_sl1_min",
                                                                             "vgs_sh2_max", "vgs_sh2_min")}))
            print(rows[-1])
    (OUT / "D79_dvdt.json").write_text(json.dumps(rows, indent=1))
    return rows
