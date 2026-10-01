"""Closed-loop cycle-to-cycle linearisation of the P24 timed-low-side map with the controller's correctors (D52).

Core map, one cycle of LowPredEventMap from the section (phase-1 turn-on):
    p = (s, d, dl, ton, t0, u)  ->  q = (s', T, crossing_k, valley_k, i_lowoff_k)
- s, s': the section's free variables (section_free);
- d, dl: high-side delays after each low-side turn-off, low-side delays after each high-side turn-off;
- t0: the slot base (phase k's low side turns off at (k - 1) t0 / N);
- u: a shift of phase 1's current threshold (the trim);
- T: the period; crossing_k: phase k's zero crossing after its high-side turn-off; valley_k: the first V_DS minimum
  of phase k's high side after its low-side turn-off (nl_valley_after_lowoff); i_lowoff_k: low-side turn-off current.
Times are in ns, currents in A, voltages in V. core_jacobian() takes central differences at a fixed point.

closed_loop() assembles the linear closed loop for a slot rule, as the RTL updates once per cycle (quantisation
ignored):
    state z = (s, d, dl, acc, slot memory)
    ton  = acc + ki (vref - Vo(s))        the ADC sample at the section updates Ton within the cycle
    d'   = d  - g (d  - valley   - e)     error-based high-side corrector
    dl'  = dl - g (dl - crossing - e)     error-based low-side corrector
    acc' = ton
    t0   = T0 (fixed) | T(n-1) (follow) | (T(n-1) + T(n-2)) / 2 (avg)
Outputs y: i_lowoff_1..4, T, high-side errors d - valley, low-side errors dl - crossing. Returns (A, B, C, D).
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from scb_ivr.p24_exact_event_map import Circuit, section_free, section_full
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff
from scb_ivr.p24_orbit_solver import PEAK, T_RS

N = 4
NS = 2 * N                      # section variables: x1, a2, a3, out, i1..i4
I_OUT = 3                       # index of Vo in the section
P_NAMES = ([f"s{j}" for j in range(NS)] + [f"d{k}" for k in range(1, N + 1)] + [f"dl{k}" for k in range(1, N + 1)]
           + ["ton", "t0", "u"])
Q_NAMES = ([f"s{j}'" for j in range(NS)] + ["T"] + [f"cross{k}" for k in range(1, N + 1)]
           + [f"valley{k}" for k in range(1, N + 1)] + [f"ilo{k}" for k in range(1, N + 1)])
Y_NAMES = [f"ilo{k}" for k in range(1, N + 1)] + ["T"] + [f"eh{k}" for k in range(1, N + 1)] \
    + [f"el{k}" for k in range(1, N + 1)]

_CTX = {}


def _init(coss_factory, pct, vf, r_dev, extra=None):
    _CTX.update(coss=coss_factory(), target=-pct / 100 * PEAK, vf=vf, r_dev=r_dev, **(extra or {}))


def core(p):
    """q(p) for one cycle (see the module docstring)."""
    p = np.asarray(p, float)
    s, d, dl = p[:NS], p[NS:NS + N] * 1e-9, p[NS + N:NS + 2 * N] * 1e-9
    ton, t0, u = p[NS + 2 * N] * 1e-9, p[NS + 2 * N + 1] * 1e-9, p[NS + 2 * N + 2]
    ctl = ControlLP(ton=ton, i_target=_CTX["target"] + u, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl), t0=t0)
    emap = LowPredEventMap(Circuit(), ctl, coss=_CTX["coss"], vf=_CTX["vf"], r_dev=_CTX["r_dev"])
    v, i = section_full(s, emap.ckt)
    v1, i1, lg = emap.run_cycle(v, i)
    valley = []
    for ph in range(1, N + 1):
        r = nl_valley_after_lowoff(emap, v, i, ph)
        if r is None:
            raise RuntimeError(f"no valley on phase {ph}")
        valley.append(r[0] * 1e9)
    lo = {x["phase"]: float(x["i"]) for x in lg["lowoff"]}
    return np.concatenate([section_free(v1, i1, emap.ckt), [lg["period"] * 1e9],
                           [x * 1e9 for x in lg["low_cross_rel"]], valley, [lo[k] for k in range(1, N + 1)]])


def steps(p0, scale=1.0):
    """Central-difference steps: 1e-5 relative (at least 1e-5) for the section, 1 ps for times, 1 mA for u; all
    times `scale`."""
    h = np.empty(len(p0))
    h[:NS] = 1e-5 * np.maximum(1.0, np.abs(p0[:NS]))
    h[NS:NS + 2 * N + 2] = 1e-3
    h[-1] = 1e-3
    return h * scale


def core_jacobian(p0, coss_factory, pct, vf, r_dev, jobs=4, scale=1.0, func=core, step_fn=steps, extra=None):
    """(q0, J, curvature), with the Coss curve from coss_factory() (a module-level function, so that each worker
    process builds its own): J[:, c] = (q(p0 + h_c) - q(p0 - h_c)) / 2h_c; curvature[c] = max|q+ + q- - 2 q0| /
    max|q+ - q-| (second-order part relative to the first-order change, a linearity check per column). func and
    step_fn replace the core map and its steps (D53's per-edge map); extra is added to each worker's context."""
    p0 = np.asarray(p0, float)
    h = step_fn(p0, scale)
    pts = [p0]
    for c in range(len(p0)):
        e = np.zeros(len(p0)); e[c] = h[c]
        pts += [p0 + e, p0 - e]
    with ProcessPoolExecutor(max_workers=jobs, initializer=_init, initargs=(coss_factory, pct, vf, r_dev, extra)) as pool:
        q = list(pool.map(func, pts))
    q0 = q[0]
    J = np.zeros((len(q0), len(p0)))
    curv = np.zeros(len(p0))
    for c in range(len(p0)):
        qp, qm = q[1 + 2 * c], q[2 + 2 * c]
        J[:, c] = (qp - qm) / (2 * h[c])
        curv[c] = np.max(np.abs(qp + qm - 2 * q0)) / max(np.max(np.abs(qp - qm)), 1e-300)
    return q0, J, curv


def closed_loop(J, rule, g=0.5, ki_ns_per_v=0.25):
    """(A, B, C, D) of the linear closed loop for rule 'fixed', 'follow' or 'avg' (module docstring), from the core
    Jacobian J (rows Q_NAMES, columns P_NAMES)."""
    m = {"fixed": 0, "follow": 1, "avg": 2}[rule]
    nz = NS + 2 * N + 1 + m
    iz_d, iz_dl, iz_acc, iz_mem = NS, NS + N, NS + 2 * N, NS + 2 * N + 1
    P = np.zeros((len(P_NAMES) - 1, nz))            # d p / d z (u excluded)
    P[:NS, :NS] = np.eye(NS)
    P[NS:NS + N, iz_d:iz_d + N] = np.eye(N)
    P[NS + N:NS + 2 * N, iz_dl:iz_dl + N] = np.eye(N)
    P[NS + 2 * N, I_OUT] = -ki_ns_per_v              # ton = acc + ki (vref - Vo)
    P[NS + 2 * N, iz_acc] = 1.0
    if rule == "follow":
        P[NS + 2 * N + 1, iz_mem] = 1.0
    elif rule == "avg":
        P[NS + 2 * N + 1, iz_mem] = P[NS + 2 * N + 1, iz_mem + 1] = 0.5
    Qz, Qu = J[:, :-1] @ P, J[:, -1]
    r_T, r_cr, r_va, r_lo = NS, NS + 1, NS + 1 + N, NS + 1 + 2 * N
    A = np.zeros((nz, nz)); B = np.zeros(nz)
    A[:NS], B[:NS] = Qz[:NS], Qu[:NS]
    Ed = np.zeros((N, nz)); Ed[:, iz_d:iz_d + N] = np.eye(N)
    Edl = np.zeros((N, nz)); Edl[:, iz_dl:iz_dl + N] = np.eye(N)
    A[iz_d:iz_d + N] = (1 - g) * Ed + g * Qz[r_va:r_va + N]
    B[iz_d:iz_d + N] = g * Qu[r_va:r_va + N]
    A[iz_dl:iz_dl + N] = (1 - g) * Edl + g * Qz[r_cr:r_cr + N]
    B[iz_dl:iz_dl + N] = g * Qu[r_cr:r_cr + N]
    A[iz_acc] = P[NS + 2 * N]
    if m >= 1:
        A[iz_mem], B[iz_mem] = Qz[r_T], Qu[r_T]
    if m == 2:
        A[iz_mem + 1, iz_mem] = 1.0
    C = np.vstack([Qz[r_lo:r_lo + N], Qz[r_T:r_T + 1], Ed - Qz[r_va:r_va + N], Edl - Qz[r_cr:r_cr + N]])
    D = np.concatenate([Qu[r_lo:r_lo + N], [Qu[r_T]], -Qu[r_va:r_va + N], -Qu[r_cr:r_cr + N]])
    return A, B, C, D


def response(A, B, C, D, z):
    """H(z) = C (zI - A)^-1 B + D, one complex gain per output."""
    return C @ np.linalg.solve(z * np.eye(len(A)) - A, B) + D
