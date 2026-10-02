"""D59: the P24 module's output-voltage loop as a sampled PI on Ton (A104), on D58's averaged plant.

Plant (D58, mode P): the module is a current source k * 4 * ((V_rail - Vo) Ton / (2L) - i_neg) into Co and the load.
Small signal at full load: g = dI/dTon (A per LSB) and the source's own conductance G_src = -dI/dVo, so
Vo(s) / Ton(s) = g / (Co s + G_load + G_src).
Controller (scb_ctrl with cfg_kp): at each ADC sample of Vo (phase 1's turn-on, once per period Ts),
e = vref - code * adc_lsb; acc += ki e (clamped); Ton = round(acc + kp e) (clamped). Each phase uses the Ton of its own
last turn-on, so a new command reaches the four phases over one period.
- design_pi(fc): kp so that |L| = 1 at fc with P alone (fc above the plant pole), ki per sample for a zero at
  fc / zero_ratio;
- margins(): crossover and phase margin of the continuous-time loop with a delay td;
- step(): a load current step from the full-load steady state, phases applied in turn, ADC and Ton quantised;
- startup(): A103's sequence (load from t = 0, handover at 72 us, mode S Ton 568 LSB) with this loop after the
  handover; mode S's r_s from A103's c1 (1.275 mOhm). step(0, ..., vo0=...) gives the recovery from a measured
  handover state instead.
- ladder_f(): the series-capacitor resonances (Roberts' dissertation Eq. 3.44, N = 4), which D58/D59 do not model.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from scb_ivr.p24_startup_averaged import LSB, Module

ADC_LSB = 0.5e-3
TS = 232.2e-9                       # the full-load period
R_S_A103 = 1.275e-3                 # mode S output resistance from A103's c1


def plant(m: Module = Module(), vr: float = 12.0, vo: float = 1.0, ton: float = 568.0):
    g = m.k * m.n * (vr - vo) * LSB / (2 * m.lf)
    g_src = m.k * m.n * ton * LSB / (2 * m.lf)
    return g, g_src, 1.0 / m.r_load


def design_pi(fc, m: Module = Module(), zero_ratio: float = 5.0):
    """(kp in LSB per V, ki in LSB per V per sample)."""
    g, _, _ = plant(m)
    wc = 2 * np.pi * fc
    kp = wc * m.co / g
    return kp, kp * (wc / zero_ratio) * TS


def margins(kp, ki, m: Module = Module(), td: float = 0.75 * TS):
    g, g_src, g_load = plant(m)
    w = np.logspace(3, 7.5, 20000)
    s = 1j * w
    L = (kp + ki / (TS * s)) * g / (m.co * s + g_load + g_src) * np.exp(-s * td)
    i = int(np.argmin(np.abs(np.abs(L) - 1)))
    return float(w[i] / (2 * np.pi)), float(180 + np.degrees(np.angle(L[i])))


def ladder_f(cs: float = 3e-6, m: Module = Module(), d: float = 568 * LSB / TS):
    """Roberts Eq. 3.44: f_k = (2 D / sqrt(L Cs)) sin(k pi / (2N)) / (2 pi), k = 1..N-1."""
    return [float(2 * d / np.sqrt(m.lf * cs) * np.sin(k * np.pi / (2 * m.n)) / (2 * np.pi)) for k in range(1, m.n)]


def _loop(m, kp, ki, vo, acc, vref, lo, hi):
    e = vref - round(vo / ADC_LSB) * ADC_LSB
    acc = min(max(acc + ki * e, lo), hi)
    return acc, int(round(min(max(acc + kp * e, lo), hi)))


def step(i_step, kp, ki, m: Module = Module(), t_end=150e-6, t_step=20e-6, dt=2e-9, vref=1.0, ton0=568.0, vo0=None):
    """Arrays t, vo, ton from the full-load steady state (or from Vo = vo0 with Ton = ton0); i_step (A) added to the
    load from t_step."""
    k, t_x, vr = m.k, m.t_x, m.vin / m.n
    lo, hi = 0.5 * ton0, 2.0 * ton0
    vo, acc, ton_cmd, t, nxt = (vref if vo0 is None else vo0), ton0, int(ton0), 0.0, 0.0
    ton_ph = [ton_cmd] * m.n
    t_ph = [TS * j / m.n for j in range(m.n)]
    out_t, out_v, out_n = [], [], []
    while t < t_end:
        if t >= nxt:
            acc, ton_cmd = _loop(m, kp, ki, vo, acc, vref, lo, hi)
            nxt += m.period_raw(ton_cmd, vo, vr) + t_x
        for j in range(m.n):
            if t >= t_ph[j]:
                ton_ph[j] = ton_cmd
                t_ph[j] += m.period_raw(ton_cmd, vo, vr) + t_x
        i = sum(k * m.i_p_raw(tn, vo, vr) for tn in ton_ph) / m.n
        i_load = vo / m.r_load + (i_step if t >= t_step else 0.0)
        vo += dt * (i - i_load) / m.co
        t += dt
        out_t.append(t); out_v.append(vo); out_n.append(ton_cmd)
    return np.array(out_t), np.array(out_v), np.array(out_n)


def step_metrics(t, vo, ton, t_step=20e-6, vref=1.0, band=0.01):
    a = t > t_step
    ta, va, na = t[a], vo[a], ton[a]
    i = int(np.argmax(np.abs(va - vref)))
    bad = np.nonzero(np.abs(va - vref) > band * vref)[0]
    late = ta > ta[-1] - 30e-6
    return {"extreme_mv": float((va[i] - vref) * 1e3), "t_extreme_us": float((ta[i] - t_step) * 1e6),
            "back_within_1pct_us": float((ta[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0,
            "ton_final_lsb": float(na[late].mean()), "ton_pp_late_lsb": float(na[late].max() - na[late].min()),
            "vo_pp_late_mv": float((va[late].max() - va[late].min()) * 1e3)}


def startup(kp, ki, m: Module = replace(Module(), r_s=R_S_A103), t_hand=72e-6, ton_s=568.0, t_end=300e-6, dt=5e-9,
            vref=1.0, t_ramp=68.61e-6):
    """A103's c1d sequence with this loop after the handover: arrays t, vo, ton."""
    k, t_x = m.k, m.t_x
    lo, hi = 0.5 * ton_s, 2.0 * ton_s
    vo, acc, ton_cmd, t, nxt, mode = 0.0, ton_s, int(ton_s), 0.0, 0.0, 0
    ton_ph = [ton_cmd] * m.n
    t_ph = [0.0] * m.n
    out_t, out_v, out_n = [], [], []
    while t < t_end:
        vin = m.vin * min(t / t_ramp, 1.0)
        vr = vin / m.n
        if mode == 0 and t >= t_hand:
            mode, nxt = 1, t
            t_ph = [t + TS * j / m.n for j in range(m.n)]
        if mode == 0:
            i = (m.a_s * ton_s * vin / m.vin - vo) / m.r_s
        else:
            if t >= nxt:
                acc, ton_cmd = _loop(m, kp, ki, vo, acc, vref, lo, hi)
                nxt += m.period_raw(ton_cmd, vo, vr) + t_x
            for j in range(m.n):
                if t >= t_ph[j]:
                    ton_ph[j] = ton_cmd
                    t_ph[j] += m.period_raw(ton_cmd, vo, vr) + t_x
            i = sum(k * m.i_p_raw(tn, vo, vr) for tn in ton_ph) / m.n
        vo += dt * (i - vo / m.r_load) / m.co
        t += dt
        out_t.append(t); out_v.append(vo); out_n.append(ton_cmd)
    return np.array(out_t), np.array(out_v), np.array(out_n)
