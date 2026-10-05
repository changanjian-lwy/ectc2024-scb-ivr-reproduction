"""A146: the measurement model and the non-learned estimators the CNN is compared with.

measure(v, dt, rng, ...): a probe (2nd-order Butterworth low-pass, fc), trigger jitter (a sub-sample shift), sampling
  at DT_SCOPE and Gaussian noise; v is a clean 20 ps trace from a146_data.trace.
crb(theta, sigma, fc): the Cramer-Rao bound of (log L, log Q_act, log didt, k) with I0 known: J = d(measured trace)
  / d(theta) by central differences, F = J^T J / sigma^2 (white noise at the scope's rate), bound = sqrt(diag F^-1).
sine_fit(y, i0): what an engineer does with a scope: a damped cosine fitted from the first peak on gives omega and tau;
  Q = omega tau / 2, L = 1 / (omega^2 C) with C = 2 Coss(v_ring) at the nominal Coss (k = 1 assumed); didt from the
  initial rise v = a t^2 (the node charged by the current the channel no longer carries, didt = 2 C_node a, C_node
  10 nF from A145's L = 0 rows). k is not identifiable by this method.
sim_fit(y, i0): least squares of the measured trace against the harness over (log L, log Q, log didt, k) plus the
  trigger shift and the probe bandwidth, from the ranges' centre or from th0 (e.g. the CNN's estimate; scipy
  least_squares, trust region), the expensive reference."""
from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit, least_squares
from scipy.signal import butter, lfilter

from a146_data import RANGES, trace
from scb_ivr.cosim.circuit import EPC2067Coss

DT_TRACE, DT_SCOPE = 20e-12, 40e-12
COSS = EPC2067Coss()
C_NODE = 10e-9


def q_act(q, k):
    """The ring's quality factor: rp = q sqrt(L / (2 Coss_nom(12 V))) against the actual sqrt(L / (2 k Coss))."""
    return q * np.sqrt(k)


def probe(v, fc, dt=DT_TRACE):
    b, a = butter(2, fc, fs=1.0 / dt)
    return lfilter(b, a, v - v[0]) + v[0]


def measure(v, rng=None, fc=1e9, sigma=0.2, jitter_s=0.0):
    """Probe, sub-sample trigger shift (linear interpolation), decimation to DT_SCOPE, noise."""
    y = probe(np.asarray(v, float), fc)
    step = int(round(DT_SCOPE / DT_TRACE))
    t = np.arange(0, len(y) - step, step) * DT_TRACE
    y = np.interp(t + jitter_s, np.arange(len(y)) * DT_TRACE, y)
    if rng is not None and sigma > 0:
        y = y + rng.normal(0.0, sigma, len(y))
    return y


def theta_of(l_ph, q, didt, k):
    return np.array([np.log(l_ph), np.log(q_act(q, k)), np.log(didt), k])


def _trace_theta(th, i0):
    l_ph, qa, didt, k = np.exp(th[0]), np.exp(th[1]), np.exp(th[2]), th[3]
    return trace(l_ph, qa / np.sqrt(k), didt, i0, k)


def crb(th, i0, sigma=0.2, fc=1e9, d=(0.02, 0.02, 0.02, 0.01)):
    cols = []
    for j, h in enumerate(d):
        tp, tm = th.copy(), th.copy(); tp[j] += h; tm[j] -= h
        cols.append((measure(_trace_theta(tp, i0), fc=fc, sigma=0) - measure(_trace_theta(tm, i0), fc=fc, sigma=0)) / (2 * h))
    J = np.stack(cols, axis=1)
    F = J.T @ J / sigma ** 2
    cov = np.linalg.inv(F)
    return np.sqrt(np.diag(cov)), float(np.linalg.cond(F))


def sine_fit(y, i0, dt=DT_SCOPE):
    t = np.arange(len(y)) * dt
    kp = int(np.argmax(y))
    tt, yy = t[kp:] - t[kp], y[kp:]
    v_end = float(np.mean(yy[-len(yy) // 5:]))
    f0 = 1.0 / 4e-9
    try:
        par, _ = curve_fit(lambda s, vf, a, tau, w, ph: vf + a * np.exp(-s / tau) * np.cos(w * s + ph), tt, yy,
                           p0=(v_end, yy[0] - v_end, 5e-9, 2 * np.pi * f0, 0.0), maxfev=4000)
        vf, a, tau, w, ph = par
        c = 2 * COSS.c(vf)
        l_ph, q = 1.0 / (w * w * c) * 1e12, abs(w * tau) / 2
    except (RuntimeError, ValueError):
        l_ph, q = np.nan, np.nan
    rise = (y < y[0] + 3.0) & (t < t[kp])                            # the first 3 V of the rise
    rise_t, rise_v = t[rise], y[rise] - y[0]
    if len(rise_t) > 4:
        a2 = np.polyfit(rise_t - rise_t[0], rise_v, 2)[0]
        didt = 2 * C_NODE * a2 * 1e-9
    else:
        didt = np.nan
    return {"l_ph": l_ph, "q_act": q, "didt": didt}


def sim_fit(y, i0, max_nfev=150, th0=None):
    """6 parameters: (log L, log Q_act, log didt, k) and the measurement chain an engineer would also fit, the
    trigger shift (ps) and log of the probe's bandwidth; th0 (4 values, e.g. the CNN's) replaces the centre start."""
    lo = np.array([np.log(RANGES["l_ph"][0]), np.log(q_act(RANGES["q"][0], RANGES["k"][0])), np.log(RANGES["didt"][0]),
                   RANGES["k"][0], -200.0, np.log(0.4e9)])
    hi = np.array([np.log(RANGES["l_ph"][1]), np.log(q_act(RANGES["q"][1], RANGES["k"][1])), np.log(RANGES["didt"][1]),
                   RANGES["k"][1], 200.0, np.log(3e9)])
    start = 0.5 * (lo[:4] + hi[:4]) if th0 is None else np.clip(np.asarray(th0, float), lo[:4] + 1e-9, hi[:4] - 1e-9)
    x0 = np.concatenate([start, [0.0, np.log(1e9)]])
    def res(th):
        return measure(_trace_theta(th[:4], i0), fc=float(np.exp(th[5])), sigma=0, jitter_s=th[4] * 1e-12) - y
    r = least_squares(res, x0, bounds=(lo, hi), x_scale=np.array([0.3, 0.3, 0.3, 0.05, 30.0, 0.3]), diff_step=0.01,
                      max_nfev=max_nfev)
    return {"l_ph": float(np.exp(r.x[0])), "q_act": float(np.exp(r.x[1])), "didt": float(np.exp(r.x[2])), "k": float(r.x[3]),
            "shift_ps": float(r.x[4]), "fc_ghz": float(np.exp(r.x[5]) / 1e9), "nfev": int(r.nfev), "cost": float(r.cost)}
