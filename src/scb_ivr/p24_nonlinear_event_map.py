"""P24 four-phase SCB: event map with nonlinear switch Coss(V) (D45).

Extends D43's exact piecewise-linear map (p24_exact_event_map, unchanged). Kept from D43: ideal switches and node
groups, the controller state machine (run_cycle), the section and Newton. Replaced (symbolic_derivations/03_P24_native/D45):
- flow: J(v) dv/dt = f(v, i), J the incremental capacitance matrix of the node groups (each switch branch n c(V)),
  integrated with DOP853 and dense output;
- device currents: the same KCL, with capacitor currents n c(V) dV/dt;
- reinitialisation at a topology change: each new group's charge is conserved, Q(u) = Q_old, by Newton;
- events: D43's 0.25 ns grid, arming rule and Brent, on the dense output.
"""
from __future__ import annotations

import dataclasses

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from scipy.linalg.lapack import dposv
from scipy.optimize import brentq

from .p24_exact_event_map import UP, Circuit, Control, ExactEventMap, _Topology


class Coss:
    """Per-device Coss(V): c(V) even, q(V) odd with q' = c. `pchip` (C1) or a constant."""

    def __init__(self, c_of_v, q_of_v):
        self._c, self._q = c_of_v, q_of_v

    def c(self, v):
        return self._c(np.abs(v))

    def q(self, v):
        return np.sign(v) * self._q(np.abs(v))

    @classmethod
    def constant(cls, c):
        return cls(lambda a: np.full(np.shape(a), c, float), lambda a: c * a)

    @classmethod
    def from_points(cls, v, c, v_max=40.0, dv=0.1):
        """A59/A86 construction: PCHIP of the points on a 0.1 V grid, q its antiderivative; held linear beyond v_max.
        Evaluated from the PCHIP's own piecewise-polynomial coefficients (the same function, less call overhead)."""
        grid = np.arange(0.0, v_max + 1e-9, dv)
        ci = PchipInterpolator(grid, np.interp(grid, v, c), extrapolate=False)
        qi = ci.antiderivative()
        c_end, q_end = float(ci(v_max)), float(qi(v_max))
        xs, last, inv = np.ascontiguousarray(ci.x), len(ci.x) - 2, 1.0 / dv
        c0, c1, c2, c3 = (np.ascontiguousarray(r) for r in ci.c)
        q0, q1, q2, q3, q4 = (np.ascontiguousarray(r) for r in qi.c)

        def c_of(a):
            a = np.asarray(a, float)
            k = np.minimum((a * inv).astype(np.intp), last)
            dx = a - xs[k]
            val = ((c0[k] * dx + c1[k]) * dx + c2[k]) * dx + c3[k]
            return np.where(a > v_max, c_end, val) if a.size and a.max() > v_max else val

        def q_of(a):
            a = np.asarray(a, float)
            k = np.minimum((a * inv).astype(np.intp), last)
            dx = a - xs[k]
            val = (((q0[k] * dx + q1[k]) * dx + q2[k]) * dx + q3[k]) * dx + q4[k]
            return np.where(a > v_max, q_end + c_end * (a - v_max), val) if a.size and a.max() > v_max else val
        return cls(c_of, q_of)


class _NLTopology(_Topology):
    """D43's node groups and inductor rows; the node rows carry the nonlinear switch capacitances."""

    def __init__(self, ckt: Circuit, conducting: tuple, h: float, coss_dev, n_dev, rtol, atol, chunk):
        super().__init__(ckt, conducting, h)
        m, n = self.m, ckt.n
        self.coss_dev, self.rtol, self.atol, self.chunk = coss_dev, rtol, atol, chunk
        cg_lin, gg, bi = np.zeros((m, m)), np.zeros((m, m)), np.zeros((m, n))
        for p, q, c in ckt.capacitors[2 * n:]:                    # Cs and Co (linear)
            gp, gq = self.root[p], self.root[q]
            if gp == gq:
                continue
            for a, b in ((gp, gq), (gq, gp)):
                if a in self.free:
                    cg_lin[self.free[a], self.free[a]] += c
                    if b in self.free:
                        cg_lin[self.free[a], self.free[b]] -= c
        go = self.root["out"]
        if go in self.free:
            gg[self.free[go], self.free[go]] += 1.0 / ckt.r_load
        for k in range(n):
            gx = self.root[f"x{k + 1}"]
            for g, sgn in ((gx, 1.0), (go, -1.0)):
                if g in self.free:
                    bi[self.free[g], k] -= sgn
        self.cg_lin, self.gg, self.bi = cg_lin, gg, bi
        rows, e0, nd, dev = [], [], [], []                          # switch branches between different groups
        for j, (_, d, s) in enumerate(ckt.devices):
            gd, gs = self.root[d], self.root[s]
            if gd == gs:
                continue
            row = np.zeros(m); off = 0.0
            if gd in self.free:
                row[self.free[gd]] += 1.0
            else:
                off += self.fixed[gd]
            if gs in self.free:
                row[self.free[gs]] -= 1.0
            else:
                off -= self.fixed[gs]
            rows.append(row); e0.append(off); nd.append(n_dev[j]); dev.append(j)
        self.E = np.array(rows).reshape(len(rows), m); self.e0 = np.array(e0); self.nd = np.array(nd, float)
        self.branch_dev = dev
        self.coss_hi, self.coss_lo = coss_dev[0], coss_dev[-1]
        self.same = self.coss_hi is self.coss_lo
        self.hi = np.array([k for k, j in enumerate(dev) if j < n], int)
        self.lo = np.array([k for k, j in enumerate(dev) if j >= n], int)
        self._seg = None                                           # dense-output cache: (z0 bytes, [(t0, t1, sol)])

    # ---- the nonlinear flow ----
    def jc(self, v):
        vb = self.E @ v + self.e0
        if self.same:
            c = self.coss_hi.c(vb)
        else:
            c = np.empty(len(vb)); c[self.hi] = self.coss_hi.c(vb[self.hi]); c[self.lo] = self.coss_lo.c(vb[self.lo])
        w = self.nd * c
        return self.cg_lin + self.E.T @ (w[:, None] * self.E)

    def rhs(self, t, z):
        m = self.m
        v, i = z[:m], z[m:]
        if m:
            _, vdot, info = dposv(self.jc(v), -self.gg @ v + self.bi @ i)   # J is symmetric positive definite
            if info:
                raise np.linalg.LinAlgError(f"capacitance matrix not positive definite ({info})")
        else:
            vdot = np.zeros(0)
        idot = self.K[m:] @ z + self.k0[m:]
        return np.concatenate([vdot, idot])

    def _segments(self, z0, t_need):
        key = z0.tobytes()
        if self._seg is None or self._seg[0] != key:
            self._seg = (key, z0.copy(), [])
        segs = self._seg[2]
        t_end = segs[-1][1] if segs else 0.0
        z_end = segs[-1][2].sol(t_end) if segs else self._seg[1]
        while t_end < t_need:
            t1 = t_end + max(self.chunk, 0.0)
            sol = solve_ivp(self.rhs, (t_end, t1), z_end, method="DOP853", rtol=self.rtol, atol=self.atol,
                            dense_output=True)
            if not sol.success:
                raise RuntimeError(f"nonlinear flow failed: {sol.message}")
            segs.append((t_end, t1, sol))
            t_end, z_end = t1, sol.y[:, -1]
        return segs

    def dense(self, z0, t):
        if t == 0.0:
            return z0.copy()
        for t0, t1, sol in self._segments(z0, t):
            if t <= t1:
                return sol.sol(t)
        raise AssertionError

    def propagate(self, z, tau):
        return self.dense(np.asarray(z, float), tau)

    def step_h(self, z):
        return self.propagate(z, self.h)

    # ---- device currents (not affine here) ----
    def _device_currents(self, z):
        ckt, m = self.ckt, self.m
        zdot = self.rhs(0.0, z)
        vdot = {name: (zdot[self.free[self.root[name]]] if self.root[name] in self.free else 0.0)
                for name in ckt.nodes + ("vin", "gnd")}
        v = {name: self.node_v(z, name) for name in ckt.nodes + ("vin", "gnd")}
        leave = {name: 0.0 for name in ckt.nodes}
        n_dev = dict(zip(self.branch_dev, self.nd))
        caps = [(d, s, n_dev.get(j, 0.0) * float(self.coss_dev[j].c(v[d] - v[s]))) for j, (_, d, s) in enumerate(ckt.devices)]
        caps += list(ckt.capacitors[2 * ckt.n:])
        for p, q, c in caps:
            cur = c * (vdot[p] - vdot[q])
            if p in leave:
                leave[p] += cur
            if q in leave:
                leave[q] -= cur
        for k in range(ckt.n):
            leave[f"x{k + 1}"] += z[m + k]
            leave["out"] -= z[m + k]
        leave["out"] += v["out"] / ckt.r_load
        cond = [j for j, on in enumerate(self.conducting) if on]
        rows = list(ckt.nodes)
        A = np.zeros((len(rows), len(cond)))
        for col, j in enumerate(cond):
            _, d, s = ckt.devices[j]
            if d in leave:
                A[rows.index(d), col] += 1.0
            if s in leave:
                A[rows.index(s), col] -= 1.0
        rhs = -np.array([leave[r] for r in rows])
        sol = np.linalg.lstsq(A, rhs, rcond=None)[0] if cond else np.zeros(0)
        return dict(zip(cond, sol))

    def device_current_affine(self):
        raise NotImplementedError("device currents are not affine with nonlinear Coss")


class NonlinearEventMap(ExactEventMap):
    """D43's period map with nonlinear switch Coss (D45). `coss`: one per-device curve, or (high side, low side)."""

    def __init__(self, ckt: Circuit = Circuit(), ctl: Control = Control(), h: float = 0.25e-9, coss: Coss = None,
                 n_high: int = 2, n_low: int = 3, rtol: float = 1e-11, atol: float = 1e-10, chunk: float = 8e-9):
        super().__init__(ckt, ctl, h)
        self.coss = coss if coss is not None else Coss.constant(ckt.c_high / n_high)
        hi, lo = self.coss if isinstance(self.coss, tuple) else (self.coss, self.coss)   # (high, low) or one curve
        self.coss_dev = [hi] * ckt.n + [lo] * ckt.n
        self.n_high, self.n_low, self.rtol, self.atol, self.chunk = n_high, n_low, rtol, atol, chunk
        self.n_dev = [n_high] * ckt.n + [n_low] * ckt.n

    def clone(self, ctl: Control):
        other = NonlinearEventMap(self.ckt, ctl, self.h, self.coss, self.n_high, self.n_low, self.rtol, self.atol,
                                  self.chunk)
        other.tol_v, other.tol_i = self.tol_v, self.tol_i
        return other

    def topo(self, conducting):
        key = tuple(bool(c) for c in conducting)
        if key not in self._topo:
            self._topo[key] = _NLTopology(self.ckt, key, self.h, self.coss_dev, self.n_dev, self.rtol, self.atol,
                                          self.chunk)
        return self._topo[key]

    # ---- charges ----
    def node_charges(self, v_full):
        """Plate charge on each node: linear caps c (v_p - v_q); switch j: +n q(V_ds) on the drain, - on the source."""
        ckt = self.ckt
        v = dict(zip(ckt.nodes, v_full)); v["vin"] = ckt.vin; v["gnd"] = 0.0
        q = {name: 0.0 for name in ckt.nodes + ("vin", "gnd")}
        for j, (_, d, s) in enumerate(ckt.devices):
            qq = self.n_dev[j] * float(self.coss_dev[j].q(v[d] - v[s]))
            q[d] += qq; q[s] -= qq
        for p, qn, c in ckt.capacitors[2 * ckt.n:]:
            q[p] += c * (v[p] - v[qn]); q[qn] += c * (v[qn] - v[p])
        return q

    def reinit(self, v_full, i, new: _NLTopology):
        """Charge-conserving reinitialisation: every new free group keeps its total plate charge."""
        ckt = self.ckt
        q_old = self.node_charges(v_full)
        target = np.zeros(new.m)
        for name in ckt.nodes:
            r = new.root[name]
            if r in new.free:
                target[new.free[r]] += q_old[name]
        u = super().reinit(v_full, i, new)[:new.m]                # initial guess: D43's linear reinitialisation
        for _ in range(60):
            z = np.concatenate([u, i])
            q_new = self.node_charges(new.to_full(z)[0])
            f = np.zeros(new.m)
            for name in ckt.nodes:
                r = new.root[name]
                if r in new.free:
                    f[new.free[r]] += q_new[name]
            f -= target
            du = np.linalg.solve(new.jc(u), f)
            u = u - du
            if np.max(np.abs(du)) < 1e-10:                        # the charge round-off floor is ~1e-12 V
                return np.concatenate([u, i])
        raise RuntimeError("nonlinear reinitialisation did not converge")

    # ---- events ----
    def _keeps_diode(self, cond_after_channel_off, j, z, topo, chan, diode):
        cur = topo._device_currents(z).get(j)
        return cur is not None and float(cur) < -self.tol_i

    def _event_functions(self, topo, chan, diode, state):
        n, funcs = self.ckt.n, []
        for j in range(2 * n):
            if not (chan[j] or diode[j]):
                funcs.append((("diode_on", j), lambda z, j=j: topo.vds(z, j), self.tol_v))
            elif diode[j] and not chan[j]:
                funcs.append((("diode_off", j), lambda z, j=j: -float(topo._device_currents(z)[j]), self.tol_i))
        if state[0] == "LOW":
            funcs.append((("cmp1", 0), lambda z: z[topo.m] - self.ctl.i_target, self.tol_i))
        return funcs

    def _first_state_event(self, topo, z0, funcs, horizon, t_abs=0.0, state=None):
        """D43's grid scan and arming rule, on the dense output from z0."""
        z0 = np.asarray(z0, float)
        if not funcs:
            if self._hook is not None:                     # the hook still sees every grid point
                t = 0.0
                while t < horizon:
                    t = min(t + self.h, horizon)
                    self._hook(topo, topo.dense(z0, t), t_abs + t, state)
            return None
        f0 = [f(z0) for _, f, _ in funcs]
        for (key, f, tol), v in zip(funcs, f0):
            if v < -tol:
                return 0.0, key
        armed = [v > tol for (_, _, tol), v in zip(funcs, f0)]
        t, prev = 0.0, f0
        while t < horizon:
            step = min(self.h, horizon - t)
            z1 = topo.dense(z0, t + step)
            cur = [f(z1) for _, f, _ in funcs]
            if self._hook is not None:
                self._hook(topo, z1, t_abs + t + step, state)
            hits = [idx for idx, (a, b) in enumerate(zip(prev, cur)) if armed[idx] and a > 0.0 and b <= 0.0]
            armed = [ar or c > funcs[idx][2] for idx, (ar, c) in enumerate(zip(armed, cur))]
            if hits:
                best = None
                for idx in hits:
                    f = funcs[idx][1]
                    root = brentq(lambda s: f(topo.dense(z0, t + s)), 0.0, step, xtol=1e-18, rtol=1e-14)
                    if best is None or root < best[0]:
                        best = (root, funcs[idx][0])
                return t + best[0], best[1]
            t, prev = t + step, cur
        return None


class _ValleyFound(Exception):
    pass


def nl_valley_after_lowoff(emap: ExactEventMap, v_full, i, phase: int, horizon=40e-9):
    """D43's valley_after_lowoff, with the time measured from the low-side turn-off itself. D43's version measures
    from the first grid point after it (h = 0.25 ns later), so its valley times are one grid step early (D45
    Section 7). Works for ExactEventMap and NonlinearEventMap. Returns (time after the low-side turn-off, Vds) of
    the first minimum of Vds(SH_phase), or None."""
    ctl = emap.ctl
    d = list(ctl.d_high); d[phase - 1] = horizon
    ctl_p = dataclasses.replace(ctl, d_high=tuple(d), t_restart_high=horizon + 1e-9)
    if isinstance(emap, NonlinearEventMap):
        probe = emap.clone(ctl_p)
    else:
        probe = ExactEventMap(emap.ckt, ctl_p, emap.h)
        probe.tol_v, probe.tol_i = emap.tol_v, emap.tol_i
    trace, t_lo = [], [None]
    inner = probe._first_state_event

    def first_state_event(topo, z0, funcs, horizon, t_abs=0.0, state=None):
        if state is not None and state[phase - 1] == UP and t_lo[0] is None:
            t_lo[0] = t_abs                                   # the first scan after the turn-off starts at it
        return inner(topo, z0, funcs, horizon, t_abs, state)

    def hook(topo, z, t, state):
        if state[phase - 1] == UP:
            trace.append((t, topo.vds(z, phase - 1)))
            if len(trace) >= 3 and trace[-2][1] <= trace[-3][1] and trace[-2][1] < trace[-1][1]:
                raise _ValleyFound                              # the rest of the cycle is not needed

    probe._first_state_event = first_state_event
    probe._hook = hook
    try:
        probe.run_cycle(v_full, i)
    except (RuntimeError, _ValleyFound):
        pass
    if len(trace) < 3:
        return None
    ts, vs = np.array([x[0] for x in trace]), np.array([x[1] for x in trace])
    t_lo = t_lo[0]
    for idx in range(1, len(vs) - 1):
        if vs[idx] <= vs[idx - 1] and vs[idx] < vs[idx + 1]:
            y0, y1, y2 = vs[idx - 1], vs[idx], vs[idx + 1]
            den = y0 - 2 * y1 + y2
            off = 0.5 * (y0 - y2) / den if den > 0 else 0.0
            step = ts[idx] - ts[idx - 1]
            return ts[idx] + off * step - t_lo, y1 - 0.25 * (y0 - y2) * off
    return None


def orbit_chord(emap: ExactEventMap, s0, J=None, tol=1e-8, max_iter=15, fd=1e-6):
    """Newton on F(s) - s like D43's `orbit`, but reusing a supplied Jacobian (chord) and recomputing it (forward
    differences) only when the residual falls by less than a factor 4 per step. Returns (s*, J, history, log)."""
    from .p24_exact_event_map import section_free, section_full

    def f(s):
        v, i = section_full(s, emap.ckt)
        v1, i1, log = emap.run_cycle(v, i)
        return section_free(v1, i1, emap.ckt), log

    def jac(s, fs):
        Jn = np.zeros((len(s), len(s)))
        for c in range(len(s)):
            ds = np.zeros(len(s)); ds[c] = fd * max(1.0, abs(s[c]))
            Jn[:, c] = (f(s + ds)[0] - fs) / ds[c]
        return Jn

    s = np.array(s0, float)
    fs, log = f(s)
    hist = [float(np.max(np.abs(fs - s)))]
    fresh = J is None
    if fresh:
        J = jac(s, fs)
    for _ in range(max_iter):
        if hist[-1] < tol:
            return s, J, hist, log
        step = np.linalg.solve(J - np.eye(len(s)), -(fs - s))
        lam, ok = 1.0, False
        while lam > 1e-3:
            try:
                fn, ln = f(s + lam * step)
                rn = float(np.max(np.abs(fn - (s + lam * step))))
                if rn < hist[-1]:
                    ok = True
                    break
            except (RuntimeError, ValueError):
                pass
            lam *= 0.5
        if not ok:
            if fresh:
                break
            J, fresh = jac(s, fs), True
            continue
        slow = rn > 0.25 * hist[-1]
        s, fs, log = s + lam * step, fn, ln
        hist.append(rn)
        if slow and not fresh and hist[-1] >= tol:
            J, fresh = jac(s, fs), True
        else:
            fresh = False
    return s, J, hist, log
