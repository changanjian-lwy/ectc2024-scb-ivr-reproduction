"""D60: D59's loop with the series-capacitor ladder as states (A107).

In mode P (boundary conduction, each cycle starting from the fixed negative current) the charge phase k's high side
carries in its on-time is
    Q_k = Ton (-i_neg + (V_rail,k - Vo) Ton / (2L)),
    V_rail,1 = Vin - V1,  V_rail,k = V_(k-1) - V_k,  V_rail,N = V_(N-1)   (V_k: series capacitor k, a_k - x_k).
Phase k charges Cs_k and phase k+1 discharges it, so per period T
    Cs dV_k / dt = (Q_k - Q_(k+1)) / T.
Linearised, dV/dt = (q' / (T Cs)) D2 V with q' = Ton^2 / (2L) and D2 = tridiag(1, -2, 1): the eigenvalues are
-(2 - 2 cos(j pi / N)), all real. **The ladder relaxes; it does not resonate** - unlike Roberts' Eq. 3.44, which is
for fixed-frequency PWM, where the inductor currents are states. Time constants T Cs / (q' (2 - 2 cos(j pi / N))).
(Mode S, A103's fixed timing during the input ramp, is fixed-frequency PWM: Roberts' resonances apply there.)

Each phase delivers k_cal ((V_rail,k - Vo) Ton / (2L) - i_neg) into Co (D58); the loop is D59's sampled PI with the
phases taking the new Ton at their own turn-ons; the input may step (A106's line steps).
"""
from __future__ import annotations

import numpy as np

from scb_ivr.p24_startup_averaged import LSB, Module
from scb_ivr.p24_voltage_loop import TS, _loop


def relaxation_us(cs: float, m: Module = Module(), ton_lsb: float = 568.0, period: float = TS):
    """The ladder's time constants (us), slowest first."""
    q = (ton_lsb * LSB) ** 2 / (2 * m.lf)
    return [float(period * cs / (q * (2 - 2 * np.cos(j * np.pi / m.n))) * 1e6) for j in range(1, m.n)]


def run(kp, ki, cs=3e-6, m: Module = Module(), t_end=150e-6, t_step=20e-6, dt=2e-9, vref=1.0, ton0=568.0,
        i_step=0.0, dvin=0.0, t_slew=0.0):
    """From the full-load steady state: arrays t, vo, ton, ladder deviation max |V_k / Vin - (N - k) / N|."""
    n = m.n
    k_ph = m.k                      # D58: the module delivers k times the sum of the phases
    vin_at = lambda t: m.vin + dvin * (min(max((t - t_step) / t_slew, 0.0), 1.0) if t_slew > 0 else float(t >= t_step))
    lo, hi = 0.5 * ton0, 2.0 * ton0
    v = np.array([m.vin * (n - j) / n for j in range(1, n)])          # ladder in its steady state
    vo, acc, ton_cmd, t, nxt = vref, ton0, int(ton0), 0.0, 0.0
    ton_ph = [ton_cmd] * n
    t_ph = [TS * j / n for j in range(n)]
    ratio = np.array([(n - j) / n for j in range(1, n)])
    out_t, out_v, out_n, out_d = [], [], [], []
    while t < t_end:
        vin = vin_at(t)
        rails = np.concatenate([[vin - v[0]], v[:-1] - v[1:], [v[-1]]])
        vr_mean = vin / n
        if t >= nxt:
            acc, ton_cmd = _loop(m, kp, ki, vo, acc, vref, lo, hi)
            nxt += m.period_raw(ton_cmd, vo, vr_mean) + m.t_x
        for j in range(n):
            if t >= t_ph[j]:
                ton_ph[j] = ton_cmd
                t_ph[j] += m.period_raw(ton_cmd, vo, vr_mean) + m.t_x
        period = m.period_raw(ton_cmd, vo, vr_mean) + m.t_x
        q = np.array([ton_ph[j] * LSB * (-m.i_neg + (rails[j] - vo) * ton_ph[j] * LSB / (2 * m.lf)) for j in range(n)])
        i = sum(k_ph * ((rails[j] - vo) * ton_ph[j] * LSB / (2 * m.lf) - m.i_neg) for j in range(n))
        v = v + dt * (q[:-1] - q[1:]) / (period * CS_SCALE * cs)
        vo += dt * (i - vo / m.r_load - (i_step if t >= t_step else 0.0)) / m.co
        t += dt
        out_t.append(t); out_v.append(vo); out_n.append(ton_cmd); out_d.append(float(np.max(np.abs(v / vin - ratio))))
    return np.array(out_t), np.array(out_v), np.array(out_n), np.array(out_d)


CS_SCALE = 1.0   # the ladder charge equation's capacitance multiplier (1: Cs as given)


def metrics(t, vo, dev, t_step=20e-6, vref=1.0, base_dev=0.0):
    a = t >= t_step
    ta, va, da = t[a], vo[a], dev[a] + base_dev
    i = int(np.argmax(np.abs(va - vref)))
    bad = np.nonzero(np.abs(va - vref) > 0.01 * vref)[0]
    lad = np.nonzero(da > 0.01)[0]
    return {"extreme_mv": float((va[i] - vref) * 1e3), "t_extreme_us": float((ta[i] - t_step) * 1e6),
            "back_within_1pct_us": float((ta[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0,
            "ladder_dev_peak": float(da.max()), "ladder_back_below_1pct_us": float((ta[lad[-1]] - t_step) * 1e6) if len(lad) else 0.0}
