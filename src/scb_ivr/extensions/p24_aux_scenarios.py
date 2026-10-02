"""D57: scenarios for the auxiliary commutation branch (D56, A101) over the values its verdict rests on.

Built on D56's single-phase model (p24_aux_commutation). Each function spans one assumed value:
- required_i_neg: the negative current a phase needs, without a branch, for the high side to reach zero voltage,
  for a given filter inductance and node composition (P24's 1-2% claim);
- hard_on: the hard turn-on loss under three models (A91's lower bound, D56's central estimate, A91's upper bound);
- LR_TECH: Lr's series resistance from its technology's R/L (the main inductor's in this model, or P24 Table 2's
  embedded inductors);
- zcs_residual: the energy and overshoot of a branch opened at a residual current instead of zero;
- area: the added die, inductor and capacitor area per phase, against P24 Table 3's switch area and the main
  inductor and series capacitors of the same technology (stored-energy scaling, see below);
- first_cycle: D56's cycle with Cm at a given voltage, for the first cycles after the branch is enabled.

Stored-energy scaling: a network of n_s x n_p identical elements (L_e, I_e) giving L at I_pk has n_p = I_pk / I_e,
n_s = L n_p / L_e, so n_s n_p = L I_pk^2 / (L_e I_e^2) elements and R = n_s R_e / n_p = L (R_e / L_e). Element count
(area) scales with L I^2 and resistance with L, whatever the element. Capacitors likewise by C V^2 (same dielectric
and voltage rating class).
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy.optimize import brentq

from scb_ivr.extensions.p24_aux_commutation import AuxBranch, EdgeCircuit, Model

EPC2067_DIE_MM2 = 2.85 * 3.25        # EPC2067 datasheet die, as P24 Table 3 counts it (80 x 3.25 x 2.85 = 741 mm^2)
P24_PEAK_A = 125.0                   # P24 Table I / Table 3: 4 phases x 4 modules, IL_peak per phase = 2 Io / (nP nM)

# P24 Table I, 4 phases x 4 modules (IL_peak 125 A): Lcrit per phase at 1, 5 and 10 MHz; and Eq. (4)'s value used here
P24_LF_NH = {"table1_1MHz": 13.44, "table1_5MHz": 2.68, "table1_10MHz": 1.34, "eq4_this_model": 1.4666667}

# node compositions (n_h, n_l, n_next): this model (P24 Table 3: 2 high-side, 3 low-side EPC2067 per phase, the next
# phase's high side on the node); the high side alone (P24 Section III's description of the commutation); P24
# Section IV's package (one high-side and two low-side EPC2067)
NODES = {"this_model_2h3l_next": (2, 3, 2), "high_side_only_2h": (2, 0, 0), "p24_sec4_1h2l_next": (1, 2, 1)}

# Lr technology, R/L in Ohm per H
LR_TECH = {
    "a101_fixed_0p2mohm": None,                       # A101's assumption: 0.2 mOhm whatever Lr
    "as_main_inductor": 0.54e-3 / 1.4666667e-9,       # this model's filter inductor, 0.54 mOhm at 1.4667 nH
    "p24_t2_coaxmil": 12e-3 / 2.5e-9,                 # P24 Table 2 [8]: CoaxMIL, 2.5 nH / 12 mOhm, 8 A
    "p24_t2_substrate_air": 7e-3 / 1.2e-9,            # P24 Table 2 [17]: substrate air core, 1.2 nH / 7 mOhm, 8 A
}


def r_lr(tech: str, lr: float) -> float:
    k = LR_TECH[tech]
    return 0.2e-3 if k is None else k * lr


def node_model(ckt: EdgeCircuit) -> Model:
    """D56's Model for any node composition, including no low-side devices (n_l = 0; its on-resistance is unused)."""
    m = Model(replace(ckt, n_l=max(ckt.n_l, 1)))
    m.ckt = ckt
    return m


def required_i_neg(ckt: EdgeCircuit, hi: float = 400.0):
    """Smallest low-side turn-off current (A, magnitude) for which the free valley of V_DS reaches zero, no branch."""
    m = node_model(ckt)
    f = lambda i: m.valley_free(i, t_max=200e-9)[1]
    if f(hi) > 0.0:
        return float("nan")
    return brentq(f, 0.1, hi, xtol=0.01)


def linear_floor(lf, c, v_rail, vo):
    """The same with one linear capacitance c: x_max = Vo + sqrt(Vo^2 + Z^2 I^2) >= V_rail, Z = sqrt(lf / c)."""
    return float(np.sqrt(max(v_rail ** 2 - 2 * v_rail * vo, 0.0) / (lf / c)))


def hard_on(m: Model, vds_on: float, model: str) -> float:
    """Hard turn-on energy (J) at V_DS = vds_on under one of: 'a91_lower' (the high side's Eoss), 'd56_central' (its
    Eoss plus the other node capacitances' charge drawn through its channel), 'a91_upper' (Qoss(V) V of the five node
    devices)."""
    x = m.ckt.v_rail - vds_on
    if model == "d56_central":
        return m.hard_on_energy(x)
    lo, hi = m.a91_bounds(x)
    return lo if model == "a91_lower" else hi


def zcs_residual(m: Model, lr: float, alpha: float, vm: float, i_res: float):
    """A branch opened at |i| = i_res: Lr's energy 0.5 Lr i^2 rings into the open switch pair (two dies of alpha x
    EPC2067 in series, alpha Coss(vm) / 2) and is lost; the peak of the ring above the blocked voltage."""
    c = alpha * float(m.coss.c(np.array([vm]))[0]) / 2.0
    return {"energy_j": 0.5 * lr * i_res ** 2, "overshoot_v": i_res * np.sqrt(lr / c), "c_pair_f": c}


def area(lr: float, ir_peak: float, ir_rms: float, lf: float, if_peak: float, if_rms: float, alpha: float,
         cm: float, vm_list, cs: float, vcs_list, n_main_dies: int = 5):
    """Added area as fractions of the main stage's of the same technology: per phase for the dies and inductors
    (by peak stored energy, or by L I_rms^2 for a resistance-limited design); for the capacitors, the module's Cm
    (one per phase, at vm_list) against its series capacitors (cs at vcs_list), by C V^2."""
    return {
        "bds_dies_mm2": 2 * alpha * EPC2067_DIE_MM2,
        "bds_vs_main_dies": 2 * alpha / n_main_dies,
        "lr_vs_lf_by_peak_energy": lr * ir_peak ** 2 / (lf * if_peak ** 2),
        "lr_vs_lf_by_rms": lr * ir_rms ** 2 / (lf * if_rms ** 2),
        "cm_vs_series_caps": sum(cm * v ** 2 for v in vm_list) / sum(cs * v ** 2 for v in vcs_list),
    }


def first_cycle(m: Model, i_neg: float, aux: AuxBranch, vm0: float, i_pk: float, x_low: float):
    """D56's cycle with Cm at vm0 (not balanced): the high side turns on at the rail or the valley, off at i_pk."""
    return m.cycle(i_neg, replace(aux, vm=vm0), i_pk=i_pk, x_low=x_low)
