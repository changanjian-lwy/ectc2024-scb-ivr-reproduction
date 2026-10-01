"""Gate-driver jitter in the P24 closed loop (D53): the timed-low-side map with one input per gate edge, a linear
covariance model, and a Monte Carlo of the linearised circuit with the controller's exact rules.

Per-edge core map (one cycle from the section, the actual phase-1 turn-on; times in ns, currents in A):
    p = (s, d_1..4, dl_1..4, ton_1..4, slot_2..4, u)  ->  q = (s', T, crossing_1..4, valley_1..4, i_lowoff_1..4)
with each phase's own on-time and slot (ControlLP's ton_offset / slot_offset) and u the shift of phase 1's
current threshold. edge_jacobian() differentiates it at an orbit (p24_closed_loop.core_jacobian).

How the jitter enters (bridge.py: each commanded edge reaches the plant at t_cmd + t_drv + delta; the RTL schedules
every edge from the previous commanded one, so the circuit sees differences of consecutive edge jitters):
    d_1  = d1 + eta(n) - loff_1          eta(n): phase 1's turn-on jitter at the end of cycle n
    ton_1 = Ton + hoff_1 - eta(n-1)       dl_k = dl_k + lon_k - hoff_k
    slot_k = slot_k + loff_k - eta(n-1)   d_k  = d_k + hon_k - loff_k        (k = 2..4)
    ton_k = Ton + hoff_k - hon_k          u   += -(Vo/L) loff_1             (phase 1's turn-off delay)
The measured errors are the actual edge minus the valley / crossing; the slots' period is that of the commanded
phase-1 turn-ons, T(n) - eta(n) + eta(n-1).

linear_loop(): the closed loop with these 16 white inputs per cycle (correctors with gain g, the voltage loop, the
slot rule; no quantisation, no early rule) and the trim input; covariance() its stationary output covariance.
monte_carlo(): the same linearised circuit with the RTL's rules (bridge.py, rtl/scb_phase.v, rtl/scb_ctrl.v):
integer delays in LSB, errors rounded to the LSB, d -= (err - tgt) >>> 1 clamped, a turn-on before the valley
(crossing) adds dt_step (dtl_step), the trim steps +-1 on the sign of phase 1's turn-off current, the voltage loop
in integers, and the slot rule in integers.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_discrete_lyapunov

from scb_ivr import p24_closed_loop as pcl
from scb_ivr.p24_exact_event_map import Circuit, section_free, section_full
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap
from scb_ivr.p24_nonlinear_event_map import nl_valley_after_lowoff
from scb_ivr.p24_orbit_solver import T_RS

N, NS = pcl.N, pcl.NS
I_D, I_DL, I_TON, I_SL, I_U = NS, NS + N, NS + 2 * N, NS + 3 * N, NS + 3 * N + N - 1
NP = I_U + 1
P_NAMES = ([f"s{j}" for j in range(NS)] + [f"d{k}" for k in range(1, N + 1)] + [f"dl{k}" for k in range(1, N + 1)]
           + [f"ton{k}" for k in range(1, N + 1)] + [f"slot{k}" for k in range(2, N + 1)] + ["u"])
Q_T, Q_CR, Q_VA, Q_LO = NS, NS + 1, NS + 1 + N, NS + 1 + 2 * N
W_NAMES = ["eta", "hoff1", "lon1", "loff1"] + [f"{e}{k}" for k in range(2, N + 1) for e in ("loff", "hon", "hoff", "lon")]
NW = len(W_NAMES)
SLOPE_LOW = -1.0 / Circuit().L * 1e-9          # A/ns: -Vo/L at Vo = 1 V, phase current slope with the low side on
LSB = 0.03125                                   # ns: T_clk / 2^FB = 4 ns / 128


def core_edges(p):
    """q(p) for one cycle with per-phase on-times and slots (module docstring)."""
    c = pcl._CTX
    p = np.asarray(p, float)
    s, d, dl = p[:NS], p[I_D:I_D + N] * 1e-9, p[I_DL:I_DL + N] * 1e-9
    ton, sl, u = p[I_TON:I_TON + N] * 1e-9, p[I_SL:I_SL + N - 1] * 1e-9, p[I_U]
    t0, tb = c["t0_base"] * 1e-9, c["ton_base"] * 1e-9
    ctl = ControlLP(ton=tb, i_target=c["target"] + u, d_high=tuple(d), t_restart_high=T_RS, d_low=tuple(dl), t0=t0,
                    ton_offset=tuple(x - tb for x in ton),
                    slot_offset=(0.0,) + tuple(x - k * t0 / N for k, x in zip(range(1, N), sl)))
    emap = LowPredEventMap(Circuit(), ctl, coss=c["coss"], vf=c["vf"], r_dev=c["r_dev"])
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


def steps_edges(p0, scale=1.0):
    """Central-difference steps as D52's: 1e-5 relative for the section, 1 ps for every time, 1 mA for u."""
    h = np.empty(len(p0))
    h[:NS] = 1e-5 * np.maximum(1.0, np.abs(p0[:NS]))
    h[NS:] = 1e-3
    return h * scale


def p0_of(rec, t0_ns):
    """The per-edge input vector at an orbit record (D50/D51 diagnostics JSON)."""
    ton = rec["ton_ns"]
    return np.concatenate([rec["section_free"], rec["d_ns"], rec["d_low_ns"], [ton] * N,
                           [k * t0_ns / N for k in range(1, N)], [0.0]])


def edge_jacobian(rec, t0_ns, coss_factory, pct, vf, r_dev, jobs=4, scale=1.0):
    p0 = p0_of(rec, t0_ns)
    q0, J, curv = pcl.core_jacobian(p0, coss_factory, pct, vf, r_dev, jobs=jobs, scale=scale, func=core_edges,
                                    step_fn=steps_edges, extra={"t0_base": t0_ns, "ton_base": rec["ton_ns"]})
    return p0, q0, J, curv


def jitter_map():
    """(Gw, Gprev): the input deviations Delta p (rows P_NAMES) from this cycle's 16 jitters (columns W_NAMES) and
    from eta(n-1), all in ns (u in A)."""
    Gw, Gp = np.zeros((NP, NW)), np.zeros(NP)
    w = {n: j for j, n in enumerate(W_NAMES)}
    Gw[I_D + 0, w["eta"]] = 1.0; Gw[I_D + 0, w["loff1"]] = -1.0
    Gw[I_TON + 0, w["hoff1"]] = 1.0; Gp[I_TON + 0] = -1.0
    Gw[I_DL + 0, w["lon1"]] = 1.0; Gw[I_DL + 0, w["hoff1"]] = -1.0
    Gw[I_U, w["loff1"]] = SLOPE_LOW
    for k in range(2, N + 1):
        j = k - 1
        Gw[I_SL + j - 1, w[f"loff{k}"]] = 1.0; Gp[I_SL + j - 1] = -1.0
        Gw[I_D + j, w[f"hon{k}"]] = 1.0; Gw[I_D + j, w[f"loff{k}"]] = -1.0
        Gw[I_TON + j, w[f"hoff{k}"]] = 1.0; Gw[I_TON + j, w[f"hon{k}"]] = -1.0
        Gw[I_DL + j, w[f"lon{k}"]] = 1.0; Gw[I_DL + j, w[f"hoff{k}"]] = -1.0
    return Gw, Gp


Y_NAMES = ([f"ilo{k}" for k in range(1, N + 1)] + ["T"] + [f"eh{k}" for k in range(1, N + 1)]
           + [f"el{k}" for k in range(1, N + 1)] + [f"valley{k}" for k in range(1, N + 1)]
           + [f"isec{k}" for k in range(1, N + 1)])


def linear_loop(J, rule, g=0.5, ki_ns_per_v=0.25):
    """(A, Bw, Bu, C, Dw, Du): z(n+1) = A z + Bw w + Bu u_trim, y = C z + Dw w + Du u_trim, with
    z = (Delta s, Delta d, Delta dl, Delta acc, slot memory, eta(n-1)) and y as Y_NAMES (Delta isec_k: the section
    current at the start of the cycle)."""
    m = {"fixed": 0, "follow": 1, "avg": 2}[rule]
    iz_d, iz_dl, iz_acc, iz_mem = NS, NS + N, NS + 2 * N, NS + 2 * N + 1
    iz_eta = iz_mem + m
    nz = iz_eta + 1
    Pz = np.zeros((NP, nz))
    Pz[:NS, :NS] = np.eye(NS)
    Pz[I_D:I_D + N, iz_d:iz_d + N] = np.eye(N)
    Pz[I_DL:I_DL + N, iz_dl:iz_dl + N] = np.eye(N)
    Pz[I_TON:I_TON + N, iz_acc] = 1.0
    Pz[I_TON:I_TON + N, pcl.I_OUT] = -ki_ns_per_v
    for j in range(1, N):
        if rule == "follow":
            Pz[I_SL + j - 1, iz_mem] = j / N
        elif rule == "avg":
            Pz[I_SL + j - 1, iz_mem] = Pz[I_SL + j - 1, iz_mem + 1] = j / (2 * N)
    ton_cmd = Pz[I_TON].copy()                             # the commanded Ton: acc - ki dVo, no jitter
    Gw, Gp = jitter_map()
    Pz[:, iz_eta] += Gp
    eu = np.zeros(NP); eu[I_U] = 1.0
    Qz, Qw, Qu = J @ Pz, J @ Gw, J @ eu
    A = np.zeros((nz, nz)); Bw = np.zeros((nz, NW)); Bu = np.zeros(nz)
    A[:NS], Bw[:NS], Bu[:NS] = Qz[:NS], Qw[:NS], Qu[:NS]
    # correctors: d' = d - g (d_eff - valley - e), d_eff = Pz/Gw rows of d (commanded plus jitter)
    for blk, i_p, i_q in ((iz_d, I_D, Q_VA), (iz_dl, I_DL, Q_CR)):
        A[blk:blk + N] = Pz[i_p:i_p + N] - g * (Pz[i_p:i_p + N] - Qz[i_q:i_q + N])
        Bw[blk:blk + N] = -g * (Gw[i_p:i_p + N] - Qw[i_q:i_q + N])
        Bu[blk:blk + N] = g * Qu[i_q:i_q + N]
    A[iz_acc] = ton_cmd                                    # acc' = the commanded Ton
    w_eta = W_NAMES.index("eta")
    if m >= 1:                                             # measured period T - eta(n) + eta(n-1)
        A[iz_mem] = Qz[Q_T]; A[iz_mem, iz_eta] += 1.0
        Bw[iz_mem] = Qw[Q_T]; Bw[iz_mem, w_eta] -= 1.0
        Bu[iz_mem] = Qu[Q_T]
    if m == 2:
        A[iz_mem + 1, iz_mem] = 1.0
    Bw[iz_eta, w_eta] = 1.0
    Ez = np.zeros((NS, nz)); Ez[:, :NS] = np.eye(NS)
    C = np.vstack([Qz[Q_LO:Q_LO + N], Qz[Q_T:Q_T + 1], Pz[I_D:I_D + N] - Qz[Q_VA:Q_VA + N],
                   Pz[I_DL:I_DL + N] - Qz[Q_CR:Q_CR + N], Qz[Q_VA:Q_VA + N], Ez[N:2 * N]])
    Dw = np.vstack([Qw[Q_LO:Q_LO + N], Qw[Q_T:Q_T + 1], Gw[I_D:I_D + N] - Qw[Q_VA:Q_VA + N],
                    Gw[I_DL:I_DL + N] - Qw[Q_CR:Q_CR + N], Qw[Q_VA:Q_VA + N], np.zeros((N, NW))])
    Du = np.concatenate([Qu[Q_LO:Q_LO + N], [Qu[Q_T]], -Qu[Q_VA:Q_VA + N], -Qu[Q_CR:Q_CR + N], Qu[Q_VA:Q_VA + N],
                         np.zeros(N)])
    return A, Bw, Bu, C, Dw, Du


def covariance(A, Bw, C, Dw, sigma_ns, inputs=None):
    """Stationary output standard deviations for white edge jitter of sigma_ns on the inputs listed (all if None)."""
    sel = np.zeros(NW, bool)
    sel[[W_NAMES.index(x) for x in (inputs or W_NAMES)]] = True
    Bs, Ds = Bw[:, sel] * sigma_ns, Dw[:, sel] * sigma_ns
    P = solve_discrete_lyapunov(A, Bs @ Bs.T)
    return np.sqrt(np.maximum(np.diag(C @ P @ C.T + Ds @ Ds.T), 0.0))


def monte_carlo(p0, q0, J, rule, sigma_ns, n_cycles=20000, warmup=3000, seed=1, jitter_inputs=None,
                dt_step=6, dtl_step=2, tgt=3, shift=1, dt_max=1114, dtl_max=320, ton_ref=568, ki_code=262,
                vref_code=2000, adc_lsb_v=0.0005, trim_offset_a=0.01, trim_lsb_a=0.25):
    """Linearised circuit with the controller's exact rules (module docstring). Delays, slots, Ton and the measured
    period are integers in LSB (31.25 ps). ton_ref: the Ton code taken as the orbit's on-time; trim_offset_a: phase
    1's turn-off current above -6.25 A at the trim's upper level (A92's runs: -6.24 / -6.49 A). Returns per-cycle
    arrays after the warm-up."""
    rng = np.random.default_rng(seed)
    sel = np.ones(NW) if jitter_inputs is None else np.array([1.0 if x in jitter_inputs else 0.0 for x in W_NAMES])
    Gw, Gp = jitter_map()
    d_star, dl_star = p0[I_D:I_D + N], p0[I_DL:I_DL + N]
    slot_star, t_star = p0[I_SL:I_SL + N - 1], q0[Q_T]
    d = np.rint(d_star / LSB).astype(int); dl = np.rint(dl_star / LSB).astype(int)
    acc, trim, eta_prev = ton_ref << 16, 0, 0.0
    tm = [int(round(t_star / LSB))] * 2
    ds = np.zeros(NS)
    keys = ("ilo", "T", "eh", "el", "early_h", "early_l", "valley", "cross", "isec", "ton", "d", "dl", "vo")
    rec = {k: [] for k in keys}
    for n in range(warmup + n_cycles):
        vo = 1.0 + ds[pcl.I_OUT]
        adc = min(max(int(round(vo / adc_lsb_v)), 0), 4095)
        acc = acc + ki_code * (vref_code - adc)
        ton = (acc + (1 << 15)) >> 16
        if rule == "fixed":
            slot = [1600 * j for j in range(1, N)]
        elif rule == "follow":
            slot = [(j * tm[0]) // N for j in range(1, N)]
        else:
            slot = [(j * (tm[0] + tm[1])) // (2 * N) for j in range(1, N)]
        w = rng.normal(0.0, sigma_ns, NW) * sel
        dp = Gw @ w + Gp * eta_prev
        dp[:NS] += ds
        dp[I_D:I_D + N] += d * LSB - d_star
        dp[I_DL:I_DL + N] += dl * LSB - dl_star
        dp[I_TON:I_TON + N] += (ton - ton_ref) * LSB
        dp[I_SL:I_SL + N - 1] += np.array(slot) * LSB - slot_star
        dp[I_U] += trim * trim_lsb_a + trim_offset_a
        q = q0 + J @ dp
        valley, cross = q[Q_VA:Q_VA + N], q[Q_CR:Q_CR + N]
        eh = d_star + dp[I_D:I_D + N] - valley
        el = dl_star + dp[I_DL:I_DL + N] - cross
        if n >= warmup:
            for k, v in (("ilo", q[Q_LO:Q_LO + N]), ("T", q[Q_T]), ("eh", eh), ("el", el), ("early_h", eh < 0),
                         ("early_l", el < 0), ("valley", valley), ("cross", cross), ("isec", ds[N:NS].copy()),
                         ("ton", ton), ("d", d.copy()), ("dl", dl.copy()), ("vo", vo)):
                rec[k].append(v)
        for k in range(N):                                  # high side (rtl/scb_phase.v, bridge.py meas_m)
            if eh[k] < 0:
                d[k] = min(d[k] + dt_step, dt_max)
            else:
                err = max(0, int(round(eh[k] / LSB)))
                d[k] = min(max(d[k] - ((err - tgt) >> shift), 0), dt_max)
            if el[k] < 0:                                   # low side (meas_l)
                dl[k] = min(dl[k] + dtl_step, dtl_max)
            else:
                err = max(0, int(round(el[k] / LSB)))
                dl[k] = min(max(dl[k] - ((err - tgt) >> shift), 0), dtl_max)
        trim += 1 if q[Q_LO] < -6.25 else -1                # i_target + u: below the target -> +1
        tm = [int(round((t_star + (q[Q_T] - t_star) - w[0] + eta_prev) / LSB)), tm[0]]
        eta_prev = w[0]
        ds = q[:NS] - p0[:NS]                               # the circuit's deviation at the next section
    out = {k: np.array(v) for k, v in rec.items()}
    out["isec"] = out["isec"] + np.asarray(p0[N:NS])
    return out


def two_cycle(x):
    """A93's measure on a series: half the absolute mean of the alternating differences."""
    x = np.asarray(x, float)
    s = np.where(np.arange(len(x) - 1) % 2 == 0, 1.0, -1.0)
    return float(abs(np.mean((x[1:] - x[:-1]) * s)) / 2)


def windowed_dither(isec, win=20):
    """A89's dither metric (largest |i_k(section) - i_k(last section)| over a window of 20 sections), per window."""
    out = []
    for a in range(0, len(isec) - win + 1, win):
        blk = isec[a:a + win]
        out.append(float(np.max(np.abs(blk - blk[-1]))))
    return np.array(out)


def mc_stats(r, window=200):
    """Statistics of a Monte Carlo record: over all cycles, and the spread of 200-cycle-window values (the
    co-simulation's records hold the last 200-250 cycles)."""
    ilo = r["ilo"]
    nwin = len(ilo) // window
    win_sd = np.array([ilo[a * window:(a + 1) * window].std(axis=0) for a in range(nwin)])
    eh_ok = np.where(r["early_h"], np.nan, r["eh"])
    el_ok = np.where(r["early_l"], np.nan, r["el"])
    dith = windowed_dither(r["isec"])
    return {"ilo_sd_a": ilo.std(axis=0).tolist(),
            "ilo_sd_200_window_p5_p50_p95": np.percentile(win_sd, [5, 50, 95], axis=0).tolist(),
            "ilo_two_cycle_a": [two_cycle(ilo[-window:, k]) for k in range(N)],
            "early_high_frac": r["early_h"].mean(axis=0).tolist(), "early_low_frac": r["early_l"].mean(axis=0).tolist(),
            "eh_mean_sd_ns": [[float(np.nanmean(eh_ok[:, k])), float(np.nanstd(eh_ok[:, k]))] for k in range(N)],
            "el_mean_sd_ns": [[float(np.nanmean(el_ok[:, k])), float(np.nanstd(el_ok[:, k]))] for k in range(N)],
            "valley_sd_ns": np.nanstd(np.where(r["early_h"], np.nan, r["valley"]), axis=0).tolist(),
            "valley_sd_all_ns": r["valley"].std(axis=0).tolist(), "period_sd_ns": float(r["T"].std()),
            "dither_window_mean_sd_a": [float(dith.mean()), float(dith.std())],
            "ton_codes": {int(k): int(v) for k, v in zip(*np.unique(r["ton"], return_counts=True))},
            "vo_mean_sd_v": [float(r["vo"].mean()), float(r["vo"].std())]}
