"""D61: what a P24 module must offer for multi-module operation - current sharing, interleaving and the ZVS margin on a
shared output (averaged; no co-simulation).

From D58 (mode P, boundary conduction with a fixed negative current i_neg), per phase:
    I = (V_rail - Vo) Ton / (2 L) - i_neg            (average current)
    T = Ton (1 + (V_rail - Vo) / Vo) + t_x            (period: rise Ton, fall dI L / Vo = (V_rail - Vo) Ton / Vo)
The period does not contain L or i_neg. So modules whose inductors differ by eps cannot have both equal currents and
equal periods with Ton alone:
- equal Ton (one shared loop): equal periods, currents in proportion to 1 / L;
- equal currents by Ton: periods in proportion to L, so interleaved modules drift apart;
- equal Ton and equal currents: each module's i_neg absorbs the difference, i_neg,m = i_neg + I_ac (1 / (1 + eps_m) - 1)
  with I_ac = (V_rail - Vo) Ton / (2L), which moves that module's ZVS margin.
Strategies on M modules sharing Vo, Co and the load (simulate()):
    "independent": each module's own PI (A104) on its own Vo sample (its ADC offset);
    "shared": one PI (one ADC) and one Ton for every module;
    "droop": each module's own PI towards vref - r_droop I_m (a load line per module), its own ADC offset.
"""
from __future__ import annotations

import numpy as np

from scb_ivr.p24_startup_averaged import LSB, Module
from scb_ivr.p24_voltage_loop import ADC_LSB, TS, design_pi


def module_current(m: Module, ton, vo, vr=12.0, eps=0.0, i_neg=None):
    """One module's output current (A), four phases, D58's calibration; inductors scaled by (1 + eps)."""
    i_n = m.i_neg if i_neg is None else i_neg
    return m.k * m.n * ((vr - vo) * ton * LSB / (2 * m.lf * (1 + eps)) - i_n)


def period(m: Module, ton, vo, vr=12.0):
    return m.period_raw(ton, vo, vr) + m.t_x


def i_neg_for_equal_current(m: Module, eps, ton=568.0, vo=1.0, vr=12.0):
    """The negative current that gives a module with inductors (1 + eps) L the nominal module's current at equal Ton."""
    i_ac = (vr - vo) * ton * LSB / (2 * m.lf)
    return m.i_neg + i_ac * (1.0 / (1.0 + eps) - 1.0)


def drift_time_us(m: Module, d_ton_lsb, ton=568.0, vo=1.0, vr=12.0, n_slots=16):
    """Time for two free-running modules whose Ton differ by d_ton_lsb to slip by one interleaving slot (T / n_slots)."""
    t0, t1 = period(m, ton, vo, vr), period(m, ton + d_ton_lsb, vo, vr)
    dt = abs(t1 - t0)
    return float("inf") if dt == 0 else float(t0 / n_slots / dt * t0 * 1e6)


def simulate(strategy, n_mod=4, eps=(0.0, 0.0, 0.0, 0.0), adc_offset_v=(0.0, 0.0, 0.0, 0.0), m: Module = Module(),
             fc=100e3, r_droop=0.0, t_end=400e-6, dt=5e-9, vref=1.0, i_step=0.0, t_step=200e-6, ton0=568.0):
    """M modules into one output (Co and load scaled by M). Returns t, vo, I (per module), Ton (per module)."""
    kp, ki = design_pi(fc, m)              # per module, D59; a shared loop sees M times the gain and M times Co: the same
    co, r_load = m.co * n_mod, m.r_load / n_mod
    lo, hi = 0.5 * ton0, 2.0 * ton0
    vo = vref
    acc = [ton0] * n_mod
    ton = [ton0] * n_mod
    nxt = 0.0
    T, V, II, NN = [], [], [], []
    t = 0.0
    while t < t_end:
        cur = [module_current(m, ton[j], vo, eps=eps[j]) for j in range(n_mod)]
        if t >= nxt:
            if strategy == "shared":
                code = round((vo + adc_offset_v[0]) / ADC_LSB) * ADC_LSB
                e = vref - code
                acc[0] = min(max(acc[0] + ki * e, lo), hi)
                ton = [int(round(min(max(acc[0] + kp * e, lo), hi)))] * n_mod
            else:
                for j in range(n_mod):
                    code = round((vo + adc_offset_v[j]) / ADC_LSB) * ADC_LSB
                    e = vref - r_droop * cur[j] - code
                    acc[j] = min(max(acc[j] + ki * e, lo), hi)
                    ton[j] = int(round(min(max(acc[j] + kp * e, lo), hi)))
            nxt += TS
        i_tot = sum(cur)
        vo += dt * (i_tot - vo / r_load - (i_step if t >= t_step else 0.0)) / co
        t += dt
        T.append(t); V.append(vo); II.append(cur); NN.append(list(ton))
    return np.array(T), np.array(V), np.array(II), np.array(NN)
