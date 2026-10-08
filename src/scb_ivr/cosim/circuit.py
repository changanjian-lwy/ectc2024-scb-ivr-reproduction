"""The P24 module circuit used by the co-simulation plant: parameters, EPC2067 device data and the implicit
modified-nodal stepper (Sim).

Circuit (N phases):
    vin-SH1-a1-SH2-a2-...-a(N-1)-SHN-xN,  SLk: xk-0,  Csk: ak-xk (k < N),  Lk: xk-out,  Co: out-0, load at out
    [Cm 0; 0 L] d/dt [v; i] = [[-G, -B], [B^T, -R]] [v; i] + f(t),  v = (a1..a(N-1), x1..xN, out), i = (i1..iN)
- conducting switches are conductances g_on; a switch that conducts only in reverse (gate off, rev_drop) carries
  n (V_SD - Vf) / R per device (EPC2067 datasheet Fig. 8 fit, A57 data);
- switch capacitances are linear (c_high, c_low) or, with nonlinear_coss, the EPC2067 datasheet Fig. 5a Coss(V)
  (A59 data): the charge change n (q(v1) - q(v0)) solved by chord iteration on the cached LU, full Newton as fallback;
  coss_scale (A132) multiplies that curve (a component spread; c_high / c_low, the chord's linear part, alike in cfg);
- one step: trapezoid, or backward Euler after a topology change; LU factors cached per topology.
- optional auxiliary branches (aux_phases, A101): per listed phase k a node m_k with aux_c to ground (after "out" in
  v) and a branch current (after the phase currents in i) through aux_l and aux_r from m_k into x_k while its
  bidirectional switch conducts; the switch states follow the 2N switches in `conducting`; an open branch is
  uncoupled with di/dt = 0. Without aux_phases every matrix is as before.
- optional commutation-loop inductance (loop_phases, A144): per listed phase k the high-side switch's drain moves to a
  node h_k (after the m_k nodes in v; its Coss c_high now between h_k and a_k / x_N) and loop_l carries a current
  (last in i) from the switch's upstream node (vin for k = 1, a(k-1) otherwise) into h_k, with loop_rp across it as
  damping (0: none); it never switches. Without loop_phases every matrix is as before.
- optional finite switching edges (edge_didt_off / edge_didt_on, A145): the plants (plant.py, not Sim) model a switch
  in an edge as open with its channel current as a source from drain to source in the right-hand side (edge_inc);
  0 = instantaneous edges, every matrix and step as before.
- optional gate-driven edges (gate_dev, A163): the listed switches' edges follow a gate model (gate.py); "" = off.

Derived from A88's a88_transient.py (Params, topology, EPC2067Coss, fit_fig8, Sim), whose arithmetic it keeps line
for line; only the parameters the co-simulation uses are kept (see CHANGELOG.md).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.linalg import lu_factor, lu_solve

PROJECT = Path(__file__).resolve().parents[3]
TRACK_A = PROJECT / "experiments" / "track_A_periodic_steady_state"
COSS_CSV = TRACK_A / "A59_nonlinear_coss_epc2067" / "epc2067_coss_qoss_eoss_digitized.csv"
FIG8_CSV = TRACK_A / "A57_datasheet_reverse_conduction_pricing" / "epc2067_fig8_reverse_characteristics.csv"


def fit_fig8(lo=10.0, hi=100.0, temp=25, path=FIG8_CSV):
    """Least-squares V_SD = Vf + R I per device over [lo, hi] A (1 A spacing) of the digitised Fig. 8 curve.
    Returns (Vf, R, max |error| over the range)."""
    pts = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if int(row["temperature_c"]) == temp:
                pts.append((float(row["isd_a_per_device"]), float(row["vsd_v"])))
    i_f, v_f = np.array(sorted(pts)).T
    cur = np.arange(lo, hi + 1e-9, 1.0)
    vol = np.interp(cur, i_f, v_f)
    r, vf = np.polyfit(cur, vol, 1)
    return float(vf), float(r), float(np.max(np.abs(vol - (vf + r * cur))))


class EPC2067Coss:
    """Per-device Coss(V) of the EPC2067 datasheet Fig. 5a (VGS = 0, typical), digitised in A59.
    PCHIP on a 0.1 V grid, tabulated at 1 mV for linear-interpolation lookup; q = antiderivative, C even and q odd
    in V; beyond v_max the v_max slope is extended (never reached here)."""

    def __init__(self, path=COSS_CSV, v_max=40.0, dv=1e-3, scale=1.0):
        from scipy.interpolate import PchipInterpolator
        pts = {}
        with open(path) as fh:
            for row in csv.DictReader(fh):
                if row["curve"] == "coss":
                    pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
        v = np.array(sorted(pts)); c = np.array([pts[x] for x in v]); keep = v > 0
        v = np.concatenate([[0.0], v[keep]]); c = np.concatenate([[c[keep][0]], c[keep]])
        grid = np.arange(0.0, v_max + 1e-9, 0.1)
        ci = PchipInterpolator(grid, np.interp(grid, v, c), extrapolate=False)
        qi = ci.antiderivative()
        self.vt = np.arange(0.0, v_max + 1e-9, dv)
        self.ct, self.qt = ci(self.vt), qi(self.vt)
        if scale != 1.0:                                       # A132: Coss spread
            self.ct, self.qt = self.ct * scale, self.qt * scale
        self.v_max, self.c_end, self.q_end = v_max, float(self.ct[-1]), float(self.qt[-1])

    def q(self, v):
        a = np.abs(v)
        out = np.interp(a, self.vt, self.qt)
        out = np.where(a > self.v_max, self.q_end + self.c_end * (a - self.v_max), out)
        return np.sign(v) * out

    def c(self, v):
        return np.interp(np.abs(v), self.vt, self.ct)


@dataclass
class CircuitParams:
    n: int = 4
    vin: float = 48.0
    L: float = 1.4666667e-9
    R: float = 0.54e-3
    c_high: float = 2 * 1860e-12
    c_low: float = 3 * 1860e-12
    cs: float = 3e-6
    co: float = 4.672e-3
    load_kind: str = "r"        # "r": resistive r_load; "cc": constant current i_load
    r_load: float = 4e-3
    i_load: float = 250.0
    g_on: float = 1e7
    h: float = 10e-12
    t_ramp: float = 68.61e-6
    t_load: float = 88.61e-6
    t_hand: float = 88.61e-6
    diode_check: bool = False
    nonlinear_coss: bool = False
    coss_scale: float = 1.0      # A132: the datasheet Coss(V) times this (nonlinear_coss only)
    n_high: int = 2              # parallel devices per high-side switch (P24 Table 3)
    n_low: int = 3               # parallel devices per low-side switch
    rev_drop: bool = False
    rev_vf: float = 0.0          # V per device, from fit_fig8 when rev_drop
    rev_r: float = 0.0           # Ohm per device, from fit_fig8 when rev_drop
    i_step: float = 0.0          # A100: a load current step drawn from the output from t_step on
    t_step: float = float("inf")
    aux_phases: tuple = ()       # A101: phases (1-based) with an auxiliary branch: Lr and a bidirectional switch (BDS)
    aux_l: float = 0.0           #   from a capacitor node m_k (aux_c to ground) to x_k; aux_r = BDS + Lr resistance
    aux_r: float = 0.0
    aux_c: float = 1e-6
    aux_vm0: float = 0.0
    vin_step: float = 0.0        # A106: the input changes by vin_step (V) from t_vstep, linearly over t_vslew (0: at once)
    t_vstep: float = float("inf")
    t_vslew: float = 0.0
    loop_phases: tuple = ()      # A144: phases (1-based) whose high-side switch has a series loop inductance loop_l
    loop_l: float = 0.0          #   (H) from its upstream node into a node h_k at the switch's drain
    loop_rp: float = 0.0         #   Ohm across loop_l (damping; 0: none)
    edge_didt_off: float = 0.0   # A145: channel current fall rate at a turn-off, A/s (0: instantaneous)
    edge_didt_on: float = 0.0    #   rise rate at a hard turn-on (V_DS > 0), A/s (0: instantaneous)
    gate_dev: str = ""           # A163: gate-driven edges with this device's model ("": off; gate.py)
    gate_switches: tuple = ()    #   switch indices (SH1..SHN = 0..N-1, SL1..SLN = N..2N-1)
    gate_r_on: float = 0.0       #   ohm per device in series with its R_G (external + driver) at turn-on
    gate_r_off: float = 0.0      #   ... at turn-off
    gate_v_on: float = 5.0       #   gate drive voltage (V; off = 0 V)
    gate_l_cs: float = 0.0       #   common-source inductance per device (H)
    gate_temp: float = 25.0      #   device temperature (deg C)
    gate_dk2: float = 0.0        #   threshold shift (V; spread case)
    gate_cg_scale: float = 1.0   #   gate capacitances times this (spread case)
    gate_v_hand: float = 0.2     #   V_DS (V) at which the channel hands over to / takes over from conduction
    gate_il: bool = False        #   A170: driver interlock (a turn-on waits until its complement stops conducting)
    gate_t_il: float = 0.0       #   ... then starts this much later (s; the interlock's propagation delay)

    def vin_at(self, t):
        v = self.vin * min(t / self.t_ramp, 1.0) if self.t_ramp > 0 else self.vin
        if self.vin_step != 0.0 and t >= self.t_vstep:                 # A106
            v += self.vin_step * (min((t - self.t_vstep) / self.t_vslew, 1.0) if self.t_vslew > 0 else 1.0)
        return v

    def load_at(self, t):
        a = self.i_load if (self.load_kind == "cc" and t >= self.t_load) else 0.0
        return a + (self.i_step if t >= self.t_step else 0.0)       # A100: + 0.0 without a step


def topology(n, loop=()):
    nodes = tuple(f"a{k}" for k in range(1, n)) + tuple(f"x{k}" for k in range(1, n + 1)) + ("out",)
    highs = [("SH1", "vin", "a1")] + [(f"SH{k}", f"a{k - 1}", f"a{k}") for k in range(2, n)] + [(f"SH{n}", f"a{n - 1}", f"x{n}")]
    highs = [(nm, f"h{k}" if k in loop else d, s) for k, (nm, d, s) in enumerate(highs, 1)]   # A144: drain behind loop_l
    lows = [(f"SL{k}", f"x{k}", None) for k in range(1, n + 1)]
    return nodes, tuple(highs + lows)


@dataclass
class Sim:
    p: CircuitParams
    cache: dict = field(default_factory=dict)

    def __post_init__(self):
        p = self.p
        self.lp = tuple(int(k) for k in p.loop_phases)            # A144: loop inductances; nodes h_k after the m_k
        nlp = len(self.lp); self.nlp = nlp
        self.nodes, self.switches = topology(p.n, self.lp)
        self.aux = tuple(int(k) for k in p.aux_phases)            # A101: the branches' phases; nodes m_k after "out"
        na = len(self.aux); self.na = na
        if na:
            self.nodes = self.nodes + tuple(f"m{k}" for k in self.aux)
        if nlp:
            self.nodes = self.nodes + tuple(f"h{k}" for k in self.lp)
        self.idx = {nm: k for k, nm in enumerate(self.nodes)}
        nv = len(self.nodes); self.nv = nv
        caps = ([(p.c_high, d, s) for _, d, s in self.switches[:p.n]] + [(p.c_low, d, s) for _, d, s in self.switches[p.n:]]
                + [(p.cs, f"a{k}", f"x{k}") for k in range(1, p.n)] + [(p.co, "out", None)])
        if na:
            caps += [(p.aux_c, f"m{k}", None) for k in self.aux]
        cm = np.zeros((nv, nv))
        for c, a, b in caps:
            ia, ib = self.idx.get(a), self.idx.get(b)
            if ia is not None:
                cm[ia, ia] += c
            if ib is not None:
                cm[ib, ib] += c
            if ia is not None and ib is not None:
                cm[ia, ib] -= c; cm[ib, ia] -= c
        ns = nv + p.n + na + nlp; self.ns = ns                   # state: node voltages, phase, branch, loop currents
        self.M = np.zeros((ns, ns)); self.M[:nv, :nv] = cm; self.M[nv:nv + p.n, nv:nv + p.n] = p.L * np.eye(p.n)
        self.B = np.zeros((nv, p.n))
        for k in range(p.n):
            self.B[self.idx[f"x{k + 1}"], k] = 1.0; self.B[self.idx["out"], k] = -1.0
        if na:                                                 # A101: branch a carries current from m_k into x_k
            self.M[nv + p.n:, nv + p.n:] = p.aux_l * np.eye(na)
            self.Baux = np.zeros((nv, na))
            for a, k in enumerate(self.aux):
                self.Baux[self.idx[f"m{k}"], a] = 1.0; self.Baux[self.idx[f"x{k}"], a] = -1.0
        if nlp:                                                # A144: loop current b from upstream u_k into h_k
            c0 = nv + p.n + na
            self.M[c0:, c0:] = p.loop_l * np.eye(nlp)
            self.Bloop = np.zeros((nv, nlp))
            for b, k in enumerate(self.lp):
                if k > 1:
                    self.Bloop[self.idx[f"a{k - 1}"], b] = 1.0
                self.Bloop[self.idx[f"h{k}"], b] = -1.0
        self.nsw = [p.n_high] * p.n + [p.n_low] * p.n            # devices per switch position
        self.nl = None
        if p.nonlinear_coss:                                   # switch-branch incidence for the charge correction
            rsw = np.zeros((2 * p.n, ns)); vin_flag = np.zeros(2 * p.n)
            for j, (_, d, s_) in enumerate(self.switches):
                if d == "vin":
                    vin_flag[j] = 1.0
                else:
                    rsw[j, self.idx[d]] += 1.0
                if s_ is not None:
                    rsw[j, self.idx[s_]] -= 1.0
            nper = np.array([p.n_high] * p.n + [p.n_low] * p.n, float)
            clin = np.array([p.c_high] * p.n + [p.c_low] * p.n)
            self.nl = dict(r=rsw, vin=vin_flag, n=nper, clin=clin, model=EPC2067Coss(scale=p.coss_scale),
                           stats={"steps": 0, "iters": 0, "max_iters": 0, "newton": 0})

    def system(self, conducting, load_on, donly=None):
        p = self.p; nv = self.nv
        G = np.zeros((nv, nv)); gv = np.zeros(nv); frev = np.zeros(self.ns)
        for j, (on, (name, d, s)) in enumerate(zip(conducting, self.switches)):
            if not on:
                continue
            g = p.g_on
            idd, iss = self.idx.get(d), self.idx.get(s)
            if donly is not None and donly[j]:                 # reverse conduction, I_ds = g (V_ds + Vf)
                g = self.nsw[j] / p.rev_r
                if iss is not None:
                    frev[iss] += g * p.rev_vf
                if idd is not None:
                    frev[idd] -= g * p.rev_vf
            if d == "vin":
                G[iss, iss] += g; gv[iss] += g
                continue
            if idd is not None:
                G[idd, idd] += g
            if iss is not None:
                G[iss, iss] += g
            if idd is not None and iss is not None:
                G[idd, iss] -= g; G[iss, idd] -= g
        if load_on and p.load_kind == "r":
            G[self.idx["out"], self.idx["out"]] += 1.0 / p.r_load
        if self.nlp and p.loop_rp > 0:                         # A144: damping resistors across the loop inductances
            gd = 1.0 / p.loop_rp
            for k in self.lp:
                ih = self.idx[f"h{k}"]; G[ih, ih] += gd
                if k == 1:
                    gv[ih] += gd
                else:
                    iu = self.idx[f"a{k - 1}"]; G[iu, iu] += gd; G[iu, ih] -= gd; G[ih, iu] -= gd
        ns, n = self.ns, p.n
        A = np.zeros((ns, ns)); A[:nv, :nv] = -G; A[:nv, nv:nv + n] = -self.B; A[nv:nv + n, :nv] = self.B.T
        A[nv:nv + n, nv:nv + n] = -p.R * np.eye(n)
        for a in range(self.na):                               # A101: conducting entries after the switches; an open
            if conducting[2 * n + a]:                          # branch is uncoupled with di/dt = 0 (its current is 0)
                c = nv + n + a
                A[:nv, c] = -self.Baux[:, a]; A[c, :nv] = self.Baux[:, a]; A[c, c] = -p.aux_r
        fv = np.zeros(ns); fv[:nv] = gv
        for b in range(self.nlp):                              # A144: loop inductances (always in the circuit)
            c = nv + n + self.na + b
            A[:nv, c] = -self.Bloop[:, b]; A[c, :nv] = self.Bloop[:, b]
            if self.lp[b] == 1:
                fv[c] = 1.0                                    # L di/dt = vin - v(h1)
        fl = np.zeros(ns); fl[self.idx["out"]] = -1.0
        return A, fv, fl, frev

    def step(self, y, conducting, h, euler, t, load_on, donly=None):
        key = (conducting, h, euler, load_on, donly)
        entry = self.cache.get(key)
        if entry is None:
            A, fv, fl, frev = self.system(conducting, load_on, donly)
            if euler:
                lhs, rhs_m = self.M - h * A, self.M
            else:
                lhs, rhs_m = self.M - 0.5 * h * A, self.M + 0.5 * h * A
            entry = (lu_factor(lhs), rhs_m, fv, fl, lhs, frev if (donly is not None and any(donly)) else None)
            if h == self.p.h:
                self.cache[key] = entry
        lu, rhs_m, fv, fl, lhs, frev = entry
        p = self.p
        f1 = fv * p.vin_at(t + h) + fl * p.load_at(t + h)
        if euler:
            rhs = rhs_m @ y + h * f1
        else:
            f0 = fv * p.vin_at(t) + fl * p.load_at(t)
            rhs = rhs_m @ y + 0.5 * h * (f0 + f1)
        if frev is not None:                                   # the constant Vf sources
            rhs = rhs + h * frev
        y1 = lu_solve(lu, rhs)
        if self.nl is None:
            return y1
        return self._nonlinear(y, y1, lu, lhs, rhs, p.vin_at(t), p.vin_at(t + h))

    def _nonlinear(self, y0, y1, lu, lhs, rhs, vin0, vin1):
        """F(y1) = lhs y1 - rhs + R^T [n (q(v1) - q(v0)) - C_lin (v1 - v0)] = 0; chord on the cached LU."""
        nl = self.nl; r, n, clin, m = nl["r"], nl["n"], nl["clin"], nl["model"]
        v0 = r @ y0 + nl["vin"] * vin0
        q0 = n * m.q(v0)
        st = nl["stats"]; st["steps"] += 1
        for it in range(1, 9):
            v1 = r @ y1 + nl["vin"] * vin1
            corr = n * m.q(v1) - q0 - clin * (v1 - v0)
            dz = lu_solve(lu, lhs @ y1 - rhs + r.T @ corr)
            y1 = y1 - dz
            if np.max(np.abs(dz)) < 1e-7:
                st["iters"] += it; st["max_iters"] = max(st["max_iters"], it)
                return y1
        st["newton"] += 1                                          # fallback: full Newton
        for it in range(1, 31):
            v1 = r @ y1 + nl["vin"] * vin1
            corr = n * m.q(v1) - q0 - clin * (v1 - v0)
            jac = lhs + (r.T * (n * m.c(v1) - clin)) @ r
            dz = np.linalg.solve(jac, lhs @ y1 - rhs + r.T @ corr)
            y1 = y1 - dz
            if np.max(np.abs(dz)) < 1e-7:
                st["iters"] += 8 + it; st["max_iters"] = max(st["max_iters"], 8 + it)
                return y1
        raise RuntimeError("nonlinear Coss step did not converge")

    def edge_inc(self, j):
        """A145: the right-hand-side pattern of a channel current from switch j's drain to its source (KCL rows:
        -1 at the drain, +1 at the source; the vin source and ground have no row)."""
        _, d, s = self.switches[j]
        e = np.zeros(self.ns)
        if d != "vin":
            e[self.idx[d]] = -1.0
        if s is not None:
            e[self.idx[s]] = 1.0
        return e

    def vds(self, y, j, vin):
        name, d, s = self.switches[j]
        vd = vin if d == "vin" else y[self.idx[d]]
        vs = 0.0 if s is None else y[self.idx[s]]
        return vd - vs
