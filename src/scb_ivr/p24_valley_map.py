"""D63: the P24 module's cycle-by-cycle valley map - how far each phase's valley (low-side turn-off current) moves in
a transient, against D57's zero-voltage threshold.

D60 assumes boundary conduction: every valley at the target. The co-simulation's breakdowns (A112 25%, A115, A116)
start when a valley moves past the threshold I_th, where the node clamps at the rail and the predictive high-side
turn-on loses its target. D63 keeps the valleys as states. One step is one phase-1 period:
- the loop: D59's sampled PI on Ton (ADC sample of Vo at phase 1's turn-on), Ton quantised to the LSB, clamped to
  [ton_min, ton_max]; every phase on in the period uses it, phase 1 included (scb_phase's turn-off compares with the
  live ton: the new value arrives within phase 1's on-time);
- rails from the series capacitors: V_rail,1 = Vin - V_1, V_rail,k = V_(k-1) - V_k, V_rail,N = V_(N-1);
- each phase starts its high side from its previous valley v: at ~0 A when -v <= I_th(rail) (the valley turn-on).
  When v >= 0 the node falls and the low side's reverse conduction (v_rev) ramps the current down at (Vo + v_rev) / L
  until the predictive turn-on at t_tr, which is hard: it starts at max(0, v - (Vo + v_rev) t_tr / L). When -v > I_th (the crossing, its depth -v - I_th) the node reaches the rail early, at
  t_reach = (2 t_tr / pi) asin(I_th / -v) (the LC swing whose valley time is t_tr), with -sqrt(v^2 - I_th^2) left; the
  high side's reverse conduction (v_rev) then ramps the current up at (V_rail + v_rev - Vo) / L until the predictive
  turn-on at t_tr, so the high side starts at min(0, that): the memory, which carries the crossing into the next
  period only when the crossing is deep;
  the rise and fall are linear-R segments di/dt = (V - R i) / L, V = V_rail - Vo and -Vo;
- phase 1's low side turns off at the target (comparator, I1; the restart timer rs_low caps it), or after the learned
  interval dlo (timed, I2), which steps by the crossing report (+ when early, - when late) with A100's adaptive step
  (doubling while decisions agree, up to smax LSB); or (floor, a proposal) at the earlier of the timed edge and the
  current reaching i_tgt - floor_a, so phase 1's valley cannot pass the floor (dlo then takes the floor's interval;
  scb_phase keeps dlo and only steps it, floor_keeps_dlo, A148);
- phases 2-4 turn off on their slots, t_lo1 + (k - 1) T_avg / N (C02's slot_lo; T_avg the mean of phase 1's last two
  periods), so their period is phase 1's plus (k - 1)/N of the change of T_avg;
- the output: Co with the resistive load (exact RC step) and an optional current step; the ladder: Cs dV_k =
  Q_on,k - Q_on,k+1 per period; the input: a linear ramp (A106's line steps);
- (A148, optional) each turn-on's V_DS from D57's free node at t_tr after the low-side turn-off, tabulated against
  the valley and the rail (von_table); a positive valley leaves V_DS near rail + v_rev (the low side's reverse
  conduction), and phase 1's timed edge can take an offset lo_add that is not learned;
- (A149, optional) each high side SH_k (k >= 2) rings to its blocking voltage rail_(k-1) + rail_k plus f(V_DS at phase
  k-1's turn-on): A144's mechanism B, f tabulated per loop inductance and edge rate from the cosim (Design.sh).
The transitions take t_tr (high side, D57's valley time) and t_dn (low side). What the map does not model: the
controller's timing after a crossing (it reports the crossing's depth and duration, the trigger), the comparator's
delay and trim (phase 1 at the target), the driver.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

LSB = 4e-9 / 128
DIVERGED_A = 1000.0


@dataclass(frozen=True)
class Design:
    lf: float = 7.3333333e-9
    cs: float = 15e-6
    co: float = 4.672e-3
    r: float = 0.54e-3
    r_load: float = 4e-3
    vin: float = 48.0
    n: int = 4
    vref: float = 1.0
    i_tgt: float = -12.5
    mode: str = "cmp"                 # "cmp" (I1), "timed" (I2) or "floor" (I2 with a comparator floor at i_tgt - floor_a)
    floor_a: float = 2.0
    kp_ns: float = 574.46
    ki_ns: float = 47.9264
    adc_lsb: float = 0.5e-3
    ton_cfg_ns: float = 88.75         # mode S Ton: the clamps are 0.5x and 2x
    smax: int = 160
    lo_tgt_ps: float = 93.75
    rs_low_ns: float = 2000.0
    t_tr: tuple = (16.9e-9, 16.9e-9, 16.9e-9, 16.9e-9)
    t_dn: float = 1.26e-9
    v_rev: float = 2.0                # the high side's reverse drop at the clamp (A88 plant: -2.1 to -2.2 V at turn-on)
    ith: tuple = field(default=None)  # (rails, I_th phases 1-3, I_th phase 4): D57 on a grid, see thresholds()
    von: tuple = field(default=None)  # A148: (currents, rails, V_DS phases 1-3, phase 4) at the turn-on, see von_table()
    floor_keeps_dlo: bool = False     # A148: a floor turn-off leaves dlo to the report's step (as scb_phase does)
    sh: tuple = field(default=None)   # A149: (V_DS grid, excess) of the SH_k overshoot block; needs von


def seg_end(v, r, lf, i0, t):
    """Current after t on di/dt = (v - r i) / lf from i0, and the charge (r = 0: the linear ramp)."""
    if r == 0:
        return i0 + v * t / lf, i0 * t + 0.5 * v * t * t / lf
    a = math.exp(-r * t / lf)
    i1 = v / r - (v / r - i0) * a
    return i1, (v * t - lf * (i1 - i0)) / r


def seg_time(v, r, lf, i0, i1):
    """Time (>= 0) for the current on di/dt = (v - r i) / lf to go from i0 to i1; math.inf when it never gets there
    in the future (i1 behind i0 in the direction of motion, or at / past the asymptote v / r). A comparator that is
    already past its level fires at once: the caller handles that case (D81)."""
    if r == 0:
        t = lf * (i1 - i0) / v if v != 0 else (0.0 if i1 == i0 else math.inf)
        return t if t >= 0 else math.inf
    if v - r * i1 == 0:                            # the target is the asymptote: reached only if already there
        return 0.0 if i1 == i0 else math.inf
    x = (v - r * i0) / (v - r * i1)
    return (lf / r) * math.log(x) if x >= 1 else math.inf


def _level_time(v, r, lf, i0, level):
    """A falling current's comparator (i <= level): 0 when it is already at or below the level, else seg_time."""
    return 0.0 if i0 <= level else seg_time(v, r, lf, i0, level)


def thresholds(lf, rails=np.arange(8.0, 17.01, 0.5)):
    """D57's zero-voltage threshold (A) against the rail, phase 1's node (2 + 3 devices and the next phase's 2) and
    phase 4's (no next phase), for Design.ith."""
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import required_i_neg
    e = EdgeCircuit()
    k = e.dv_cs / e.v_rail
    t13 = [required_i_neg(replace(e, lf=lf, v_rail=float(v), dv_cs=float(v) * k)) for v in rails]
    t4 = [required_i_neg(replace(e, lf=lf, v_rail=float(v), dv_cs=0.0, n_next=0)) for v in rails]
    return tuple(float(x) for x in rails), tuple(t13), tuple(t4)


def von_point(lf, rail, i_off, t_on, last=False):
    """V_DS of the high side t_on after the low side's turn-off at i_off (A, + into the inductor): D57's free node
    (EPC2067 Coss, the low side's and high side's reverse conduction) with no turn-on; rail - x(t_on)."""
    from scipy.integrate import solve_ivp
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import node_model
    e = EdgeCircuit()
    k = e.dv_cs / e.v_rail
    m = node_model(replace(e, lf=lf, v_rail=float(rail), dv_cs=0.0 if last else float(rail) * k, n_next=0 if last else e.n_next))
    s = solve_ivp(m._rhs_free(None), (0.0, t_on), [0.0, float(i_off), 0.0], max_step=2e-12, rtol=1e-9, atol=1e-7)
    return float(rail - s.y[0, -1])


def _von_row(args):
    lf, rail, t_on, last, cur = args
    return [von_point(lf, rail, i, t_on, last) for i in cur]


def von_table(lf, t_tr, currents=np.arange(-45.0, 30.01, 1.0), rails=np.arange(6.0, 22.01, 0.5), jobs=1):
    """A148: Design.von, turn-on V_DS against (low-side turn-off current, rail) at the predictive turn-on t_tr[k] (D57's
    valley time; the RTL learns dt_pred to it) for phases 1-3 (node as thresholds()) and phase 4 (no next phase)."""
    cur = [float(x) for x in currents]
    tasks = [(lf, float(v), t_tr[0], False, cur) for v in rails] + [(lf, float(v), t_tr[-1], True, cur) for v in rails]
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs) as p:
            rows = p.map(_von_row, tasks)
    else:
        rows = [_von_row(t) for t in tasks]
    n = len(rails)
    return tuple(cur), tuple(float(v) for v in rails), tuple(map(tuple, rows[:n])), tuple(map(tuple, rows[n:]))


def _bilinear(xs, ys, tab, x, y):
    """tab[j][i] at (xs[i], ys[j]), uniform grids, clamped at the edges."""
    fx = min(max((x - xs[0]) / (xs[1] - xs[0]), 0.0), len(xs) - 1.000001)
    fy = min(max((y - ys[0]) / (ys[1] - ys[0]), 0.0), len(ys) - 1.000001)
    i, j = int(fx), int(fy)
    a, b = fx - i, fy - j
    return ((1 - a) * (1 - b) * tab[j][i] + a * (1 - b) * tab[j][i + 1] + (1 - a) * b * tab[j + 1][i]
            + a * b * tab[j + 1][i + 1])


class ValleyMap:
    def __init__(self, d: Design):
        self.d = d
        self.ton_min, self.ton_max = 0.5 * d.ton_cfg_ns * 1e-9, 2.0 * d.ton_cfg_ns * 1e-9
        rails, t13, t4 = d.ith
        self._ith = (np.array(rails), np.array(t13), np.array(t4))

    def ith(self, k, rail):
        rails, t13, t4 = self._ith
        return float(np.interp(rail, rails, t4 if k == self.d.n - 1 else t13))

    def init_state(self, ton):
        d = self.d
        n = d.n
        return {"vo": d.vref, "vc": [d.vin * (n - j) / n for j in range(1, n)], "acc": ton, "ton_ph1": ton,
                "valley": [d.i_tgt] * n, "dlo": None, "step": 1, "last_up": None, "t_hist": [None, None], "t": 0.0}

    def period(self, s, vin, i_step, rule=None, ton_scale=None, ton_cap=None, lo_add=None):
        """One phase-1 period from state s (updated in place). Returns the record. rule ("cmp", "timed", "floor")
        overrides the design's turn-off rule for this period (A122's agent); after a comparator period dlo takes its
        on-low interval, as the RTL's learning does. ton_scale (one factor per phase) scales each phase's Ton after
        the loop, and ton_cap (one per phase, s) caps it, both quantised to the LSB (A126's feed-forward); None
        leaves every phase on the loop's Ton. lo_add (A148; s, or a function of phase 1's Ton in s) moves phase 1's
        timed edge to dlo + lo_add without entering dlo: dlo then moves only by the report's step (a floor turn-off
        does not overwrite it).
        With d.von the record has "von", each phase's turn-on V_DS (D57 at its rail and previous valley); with d.sh
        too, "sh": SH_2..SH_N's peak V_DS, rail_(k-1) + rail_k + f(von of phase k-1), f interpolated in d.sh."""
        d, n = self.d, self.d.n
        mode = rule or d.mode
        code = round(s["vo"] / d.adc_lsb)
        e = d.vref - code * d.adc_lsb
        s["acc"] = min(max(s["acc"] + d.ki_ns * 1e-9 * e, self.ton_min), self.ton_max)
        ton_new = min(max(s["acc"] + d.kp_ns * 1e-9 * e, self.ton_min), self.ton_max)
        ton_new = round(ton_new / LSB) * LSB
        rails = [vin - s["vc"][0]] + [s["vc"][j - 1] - s["vc"][j] for j in range(1, n - 1)] + [s["vc"][-1]]
        rails_tab = self._ith[0]
        vo, v_prev = s["vo"], s["valley"]
        pk, q_on, q_tot, i_on, depth = [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n
        tons = [ton_new] * n
        if ton_scale is not None or ton_cap is not None:
            sc, cap = ton_scale or [1.0] * n, ton_cap or [math.inf] * n
            tons = [max(round(min(ton_new * f, c) / LSB), 0) * LSB for f, c in zip(sc, cap)]
        for k in range(n):
            v, th = s["valley"][k], self.ith(k, rails[k])
            if v >= 0:
                i0 = max(0.0, v - (vo + d.v_rev) / d.lf * d.t_tr[k])
            elif -v <= th:
                i0 = 0.0
            else:
                t_reach = 2 * d.t_tr[k] / math.pi * math.asin(th / -v)
                i0 = min(0.0, -math.sqrt(v * v - th * th) + (rails[k] + d.v_rev - vo) / d.lf * (d.t_tr[k] - t_reach))
                depth[k] = -v - th
            i_on[k] = i0
            pk[k], q_on[k] = seg_end(rails[k] - vo, d.r, d.lf, i0, tons[k])
            q_tot[k] = q_on[k] + 0.5 * (v + i0) * d.t_tr[k] + pk[k] * d.t_dn
        # phase 1's low side
        flags = set()
        if any(not rails_tab[0] <= x <= rails_tab[-1] for x in rails):
            flags.add("ith_rail")                  # I_th clamped at the table's end (thresholds() grid)
        if pk[0] <= d.i_tgt:
            flags.add("past_level")                # phase 1 is at / below its turn-off level when its high side ends
        if mode == "cmp":
            t_ls1 = _level_time(-vo, d.r, d.lf, pk[0], d.i_tgt)
            t_ls1 = min(t_ls1, d.rs_low_ns * 1e-9)
            if rule is not None:
                s["dlo"] = t_ls1
        else:
            if s["dlo"] is None:
                s["dlo"] = _level_time(-vo, d.r, d.lf, pk[0], d.i_tgt)
            t_ls1 = base = s["dlo"]
            if lo_add is not None:
                add = lo_add(tons[0]) if callable(lo_add) else lo_add
                t_ls1 = max(t_ls1 + add, 0.0)
            if mode == "floor":
                t_ls1 = min(t_ls1, _level_time(-vo, d.r, d.lf, pk[0], d.i_tgt - d.floor_a))
        v1, q_ls1 = seg_end(-vo, d.r, d.lf, pk[0], t_ls1)
        if mode in ("timed", "floor"):             # the crossing report steps dlo (A100's adaptive step)
            t_cross = _level_time(-vo, d.r, d.lf, pk[0], d.i_tgt)
            up = (v1 > d.i_tgt) or (t_ls1 - t_cross < d.lo_tgt_ps * 1e-12)
            s["step"] = min(2 * s["step"], d.smax) if (s["last_up"] is not None and up == s["last_up"]) else 1
            s["last_up"] = up
            keep = lo_add is not None or d.floor_keeps_dlo
            s["dlo"] = (base if keep else t_ls1) + (1 if up else -1) * s["step"] * LSB
        t1 = d.t_tr[0] + tons[0] + d.t_dn + t_ls1
        th_ = s["t_hist"]
        t_avg_prev = (th_[0] + th_[1]) / 2 if th_[1] is not None else t1
        th_ = [t1, th_[0] if th_[0] is not None else t1]
        s["t_hist"] = th_
        t_avg = (th_[0] + th_[1]) / 2
        valleys, periods = [v1], [t1]
        q_tot[0] += q_ls1
        late = [False] * n
        for k in range(1, n):
            p_k = t1 + k / n * (t_avg - t_avg_prev)
            t_ls = p_k - d.t_tr[k] - tons[k] - d.t_dn
            if t_ls <= 0:
                late[k] = True
                t_ls = 0.0
            vk, q_ls = seg_end(-vo, d.r, d.lf, pk[k], t_ls)
            valleys.append(vk); periods.append(p_k); q_tot[k] += q_ls
        i_sum = sum(q_tot[k] / periods[k] for k in range(n))
        tau = d.r_load * d.co
        target = (i_sum - i_step) * d.r_load
        s["vo"] = target + (vo - target) * math.exp(-t1 / tau)
        for j in range(n - 1):
            s["vc"][j] += (q_on[j] - q_on[j + 1]) / d.cs
        s["valley"] = valleys
        s["ton_ph1"] = ton_new
        rec = {"t": s["t"], "vo": vo, "ton": ton_new, "valley": list(valleys), "peak": list(pk), "i_on": list(i_on),
               "depth": list(depth), "rails": rails, "period": t1, "late": late}
        if d.von is not None:
            cur, rv, t13, t4 = d.von
            rec["von"] = [_bilinear(cur, rv, t4 if k == n - 1 else t13, v_prev[k], rails[k]) for k in range(n)]
            rec["tons"] = list(tons)
            if any(not (cur[0] <= v_prev[k] <= cur[-1] and rv[0] <= rails[k] <= rv[-1]) for k in range(n)):
                flags.add("von_grid")
            if d.sh is not None:
                g, x = d.sh
                rec["sh"] = [rails[k - 1] + rails[k] + float(np.interp(rec["von"][k - 1], g, x)) for k in range(1, n)]
                if any(not g[0] <= v <= g[-1] for v in rec["von"][:-1]):
                    flags.add("sh_grid")
        rec["flags"] = sorted(flags)
        s["t"] += t1
        return rec


def steady_ton(d: Design, vin=None):
    """The boundary-mode Ton (s) at which the cycle-average phase current is vref / (r_load n): from 0 A to the peak,
    down to the target, the valley transition and t_dn (the map's own segments). Bisection on [1 ns, 1 us]; raises
    ValueError when the interval does not bracket a root or the result's current error exceeds 1e-6 of i_ph (D81)."""
    vin = d.vin if vin is None else vin
    i_ph = d.vref / d.r_load / d.n

    def excess(ton):
        pk, q_on = seg_end(vin / d.n - d.vref, d.r, d.lf, 0.0, ton)
        t_ls = seg_time(-d.vref, d.r, d.lf, pk, d.i_tgt)
        _, q_ls = seg_end(-d.vref, d.r, d.lf, pk, t_ls)
        q = q_on + q_ls + pk * d.t_dn + 0.5 * d.i_tgt * d.t_tr[0]
        return q / (d.t_tr[0] + ton + d.t_dn + t_ls) - i_ph

    lo, hi = 1e-9, 1e-6
    if not excess(lo) < 0 < excess(hi):
        raise ValueError(f"steady_ton: [1 ns, 1 us] does not bracket a root (excess {excess(lo):.3g}, {excess(hi):.3g} A)")
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if excess(mid) < 0 else (lo, mid)
    ton = 0.5 * (lo + hi)
    if not abs(excess(ton)) <= 1e-6 * i_ph:
        raise ValueError(f"steady_ton: residual {excess(ton):.3g} A at {ton * 1e9:.4f} ns (not a root)")
    return ton


STEADY_TOL = {"vo": 1e-5, "vc": 1e-4, "valley": 1e-3, "acc": 1e-13,   # V, V, A, s: well below an ADC / Ton LSB
              "dlo": 1e-13, "t_hist": 1e-13}                           # s: the timed edge and the slot history


def steady_record(s, r):
    """The state steady_check compares after one period (state s after ValleyMap.period returned record r): the
    continuous states as lists (STEADY_TOL's keys), the Ton codes and the adaptive step's memory (step, last_up)."""
    return {"vo": [s["vo"]], "vc": list(s["vc"]), "valley": list(s["valley"]), "acc": [s["acc"]], "ton": r["ton"],
            "dlo": [0.0 if s["dlo"] is None else s["dlo"]], "t_hist": [0.0 if x is None else x for x in s["t_hist"]],
            "mem": (s["step"], s["last_up"])}


def steady_lag(hist, pmax, tol=None):
    """The smallest p <= pmax with every state of steady_record within tol and identical Ton codes and step memory
    over hist[p:] against hist[:-p]; None if there is none."""
    tol = tol or STEADY_TOL
    n = len(hist)
    for p in range(1, min(pmax, n // 2) + 1):               # every candidate compared over at least n / 2 periods
        if all(max(abs(a - b) for j in range(p, n) for a, b in zip(hist[j][k], hist[j - p][k])) <= tol[k] for k in tol) \
                and all(hist[j]["ton"] == hist[j - p]["ton"] and hist[j]["mem"] == hist[j - p]["mem"] for j in range(p, n)):
            return p
    return None


def steady_check(m: ValleyMap, s, vin, n=64, pmax=16, tol=None):
    """Whether state s is on a periodic orbit of the map (a fixed point, or the repeating pattern of a quantised limit
    cycle): runs n periods on a copy (s is not touched) and finds the smallest p <= pmax with |x_j - x_(j-p)| within
    tol on every compared state (vo, vc, valley, acc, and the control memory dlo and t_hist) and identical Ton codes
    and adaptive-step state (step, last_up) over the last n - p periods. Returns {"settled", "cycle" (p or None),
    "drift" (largest difference per state at p = 1)} (D81; the memory added 2026-10-10)."""
    import copy
    tol = tol or STEADY_TOL
    c, hist = copy.deepcopy(s), []
    for _ in range(n):
        r = m.period(c, vin, 0.0)
        hist.append(steady_record(c, r))
    drift = {k: max(abs(a - b) for j in range(1, n) for a, b in zip(hist[j][k], hist[j - 1][k])) for k in tol}
    p = steady_lag(hist, pmax, tol)
    return {"settled": p is not None, "cycle": p, "drift": drift}


def simulate(d: Design, t_end, t_step, i_step=0.0, dvin=0.0, t_slew=0.0, ton0=None, warm=None):
    """A load step i_step (A, drawn from t_step on) and/or an input step dvin over t_slew, after a warm-up: comparator
    turn-off for `warm` periods, then 200 periods of the design's own rule (for the timed design, dlo learnt from the
    last comparator-decided turn-off, as the RTL does with lo_learn). Returns the per-period records after the warm-up
    (t from 0); the first record carries "warm", steady_check() of the state the step starts from - a step from an
    unsettled state (settled False) is not a step from steady state, and metrics() reports it."""
    mw = ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(ton0 or steady_ton(d))
    warm = warm or 600
    for _ in range(warm):
        mw.period(s, d.vin, 0.0)
    m = ValleyMap(d)
    for _ in range(200):
        m.period(s, d.vin, 0.0)
    s["t"] = 0.0
    warm_rep = steady_check(m, s, d.vin)
    out = []
    while s["t"] < t_end:
        t = s["t"]
        vin = d.vin + dvin * (min(max((t - t_step) / t_slew, 0.0), 1.0) if t_slew > 0 else float(t >= t_step))
        rec = m.period(s, vin, i_step if t >= t_step else 0.0)
        out.append(rec)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in rec["valley"] + rec["peak"]):
            rec["diverged"] = True                     # past the map's validity (the controller's timing is not modelled)
            break
    if out:
        out[0]["warm"] = warm_rep
    return out


def handover(d: Design, t_end, vo0, vcs0, ton0, valley0=None):
    """Mode P from mode S's final state (A103's handover): Vo, the series capacitors and Ton as mode S left them, the
    valleys at the target unless given; the comparator turn-off (the RTL learns for lo_learn turn-offs before a timed
    one). Records from t = 0 (the handover)."""
    m = ValleyMap(replace(d, mode="cmp"))
    s = m.init_state(ton0)
    s["vo"], s["vc"] = vo0, list(vcs0)
    if valley0 is not None:
        s["valley"] = list(valley0)
    out = []
    while s["t"] < t_end:
        rec = m.period(s, d.vin, 0.0)
        out.append(rec)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in rec["valley"] + rec["peak"]):
            rec["diverged"] = True
            break
    return out


def metrics(recs, t_step, vref=1.0, band=0.01):
    """Vo's extreme after the step (mV) and the last exit from vref +/- band (us); per phase the valley range after the
    step, the deepest crossing (A) and the number of periods with a crossing; the largest peak (A). Validity (D81):
    "flag_periods", per flag the number of periods after the step that left a table or passed a comparator level
    (ValleyMap.period's rec["flags"]), with the time of the first; "warm_settled" from simulate()'s warm-up check
    (None when the records did not come from simulate)."""
    a = [r for r in recs if r["t"] >= t_step]
    vo = np.array([r["vo"] for r in a]); t = np.array([r["t"] for r in a])
    i = int(np.argmax(np.abs(vo - vref)))
    bad = np.nonzero(np.abs(vo - vref) > band * vref)[0]
    back = float((t[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0
    if len(bad) and bad[-1] == len(vo) - 1:
        back = math.inf
    n = len(a[0]["valley"])
    return {"extreme_mv": float((vo[i] - vref) * 1e3), "back_us": back,
            "valley_min_a": [min(r["valley"][k] for r in a) for k in range(n)],
            "valley_max_a": [max(r["valley"][k] for r in a) for k in range(n)],
            "depth_max_a": [max(r["depth"][k] for r in a) for k in range(n)],
            "crossing_periods": [sum(1 for r in a if r["depth"][k] > 0) for k in range(n)],
            "memory_max_a": [max(-r["i_on"][k] for r in a) for k in range(n)],
            "peak_max_a": max(max(r["peak"]) for r in a), "late": sum(sum(r["late"]) for r in a),
            "diverged_us": float((a[-1]["t"] - t_step) * 1e6) if a[-1].get("diverged") else None,
            "flag_periods": _flag_periods(a, t_step),
            "warm_settled": recs[0]["warm"]["settled"] if "warm" in recs[0] else None}


def _flag_periods(a, t_step):
    out = {}
    for r in a:
        for f in r.get("flags", ()):
            e = out.setdefault(f, {"periods": 0, "first_us": float((r["t"] - t_step) * 1e6)})
            e["periods"] += 1
    return out
