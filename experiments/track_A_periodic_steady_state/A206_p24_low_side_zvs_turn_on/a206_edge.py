"""A206 single-edge harness: one high-side turn-off followed by its low side's turn-on, on the plant alone.

Phase 1's high side conducts i0 and is commanded off at t = 0; its low side is commanded on t_dead later (the settled
record's 3.03 ns), when the node has swung below zero. The other phases sit on their low sides. Reported for 40 ns
from the turn-off command: the low side's reverse volt-seconds (int max(-V_DS, 0) dt), its channel-edge and
diode-fit energies, the time until it conducts, and phase 1's current at the end.
  PYTHONPATH=src python3 a206_edge.py            table for zvs off / on and the low-side turn-on resistances
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from scb_ivr.cosim.circuit import CircuitParams, fit_fig8
from scb_ivr.cosim.plant import FastPlant

HERE = Path(__file__).resolve().parent
L0, CS, T_DEAD, T_END = 2.9333333199999997e-09, 6e-6, 3.03125e-9, 40e-9
T_PRE = 0.1e-9
R_TYP, R_MAX = 1.276e-3, 1.55e-3            # ohm per device: the vendor model at 5 V / 25 C (A205), datasheet maximum


def params(zvs, r_on_ls=-1.0, r_sw=(), r=0.54e-3, temp=25.0, dk2=0.0, r_on=3.0, v_hand=0.2, miller=False):
    vf, rr, _ = fit_fig8(10.0, 100.0)
    return CircuitParams(L=L0, cs=CS, R=r, nonlinear_coss=True, rev_drop=True, rev_vf=vf, rev_r=rr, diode_check=True,
                         t_ramp=0.0, load_kind="cc", i_load=250.0, t_load=0.0, gate_dev="EPC2067",
                         gate_switches=tuple(range(8)), gate_r_on=r_on, gate_r_off=0.3, gate_temp=temp, gate_dk2=dk2,
                         gate_il="threshold", gate_t_il=1e-9, gate_v_hand=v_hand, gate_r_on_ls=r_on_ls,
                         gate_zvs_edge=bool(zvs), gate_miller=bool(miller), r_sw=tuple(r_sw))


def edge(p, i0=136.4, t_dead=T_DEAD, t_end=T_END, trace=False):
    n = p.n
    y0 = np.zeros(2 * n + 2 * n)                               # a1..a3, x1..x4, out, i1..i4
    y0[:3] = [48.0, 24.0, 12.0]; y0[3] = 12.0; y0[7] = 1.0
    y0[8:12] = [i0, 100.3, 9.8, 55.1]
    pl = FastPlant(p, y0[:8 + n], [True, False, False, False], [False, True, True, True])
    for j in (0, 5, 6, 7):
        pl.gm.st[j].update(vgs=p.gate_v_on, drv=True)
    for j in range(2 * n):
        pl.gm.st[j]["vds"] = float(pl.vds(j))
    log = []

    def on_step():
        log.append((pl.t, float(pl.vds(n)), float(pl.y[pl.nv]), pl.gm.st[n]["vgs"], pl.gm.st[n]["phase"], pl.eff(n)))

    pl.integrate_to(T_PRE, lambda: None)                       # the conducting high side takes its drop
    pl.set_gate(0, False)
    pl.integrate_to(T_PRE + t_dead, on_step)
    v_cmd = float(pl.vds(n))
    pl.set_gate(n, True)
    pl.integrate_to(T_PRE + t_end, on_step)
    t = np.array([a[0] for a in log]) - T_PRE; v = np.array([a[1] for a in log]); i = np.array([a[2] for a in log])
    dt = np.diff(np.concatenate([[0.0], t]))
    on = [a[0] - T_PRE for a in log if a[5]]
    out = {"v_cmd": v_cmd, "rev_nvs": float(np.sum(np.maximum(-v, 0.0) * dt) * 1e9), "v_min": float(v.min()),
           "t_on_ns": (on[0] - t_dead) * 1e9 if on else None, "i_end": float(i[-1]), "i_peak": float(i.max()),
           "e_edge_uj": pl.edge_e[n] * 1e6, "e_rev_uj": pl.rev_e[n] * 1e6, "e_hs_uj": pl.edge_e[0] * 1e6,
           "steps": pl.gm.stats["steps"], "newton_max": pl.gm.stats["newton_max"], "vgs_end": pl.gm.st[n]["vgs"]}
    if trace:
        out["trace"] = [(round((a[0] - T_PRE) * 1e9, 3), round(a[1], 3), round(a[2], 2), round(a[3], 3), a[4])
                        for a in log[::25]]
    return out


def table():
    rows = {"off (as V5)": params(False)}
    for r in (3.0, 1.0, 0.3):
        rows[f"zvs, low side {r:g} ohm"] = params(True, r_on_ls=r)
    for r in (3.0, 1.0, 0.3):
        rows[f"zvs + r_sw typ, {r:g} ohm"] = params(True, r_on_ls=r, r_sw=(R_TYP / 2, R_TYP / 3), r=0.0)
    for r in (3.0, 1.0, 0.3):
        rows[f"zvs + miller + r_sw typ, {r:g} ohm"] = params(True, r_on_ls=r, r_sw=(R_TYP / 2, R_TYP / 3), r=0.0, miller=True)
    return {k: edge(p) for k, p in rows.items()}


if __name__ == "__main__":
    res = table()
    (HERE / "a206_edge.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, o in res.items():
        print(f"{k:34s} V_cmd {o['v_cmd']:6.2f} V  rev {o['rev_nvs']:5.2f} nVs  V_min {o['v_min']:6.2f}  on after "
              f"{o['t_on_ns']:6.2f} ns  i_end {o['i_end']:7.2f} A  edge {o['e_edge_uj']:6.3f} uJ  fit {o['e_rev_uj']:6.3f} uJ  "
              f"steps {o['steps']}  newton {o['newton_max']}")
