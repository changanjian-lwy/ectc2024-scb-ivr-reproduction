"""D56: the P24 high side's rising edge with an auxiliary commutation branch - a single-phase edge and cycle model.

One switch node x (phase 1 of the 5% orbit, D51) between its stiff neighbours:
    C(x) dx/dt = i_r - i_f + i_dev(x)
    C(x) = n_l Coss(x) + n_h Coss(V_rail - x) + n_h Coss(x + dV_cs)
    Lf di_f/dt = x - Vo - R i_f                      (filter inductor, current from x to the output)
    Lr di_r/dt = Vm - x - R_aux i_r                  (auxiliary branch, current from its source Vm into x)
- Coss(V) is the EPC2067 datasheet curve (A59), n_h = 2, n_l = 3 devices;
- the third term is the next phase's high side: in the series-capacitor chain its drain is this phase's capacitor
  node, so its V_DS rises with x from dV_cs = V_Cs1 - V_Cs2;
- i_dev is the reverse conduction of an off switch, n (V_SD - Vf) / R per device (A57's fit of datasheet Fig. 8).
With i_r = 0 this reproduces the full four-phase nonlinear event map's valley after phase 1's low-side turn-off
(nl_valley_after_lowoff) within 0.03 V for negative currents of 6.25-37.5 A (validation() below).

The auxiliary branch (ARCP-type, De Doncker 1990; ZVT synchronous buck, Nan and Ayyanar 2016):
- source "vo": Lr to the output through a synchronous switch, i_r >= 0 (Nan and Ayyanar's circuit, the diode
  replaced by a switch);
- source "cm": Lr to a capacitor Cm at Vm through a bidirectional switch (BDS) of two dies in common source, each
  alpha times an EPC2067 (R = 2 RDS(on) / alpha, gate charge and Coss times alpha). cycle() switches it on at the
  low-side turn-off and off when its current returns to zero after the falling edge; Cm's charge balance over the
  cycle sets Vm (balance_vm).

cycle(): from the low-side turn-off (i_f = -i_neg) - rising edge until x reaches the rail (the high side turns on at
zero voltage) or the node current reverses (it turns on at the valley); the high side conducts until i_f reaches the
baseline's peak (the voltage loop keeps the average current); the falling edge, with the low side turning on at a
fixed dead time or when x reaches x_low (the baseline's turn-on voltage); then the low side conducts while the
auxiliary current returns to zero. Loss bookkeeping in losses().
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from scb_ivr.cosim.circuit import EPC2067Coss, fit_fig8

RDS_ON = 1.3e-3          # EPC2067 datasheet, RDS(on) typical, VGS = 5 V, ID = 37 A, 25 C
QG = 17.1e-9             # EPC2067 datasheet, QG typical, VDS = 20 V, VGS = 5 V
VGATE = 5.0


@dataclass(frozen=True)
class EdgeCircuit:
    """Phase 1 at the 5% orbit (D51_orbit_5p0pct_m0p0.json): V_rail = 48 - V_Cs1, dV_cs = V_Cs1 - V_Cs2."""
    v_rail: float = 48.0 - 35.792569779918395
    dv_cs: float = 35.792569779918395 - 23.88268463001492
    vo: float = 1.0
    lf: float = 1.4666667e-9
    rl: float = 0.54e-3
    n_h: int = 2
    n_l: int = 3
    n_next: int = 2            # devices of the next phase's high side on this node (0 for the last phase)
    ton_ns: float = 17.74106765758561
    d_low_ns: float = 1.2639414679389491
    period_ns: float = 231.8838685794732


def phase_circuit(orbit: dict, phase: int, dv_prev: float = 0.0) -> EdgeCircuit:
    """EdgeCircuit of one phase from an orbit record (vcs_v at the section, ton_ns, d_low_ns, period_ns): the high
    side blocks V_Cs(k-1) - V_Cs(k) (V_Cs0 = vin = 48 V, V_CsN = 0) plus dv_prev, the rise of V_Cs(k-1) from the
    previous phase's on-time since the section; the next phase's high side, absent for the last phase, is biased at
    V_Cs(k) - V_Cs(k+1)."""
    vcs = [48.0] + list(orbit["vcs_v"]) + [0.0]
    n = len(vcs) - 1
    k = phase
    return EdgeCircuit(v_rail=vcs[k - 1] - vcs[k] + dv_prev, dv_cs=(vcs[k] - vcs[k + 1]) if k < n else 0.0,
                       n_next=2 if k < n else 0, ton_ns=orbit["ton_ns"], d_low_ns=orbit["d_low_ns"][k - 1],
                       period_ns=orbit["period_ns"])


def phase_circuits(orbit: dict, cs: float = 3e-6):
    """The four phases' EdgeCircuits in turn-on order from the section (phase 1's turn-on): phase k >= 2 sees
    V_Cs(k-1) raised by the charge through phase k-1's high side in its on-time (its baseline cycle), divided by Cs."""
    out, dv = [], 0.0
    for k in range(1, len(orbit["vcs_v"]) + 2):
        ckt = phase_circuit(orbit, k, dv)
        out.append(ckt)
        r = Model(ckt).cycle(-orbit["lowoff_i"][k - 1])
        s = [seg for name, seg in r["segments"] if name == "high"][0]
        dv = float(np.trapezoid(s.y[0] - s.y[1], s.t)) / cs
    return out


@dataclass(frozen=True)
class AuxBranch:
    lr: float                  # H
    source: str = "cm"         # "cm" (capacitor at vm, bidirectional) or "vo" (output, i_r >= 0)
    vm: float = 0.0            # V, for "cm"
    alpha: float = 0.3         # die area of each BDS device / EPC2067
    r_lr: float = 0.2e-3       # Ohm, Lr's series resistance (assumed)

    @property
    def r_bds(self):
        return 2 * RDS_ON / self.alpha

    @property
    def r_total(self):
        return self.r_bds + self.r_lr


class Model:
    def __init__(self, ckt: EdgeCircuit = EdgeCircuit()):
        self.ckt = ckt
        self.coss = EPC2067Coss()
        self.vf, self.r_rev, _ = fit_fig8()
        self.r_hs, self.r_ls = RDS_ON / ckt.n_h, RDS_ON / ckt.n_l

    # ---- node ----
    def cnode(self, x):
        k = self.ckt
        return k.n_l * self.coss.c(x) + k.n_h * self.coss.c(k.v_rail - x) + k.n_next * self.coss.c(x + k.dv_cs)

    def idev(self, x):
        k, i = self.ckt, 0.0
        if -x > self.vf:
            i += k.n_l * (-x - self.vf) / self.r_rev
        if x - k.v_rail > self.vf:
            i -= k.n_h * (x - k.v_rail - self.vf) / self.r_rev
        return i

    def eoss(self, v, n=1):
        vv = np.linspace(0.0, v, 400)
        return n * float(np.trapezoid(vv * self.coss.c(vv), vv))

    def hard_on_energy(self, x_on):
        """Channel energy of a high-side turn-on at node voltage x_on: its own Eoss(V_DS) plus the charge of the low
        side and the next high side drawn through it, int (V_rail - x) C dx (no current overlap)."""
        k = self.ckt
        v = k.v_rail - x_on
        if v <= 0:
            return 0.0
        xs = np.linspace(x_on, k.v_rail, 400)
        other = k.n_l * self.coss.c(xs) + k.n_next * self.coss.c(xs + k.dv_cs)
        return self.eoss(v, k.n_h) + float(np.trapezoid((k.v_rail - xs) * other, xs))

    def a91_bounds(self, x_on):
        """A91's bounds at the turn-on V_DS: Eoss of the high-side devices; Qoss(V) V of the five node devices."""
        k = self.ckt
        v = max(k.v_rail - x_on, 0.0)
        return self.eoss(v, k.n_h), (k.n_h + k.n_l) * float(self.coss.q(v)) * v

    # ---- dynamics ----
    def _aux_di(self, aux: AuxBranch, x, i_r):
        if aux is None:
            return 0.0
        src = self.ckt.vo if aux.source == "vo" else aux.vm
        d = (src - x - aux.r_total * i_r) / aux.lr
        if aux.source == "vo" and i_r <= 0.0 and d < 0.0:
            return 0.0
        return d

    def _rhs_free(self, aux):
        k = self.ckt

        def f(t, z):
            x, i_f, i_r = z
            return [(i_r - i_f + self.idev(x)) / self.cnode(x), (x - k.vo - k.rl * i_f) / k.lf, self._aux_di(aux, x, i_r)]
        return f

    def rising_edge(self, i_neg, aux: AuxBranch = None, i_r0=0.0, t_max=30e-9):
        """Free rising edge from the low-side turn-off. Returns (t, V_DS) at the first of: x reaches the rail (V_DS = 0,
        the high side turns on at zero voltage) or the node current reverses (the valley), and the solution."""
        k = self.ckt
        top = lambda t, z: z[0] - k.v_rail
        top.terminal, top.direction = True, 1
        rev = lambda t, z: z[1] - z[2] - self.idev(z[0])
        rev.terminal, rev.direction = True, 1
        s = solve_ivp(self._rhs_free(aux), (0, t_max), [0.0, -i_neg, i_r0], max_step=2e-12, rtol=1e-9, atol=1e-7,
                      events=[top, rev], dense_output=True)
        return s.t[-1], k.v_rail - s.y[0, -1], s

    def valley_free(self, i_neg, aux=None, i_r0=0.0, t_max=30e-9):
        """The valley of V_DS without a turn-on (x may pass the rail): (t, V_DS min). For the validation."""
        k = self.ckt
        rev = lambda t, z: z[1] - z[2] - self.idev(z[0])
        rev.terminal, rev.direction = True, 1
        s = solve_ivp(self._rhs_free(aux), (0, t_max), [0.0, -i_neg, i_r0], max_step=2e-12, rtol=1e-9, atol=1e-7,
                      events=[rev])
        j = int(np.argmax(s.y[0]))
        return s.t[j], k.v_rail - s.y[0, j]

    def min_ir_for_zvs(self, i_neg, aux: AuxBranch, hi=300.0):
        """Smallest auxiliary current at the low-side turn-off for which the free valley of V_DS reaches zero."""
        f = lambda ir: self.valley_free(i_neg, aux, ir)[1]
        if f(0.0) <= 0.0:
            return 0.0
        if f(hi) > 0.0:
            return float("nan")
        return brentq(f, 0.0, hi, xtol=0.02)

    def turn_on_timing(self, i_neg, aux: AuxBranch, deltas_ns=(0.25, 0.5, 1.0), t_max=30e-9):
        """The high side turned on early or late by delta around the instant x first reaches the rail, on the free
        trajectory: early -> hard turn-on energy at x(t_rail - delta); late -> high-side reverse conduction energy up to
        t_rail + delta plus the hard turn-on energy if x has fallen back below the rail. None if x never reaches it."""
        k = self.ckt
        s = solve_ivp(self._rhs_free(aux), (0, t_max), [0.0, -i_neg, 0.0], max_step=2e-12, rtol=1e-9, atol=1e-7,
                      dense_output=True)
        tt = np.linspace(0, t_max, 30001)
        xx = s.sol(tt)[0]
        hit = np.nonzero(xx >= k.v_rail)[0]
        if not len(hit):
            return None
        t_rail = tt[hit[0]]
        p_rev = np.array([(x - k.v_rail) * (-self.idev(x)) if x - k.v_rail > self.vf else 0.0 for x in xx])
        rows = []
        for d in deltas_ns:
            te = t_rail - d * 1e-9
            tl = t_rail + d * 1e-9
            sel = (tt >= t_rail) & (tt <= tl)
            xl = float(s.sol(tl)[0])
            rows.append({"delta_ns": d, "early_vds_v": k.v_rail - float(s.sol(te)[0]),
                         "early_e_nj": self.hard_on_energy(float(s.sol(te)[0])) * 1e9,
                         "late_e_nj": (float(np.trapezoid(p_rev[sel], tt[sel])) + self.hard_on_energy(xl)) * 1e9})
        return {"t_rail_ns": t_rail * 1e9, "rows": rows}

    def cycle(self, i_neg, aux: AuxBranch = None, i_pk=None, x_low=None, i_r0=0.0, t_bds=0.0):
        """One cycle from the low-side turn-off (see the module docstring). t_bds: the BDS turns on t_bds after the
        low-side turn-off (negative: before it, with i_r0 built through the low side - pass i_r0 accordingly).
        i_pk: the high side turns off when i_f reaches it (None: after ton_ns). x_low: the low side turns on when x
        reaches it (None: after d_low_ns)."""
        k = self.ckt
        out = {}
        f_free = self._rhs_free(aux)
        segs = []
        # A1: delayed BDS turn-on (node rises on the filter current alone)
        z0 = [0.0, -i_neg, i_r0]
        t_shift = 0.0
        if aux is not None and t_bds > 0:
            s0 = solve_ivp(self._rhs_free(None), (0, t_bds), z0, max_step=2e-12, rtol=1e-9, atol=1e-7)
            z0 = list(s0.y[:, -1]); segs.append(("rise0", s0)); t_shift = t_bds
        top = lambda t, z: z[0] - k.v_rail
        top.terminal, top.direction = True, 1
        rev = lambda t, z: z[1] - z[2] - self.idev(z[0])
        rev.terminal, rev.direction = True, 1
        sA = solve_ivp(f_free, (0, 30e-9), z0, max_step=2e-12, rtol=1e-9, atol=1e-7, events=[top, rev])
        segs.append(("rise", sA))
        xA, ifA, irA = sA.y[:, -1]
        out["t_hs_on_ns"] = (t_shift + sA.t[-1]) * 1e9
        out["vds_on"] = k.v_rail - xA
        out["e_hard_on"] = self.hard_on_energy(xA)
        out["a91_bounds"] = self.a91_bounds(xA)
        out["bds_v_on"] = (aux.vm - z0[0]) if (aux is not None and aux.source == "cm") else 0.0

        # B: high side on; x = V_rail - R_hs (i_f - i_r)
        def fB(t, z):
            i_f, i_r = z
            x = k.v_rail - self.r_hs * (i_f - i_r)
            return [(x - k.vo - k.rl * i_f) / k.lf, self._aux_di(aux, x, i_r)]
        if i_pk is None:
            sB = solve_ivp(fB, (0, k.ton_ns * 1e-9), [ifA, irA], max_step=5e-12, rtol=1e-9, atol=1e-7)
        else:
            pk = lambda t, z: z[0] - i_pk
            pk.terminal, pk.direction = True, 1
            sB = solve_ivp(fB, (0, 40e-9), [ifA, irA], max_step=5e-12, rtol=1e-9, atol=1e-7, events=pk)
        segs.append(("high", sB))
        ifB, irB = sB.y[:, -1]
        out["t_high_ns"] = sB.t[-1] * 1e9
        out["i_hs_off"] = ifB - irB
        out["ir_hs_off"] = irB
        out["int_ihs2"] = float(np.trapezoid((sB.y[0] - sB.y[1]) ** 2, sB.t))
        # C: falling edge
        xB = k.v_rail - self.r_hs * (ifB - irB)
        if x_low is None:
            sC = solve_ivp(f_free, (0, k.d_low_ns * 1e-9), [xB, ifB, irB], max_step=1e-12, rtol=1e-9, atol=1e-7)
        else:
            lo = lambda t, z: z[0] - x_low
            lo.terminal, lo.direction = True, -1
            sC = solve_ivp(f_free, (0, 10e-9), [xB, ifB, irB], max_step=1e-12, rtol=1e-9, atol=1e-7, events=lo)
        segs.append(("fall", sC))
        xC, ifC, irC = sC.y[:, -1]
        out["t_fall_ns"] = sC.t[-1] * 1e9
        out["low_on_vds"] = xC
        p_rev = np.array([(-x) * self.idev(x) if -x > self.vf else 0.0 for x in sC.y[0]])
        out["e_rev_fall"] = float(np.trapezoid(p_rev, sC.t))
        # D: low side on until the auxiliary current returns to zero
        out["int_ls2_extra"], out["t_tail_ns"], out["tail_ok"] = 0.0, 0.0, True
        if aux is not None and abs(irC) > 1e-9:
            def fD(t, z):
                i_f, i_r = z
                x = self.r_ls * (i_r - i_f)
                return [(x - k.vo - k.rl * i_f) / k.lf, self._aux_di(aux, x, i_r)]
            zero = lambda t, z: z[1]
            zero.terminal = True
            sD = solve_ivp(fD, (0, 60e-9), [ifC, irC], max_step=5e-12, rtol=1e-9, atol=1e-7, events=zero)
            segs.append(("tail", sD))
            out["int_ls2_extra"] = float(np.trapezoid((sD.y[0] - sD.y[1]) ** 2 - sD.y[0] ** 2, sD.t))
            out["t_tail_ns"] = sD.t[-1] * 1e9
            out["tail_ok"] = bool(len(sD.t_events[0]))
        q = s2 = 0.0
        ir_all, cum = [], [0.0]
        for name, s in segs:
            ir = s.y[-1] if name in ("high", "tail") else s.y[2]
            q += float(np.trapezoid(ir, s.t)); s2 += float(np.trapezoid(ir ** 2, s.t)); ir_all.append(ir)
            c = np.concatenate([[0.0], np.cumsum(0.5 * (ir[1:] + ir[:-1]) * np.diff(s.t))])
            cum.extend(list(cum[-1] + c[1:]))
        ir_all = np.concatenate(ir_all)
        out["q_aux"] = q
        out["q_excursion"] = float(max(cum) - min(cum))         # Cm's charge swing within the cycle
        out["int_ir2"] = s2
        out["ir_max"], out["ir_min"] = float(ir_all.max()), float(ir_all.min())
        out["segments"] = segs
        return out

    def balance_vm(self, i_neg, aux: AuxBranch, lo=1.0, hi=None, **kw):
        """Vm at which Cm's charge over the cycle is zero (None if not bracketed)."""
        hi = hi or self.ckt.v_rail
        f = lambda vm: self.cycle(i_neg, replace(aux, vm=vm), **kw)["q_aux"]
        a, b = f(lo), f(hi)
        if a * b > 0:
            return None
        return brentq(f, lo, hi, xtol=1e-3)


def turn_off_overlap(i_off, c_eff, t_f):
    """Channel turn-off overlap energy with a linear current fall over t_f into a capacitive node, I^2 t_f^2 / (24 C)."""
    return i_off ** 2 * t_f ** 2 / (24.0 * c_eff)


def losses(m: Model, base: dict, r: dict, aux: AuxBranch, c_eff, t_f=(0.5e-9, 1.0e-9)):
    """Per-cycle energy changes (J) of an auxiliary-branch cycle r against the baseline cycle base (same model,
    no branch). Positive = more loss."""
    e = {}
    e["hard_on_saved"] = r["e_hard_on"] - base["e_hard_on"]
    e["aux_conduction"] = r["int_ir2"] * aux.r_total
    e["hs_conduction"] = (r["int_ihs2"] - base["int_ihs2"]) * m.r_hs
    e["ls_tail_conduction"] = r["int_ls2_extra"] * m.r_ls
    e["dead_time_reverse"] = r["e_rev_fall"] - base["e_rev_fall"]
    if aux.source == "cm":
        e["bds_gate"] = 2 * aux.alpha * QG * VGATE
        e["bds_switching"] = aux.alpha * (m.eoss(abs(r["bds_v_on"])) + m.eoss(aux.vm))
    else:
        e["bds_gate"] = 2 * aux.alpha * QG * VGATE
        e["bds_switching"] = aux.alpha * m.eoss(m.ckt.v_rail - m.ckt.vo)
    lo = turn_off_overlap(r["i_hs_off"], c_eff, t_f[0]) - turn_off_overlap(base["i_hs_off"], c_eff, t_f[0])
    hi = turn_off_overlap(r["i_hs_off"], c_eff, t_f[1]) - turn_off_overlap(base["i_hs_off"], c_eff, t_f[1])
    e["turn_off_overlap_range"] = (lo, hi)
    core = sum(v for kk, v in e.items() if kk != "turn_off_overlap_range")
    e["net_without_overlap"] = core
    e["net_range"] = (core + lo, core + hi)
    return e


def validation(m: Model, reference=None):
    """The single-phase edge against the full model's valley table (nl_valley_after_lowoff, D47's 5% state)."""
    reference = reference or {6.25: 8.98, 9.375: 8.03, 12.5: 7.04, 18.75: 5.01, 25.0: 2.92, 31.25: 0.77, 37.5: -1.47}
    rows = []
    for i_neg, v_full in reference.items():
        t, v = m.valley_free(i_neg)
        rows.append({"i_neg_a": i_neg, "valley_v": v, "t_ns": t * 1e9, "full_model_v": v_full, "diff_v": v - v_full})
    return rows
