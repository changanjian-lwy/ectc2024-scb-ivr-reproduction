"""D62: the P24 module's loss budget and efficiency (per module), from a co-simulation's measured waveforms and public
device data, with every uncertain value carried as a scenario.

Per phase, the inductor current is a triangle: from the valley a (negative) to the peak b over Ton (high side), back to
a over the rest of the period T (low side; the transitions are short and carry ~zero reverse-conduction energy, A97).
The mean square of a linear segment from a to b is (a^2 + a b + b^2) / 3.
Terms (W per module, N phases):
- switches' conduction: high side Ton/T ms R_on/n_h, low side (T - Ton)/T ms R_on/n_l (EPC2067: 1.3 typ, 1.55 max mOhm);
- inductor copper: ms_total x L x (R/L of the inductor technology) - an array of identical elements has R = L R_e/L_e;
- series capacitors: each carries phase k's on-time current and phase k+1's: (Ton/T)(ms_on,k + ms_on,k+1) ESR;
- hard turn-on of the high side at its measured V_DS: its own Eoss plus the other node capacitances' charge through its
  channel (the energy balance's minimum, D57 Section 3), datasheet Coss(V);
- turn-off overlap: I_off^2 t_f^2 / (24 C_node), t_f 0.5-1 ns;
- gate drive: devices x Q x V_GS x f, Q = QG (hard) or QG - QGD (zero-voltage turn-on), EPC2067 QG 17.1 typ / 22.3 max nC,
  QGD 2 nC, V_GS 5 V;
- reverse conduction: the co-simulation's recorded energy.
Not included: Coss hysteresis, AC resistance (skin, proximity), driver and controller quiescent power, output-capacitor
ESR (interleaved ripple), interconnect.
"""
from __future__ import annotations

import numpy as np

from scb_ivr.cosim.circuit import EPC2067Coss

RON_TYP, RON_MAX = 1.3e-3, 1.55e-3            # EPC2067 datasheet, VGS = 5 V, ID = 37 A, 25 C
QG_TYP, QG_MAX, QGD = 17.1e-9, 22.3e-9, 2.0e-9
VGS = 5.0
N_H, N_L = 2, 3

# inductor technology, R/L in Ohm per H (P24 Table 2; the HBS1 MPC core spans 20-500 nH / 13.6-39.3 mOhm)
L_TECH = {"ideal": 0.0, "mpc_hbs1_500nH": 39.3e-3 / 500e-9, "mpc_hbs1_20nH": 13.6e-3 / 20e-9,
          "stripline_composite": 12e-3 / 3e-9, "coaxmil": 12e-3 / 2.5e-9, "substrate_air": 7e-3 / 1.2e-9}


def ms(a, b):
    """Mean square of a linear segment from a to b."""
    return (a * a + a * b + b * b) / 3.0


def phase_ms(valley, peak, ton, period):
    """(high-side ms over the period, low-side ms over the period, on-time ms)."""
    on = ms(valley, peak)
    off = ms(peak, valley)
    return ton / period * on, (period - ton) / period * off, on


def hard_on_energy(vds, v_rail, dv_next, n_h=N_H, n_l=N_L, n_next=N_H, coss=None):
    """Channel energy of a high-side turn-on at V_DS = vds (node at x_on = v_rail - vds): its own Eoss(vds) plus
    int_{x_on}^{v_rail} (v_rail - x) (n_l Coss(x) + n_next Coss(x + dv_next)) dx. n_next = 0 for the last phase."""
    c = coss or EPC2067Coss()
    if vds <= 0:
        return 0.0
    vv = np.linspace(0.0, vds, 400)
    e_own = n_h * float(np.trapezoid(vv * c.c(vv), vv))
    xs = np.linspace(v_rail - vds, v_rail, 400)
    other = n_l * c.c(xs) + n_next * c.c(xs + dv_next)
    return e_own + float(np.trapezoid((v_rail - xs) * other, xs))


def turn_off_overlap(i_off, t_f, c_node=13.5e-9):
    return i_off ** 2 * t_f ** 2 / (24.0 * c_node)


def budget(phases, ton, period, lf, scenario, rails, dv_next, p_rev=0.0, p_out=250.0):
    """phases: per phase {valley, peak, vds_on}; scenario: {ron, l_tech, esr_cs, q_gate, t_f}. Returns W per term."""
    n = len(phases)
    f = 1.0 / period
    out = {"switch_conduction": 0.0, "inductor_copper": 0.0, "series_caps": 0.0, "hard_turn_on": 0.0,
           "turn_off_overlap": 0.0, "gate_drive": 0.0, "reverse_conduction": p_rev}
    on_ms = []
    for k, p in enumerate(phases):
        hs, ls, on = phase_ms(p["valley"], p["peak"], ton, period)
        on_ms.append(on)
        out["switch_conduction"] += hs * scenario["ron"] / N_H + ls * scenario["ron"] / N_L
        out["inductor_copper"] += (hs + ls) * lf * L_TECH[scenario["l_tech"]]
        out["hard_turn_on"] += hard_on_energy(p["vds_on"], rails[k], dv_next[k], n_next=N_H if k < n - 1 else 0) * f
        out["turn_off_overlap"] += turn_off_overlap(p["peak"], scenario["t_f"]) * f
    for k in range(n - 1):
        out["series_caps"] += ton / period * (on_ms[k] + on_ms[k + 1]) * scenario["esr_cs"]
    out["gate_drive"] = n * (N_H + N_L) * scenario["q_gate"] * VGS * f
    total = sum(out.values())
    out["total"] = total
    out["efficiency"] = p_out / (p_out + total)
    return out


def measure(d, n_periods=200, vin=48.0, r_load=4e-3, lsb=4e-9 / 128, t1=None):
    """budget()'s inputs from a one-module co-simulation result d over its last n periods (before t1 if given): each
    phase's mean valley, peak and high-side turn-on V_DS, Ton, the period, the rails and the next phase's rail from the
    series-capacitor voltages, the reverse-conduction power and the output power. scripts/p24_loss_budget.py's
    measurement for any run (A110)."""
    secs = [s for s in d["sections"] if t1 is None or s["t_s"] < t1][-n_periods:]
    t0, t1w = secs[0]["t_s"], secs[-1]["t_s"]
    period = float(np.mean(np.diff([s["t_s"] for s in secs])))
    ton = float(np.mean([s["ton_lsb"] for s in secs])) * lsb
    vcs = np.mean([s["vcs_v"] for s in secs], axis=0)
    chain = [vin] + list(vcs) + [0.0]
    rails = [chain[k] - chain[k + 1] for k in range(4)]
    dv_next = [chain[k + 1] - chain[k + 2] for k in range(3)] + [0.0]
    phases = []
    for k in range(4):
        win = lambda recs: [r for r in recs if r["phase"] == k + 1 and t0 <= r["t_s"] <= t1w]
        phases.append({"valley": float(np.mean([r["i_a"] for r in win(d["lowoffs_last"])])),
                       "peak": float(np.mean([r["i_a"] for r in win(d["highoffs_last"])])),
                       "vds_on": float(np.mean([r["vds_v"] for r in win(d["turnons_last"])]))})
    p_rev = float(np.mean([sum(s["rev_energy_j"]) for s in secs[1:]]) / period)
    p_out = float(np.mean([s["vo"] for s in secs])) ** 2 / r_load
    return {"phases": phases, "ton_s": ton, "period_s": period, "rails_v": rails, "dv_next_v": dv_next, "p_rev_w": p_rev,
            "p_out_w": p_out}

