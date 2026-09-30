"""P24 four-phase SCB: exact piecewise-linear event map with ideal switches (D43).

Independent of the Track A simulator (see symbolic_derivations/03_P24_native/D43):
- an ideal switch or conducting diode merges its two nodes (Vds = 0);
- a hard turn-on redistributes charge instantaneously (group charge conserved);
- each topology is linear time-invariant and is integrated exactly with the augmented matrix exponential;
- events are located on the exact trajectory: a 0.25 ns grid brackets a sign change, Brent refines it.

State: node voltages of (a1..a(N-1), x1..xN, out) and inductor currents (xk -> out).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq

HIGH, DOWN, LOW, UP = "HIGH", "DOWN", "LOW", "UP"


@dataclass(frozen=True)
class Circuit:
    """P24 single module (D43 Section 3); values as the Track A reference runs."""
    n: int = 4
    vin: float = 48.0
    L: float = 1.4666667e-9
    R: float = 0.54e-3
    c_high: float = 3.72e-9
    c_low: float = 5.58e-9
    cs: float = 3e-6
    co: float = 4.672e-3
    r_load: float = 4e-3

    @property
    def nodes(self):
        return tuple(f"a{k}" for k in range(1, self.n)) + tuple(f"x{k}" for k in range(1, self.n + 1)) + ("out",)

    @property
    def devices(self):
        """(name, drain, source): SH1..SHN then SL1..SLN."""
        n = self.n
        highs = [("SH1", "vin", "a1")] + [(f"SH{k}", f"a{k - 1}", f"a{k}") for k in range(2, n)] \
            + [(f"SH{n}", f"a{n - 1}", f"x{n}")]
        lows = [(f"SL{k}", f"x{k}", "gnd") for k in range(1, n + 1)]
        return tuple(highs + lows)

    @property
    def capacitors(self):
        caps = [(d, s, self.c_high if j < self.n else self.c_low) for j, (_, d, s) in enumerate(self.devices)]
        caps += [(f"a{k}", f"x{k}", self.cs) for k in range(1, self.n)]
        caps.append(("out", "gnd", self.co))
        return tuple(caps)


@dataclass(frozen=True)
class Control:
    """Mode-P controller matched to the Track A adopted rules (D43 Section 4)."""
    ton: float = 18.034e-9
    t0: float = 200e-9
    i_target: float = -9.375
    d_high: tuple = (8.12e-9, 7.88e-9, 7.88e-9, 7.0e-9)  # high-side turn-on delay after the low-side turn-off
    t_d_low: float = 10e-9                                # low-side ZVS decision -> channel on
    t_restart_high: float = 20e-9
    t_restart_low: float = 400e-9


class _Topology:
    """Node groups and the exact LTI flow for one set of conducting devices."""

    def __init__(self, ckt: Circuit, conducting: tuple, h: float):
        self.ckt, self.conducting = ckt, conducting
        parent = {name: name for name in ckt.nodes + ("vin", "gnd")}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for on, (_, d, s) in zip(conducting, ckt.devices):
            if on:
                parent[find(d)] = find(s)
        rv, rg = find("vin"), find("gnd")
        if rv == rg:
            raise ValueError("topology shorts the input")
        self.free, self.fixed = {}, {rv: ckt.vin, rg: 0.0}
        for name in ckt.nodes:
            r = find(name)
            if r not in self.fixed and r not in self.free:
                self.free[r] = len(self.free)
        self.root = {name: find(name) for name in ckt.nodes + ("vin", "gnd")}
        m, n = len(self.free), ckt.n
        self.m, self.dim = m, m + n
        cg, gg, bi, pv, p0 = np.zeros((m, m)), np.zeros((m, m)), np.zeros((m, n)), np.zeros((n, m)), np.zeros(n)
        for p, q, c in ckt.capacitors:
            gp, gq = self.root[p], self.root[q]
            if gp == gq:
                continue
            if gp in self.free:
                cg[self.free[gp], self.free[gp]] += c
            if gq in self.free:
                cg[self.free[gq], self.free[gq]] += c
            if gp in self.free and gq in self.free:
                cg[self.free[gp], self.free[gq]] -= c
                cg[self.free[gq], self.free[gp]] -= c
        go = self.root["out"]
        if go in self.free:
            gg[self.free[go], self.free[go]] += 1.0 / ckt.r_load
        for k in range(n):
            gx = self.root[f"x{k + 1}"]
            for g, sgn in ((gx, 1.0), (go, -1.0)):   # KCL: current i_k leaves x_k, enters out
                if g in self.free:
                    bi[self.free[g], k] -= sgn
                    pv[k, self.free[g]] += sgn
                else:
                    p0[k] += sgn * self.fixed[g]
        self.cg = cg
        ci = np.linalg.inv(cg) if m else np.zeros((0, 0))
        K = np.zeros((self.dim, self.dim)); k0 = np.zeros(self.dim)
        K[:m, :m] = -ci @ gg
        K[:m, m:] = ci @ bi
        K[m:, :m] = pv / ckt.L
        K[m:, m:] = -np.eye(n) * ckt.R / ckt.L
        k0[m:] = p0 / ckt.L
        self.K, self.k0 = K, k0
        aug = np.zeros((self.dim + 1, self.dim + 1))
        aug[:self.dim, :self.dim] = K
        aug[:self.dim, self.dim] = k0
        self.aug, self.h = aug, h
        self.phi_h = expm(aug * h)
        self._dev_affine = None

    # ---- coordinates ----
    def to_z(self, v_full, i):
        z = np.zeros(self.dim)
        for name, val in zip(self.ckt.nodes, v_full):
            r = self.root[name]
            if r in self.free:
                z[self.free[r]] = val
        z[self.m:] = i
        return z

    def node_v(self, z, name):
        r = self.root[name]
        return z[self.free[r]] if r in self.free else self.fixed[r]

    def to_full(self, z):
        return np.array([self.node_v(z, name) for name in self.ckt.nodes]), z[self.m:].copy()

    def propagate(self, z, tau):
        if tau == 0.0:
            return z.copy()
        return (expm(self.aug * tau) @ np.append(z, 1.0))[:-1]

    def step_h(self, z):
        return (self.phi_h @ np.append(z, 1.0))[:-1]

    # ---- linear functionals ----
    def vds(self, z, j):
        _, d, s = self.ckt.devices[j]
        return self.node_v(z, d) - self.node_v(z, s)

    def _device_currents(self, z):
        """Currents drain -> source of the conducting devices, from KCL on the merged-node forest."""
        ckt, m = self.ckt, self.m
        zdot = self.K @ z + self.k0
        vdot = {name: (zdot[self.free[self.root[name]]] if self.root[name] in self.free else 0.0)
                for name in ckt.nodes + ("vin", "gnd")}
        v = {name: self.node_v(z, name) for name in ckt.nodes}
        leave = {name: 0.0 for name in ckt.nodes}
        for p, q, c in ckt.capacitors:
            cur = c * (vdot[p] - vdot[q])                # p -> q through the capacitor
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
        """For each conducting device j: (a, b) with I_ds = a . z + b (exact, the map is affine)."""
        if self._dev_affine is None:
            base = self._device_currents(np.zeros(self.dim))
            cols = []
            for e in np.eye(self.dim):
                cur = self._device_currents(e)
                cols.append({j: cur[j] - base[j] for j in base})
            self._dev_affine = {j: (np.array([c[j] for c in cols]), base[j]) for j in base}
        return self._dev_affine


class ExactEventMap:
    """One period of the P24 module in mode P, from a phase-1 high-side turn-on to the next (D43)."""

    def __init__(self, ckt: Circuit = Circuit(), ctl: Control = Control(), h: float = 0.25e-9):
        self.ckt, self.ctl, self.h = ckt, ctl, h
        self._topo = {}
        self.tol_v, self.tol_i = 1e-9, 1e-9
        self._hook = None                     # optional callback(topo, z, t, state) on each grid point

    def topo(self, conducting):
        key = tuple(bool(c) for c in conducting)
        if key not in self._topo:
            self._topo[key] = _Topology(self.ckt, key, self.h)
        return self._topo[key]

    # ---- charge-conserving reinitialisation at a topology change ----
    def reinit(self, v_full, i, new: _Topology):
        ckt = self.ckt
        v = dict(zip(ckt.nodes, v_full)); v["vin"] = ckt.vin; v["gnd"] = 0.0
        q = {name: 0.0 for name in ckt.nodes}
        for p, qn, c in ckt.capacitors:
            if p in q:
                q[p] += c * (v[p] - v[qn])
            if qn in q:
                q[qn] += c * (v[qn] - v[p])
        rhs = np.zeros(new.m)
        for name in ckt.nodes:
            r = new.root[name]
            if r in new.free:
                rhs[new.free[r]] += q[name]
        for p, qn, c in ckt.capacitors:
            gp, gq = new.root[p], new.root[qn]
            if gp == gq:
                continue
            if gp in new.free and gq in new.fixed:
                rhs[new.free[gp]] += c * new.fixed[gq]
            if gq in new.free and gp in new.fixed:
                rhs[new.free[gq]] += c * new.fixed[gp]
        u = np.linalg.solve(new.cg, rhs) if new.m else np.zeros(0)
        z = np.concatenate([u, i])
        return z

    # ---- one period ----
    def run_cycle(self, v0, i0, record=False, t_max=3e-6):
        """Start: phase 1 has just turned on (SH1 conducting, a1 = Vin), phases 2..N LOW (SLk conducting).
        Return (v, i) at the next phase-1 high-side turn-on, after the turn-on's charge redistribution,
        and a log of the period."""
        ckt, ctl, n = self.ckt, self.ctl, self.ckt.n
        chan = [False] * (2 * n); diode = [False] * (2 * n)
        chan[0] = True
        for k in range(1, n):
            chan[n + k] = True
        state = [HIGH] + [LOW] * (n - 1)
        t_on = [0.0] + [None] * (n - 1); t_off = [None] * n; t_lo = [None] * n; t_lon = [0.0] * n
        t_zvs = [None] * n; fired = [False] * n
        slots = [None] + [k * ctl.t0 / n for k in range(1, n)]
        log = {"lowoff": [], "turnon": [], "events": []}
        topo = self.topo([c or d for c, d in zip(chan, diode)])
        z = self.reinit(np.asarray(v0, float), np.asarray(i0, float), topo)
        t = 0.0
        same_t = [0.0, 0]                     # guard against an endless chain of zero-time events

        def conducting():
            return [c or d for c, d in zip(chan, diode)]

        def change(new_cond, v_full, i_vec):
            tp = self.topo(new_cond)
            return tp, self.reinit(v_full, i_vec, tp)

        while t < t_max:
            # ---- timed events of the controller ----
            timed = []
            for k in range(n):
                if state[k] == HIGH:
                    timed.append((t_on[k] + ctl.ton, k, "high_off"))
                elif state[k] == DOWN:
                    timed.append(((t_zvs[k] + ctl.t_d_low) if t_zvs[k] is not None else (t_off[k] + ctl.t_restart_high),
                                  k, "low_on"))
                elif state[k] == LOW:
                    if k == 0:
                        timed.append((t_lon[0] + ctl.t_restart_low, 0, "low_off_restart"))
                    elif not fired[k]:
                        timed.append((slots[k], k, "low_off"))
                elif state[k] == UP:
                    d = min(ctl.d_high[k], ctl.t_restart_high)
                    timed.append((t_lo[k] + d, k, "high_on" if ctl.d_high[k] < ctl.t_restart_high else "high_restart"))
            t_next, k_next, kind_next = min(timed)
            # ---- state events on the exact trajectory ----
            funcs = self._event_functions(topo, chan, diode, state)
            ev = self._first_state_event(topo, z, funcs, max(t_next - t, 0.0), t, state)
            if ev is not None and ev[0] < t_next - t:
                tau, key = ev
                z = topo.propagate(z, tau); t += tau
                if tau == 0.0 and t == same_t[0]:
                    same_t[1] += 1
                    if same_t[1] > 50:
                        raise RuntimeError(f"event chain does not settle at t = {t}: {key}")
                else:
                    same_t[:] = [t, 0]
                v_full, i_vec = topo.to_full(z)
                kind, j = key
                log["events"].append((t, kind, j))
                if kind == "diode_on":
                    diode[j] = True
                    if j >= n and state[j - n] == DOWN and t_zvs[j - n] is None:
                        t_zvs[j - n] = t                     # low-side ZVS decision
                elif kind == "diode_off":
                    diode[j] = False
                elif kind == "cmp1":
                    log["lowoff"].append({"t": t, "phase": 1, "i": i_vec[0], "how": "current"})
                    chan[n + 0] = False; state[0] = UP; t_lo[0] = t
                    diode[n + 0] = self._keeps_diode(conducting(), n + 0, z, topo, chan, diode)
                topo, z = change(conducting(), v_full, i_vec)
                continue
            # ---- the timed event ----
            z = topo.propagate(z, t_next - t); t = t_next
            v_full, i_vec = topo.to_full(z)
            k = k_next
            if kind_next == "high_off":
                chan[k] = False; state[k] = DOWN; t_off[k] = t; t_zvs[k] = None
                diode[k] = self._keeps_diode(conducting(), k, z, topo, chan, diode)
            elif kind_next == "low_on":
                chan[n + k] = True; state[k] = LOW; t_lon[k] = t
            elif kind_next in ("low_off", "low_off_restart"):
                log["lowoff"].append({"t": t, "phase": k + 1, "i": i_vec[k], "how": kind_next})
                chan[n + k] = False; state[k] = UP; t_lo[k] = t; fired[k] = True
                diode[n + k] = self._keeps_diode(conducting(), n + k, z, topo, chan, diode)
            elif kind_next in ("high_on", "high_restart"):
                log["turnon"].append({"t": t, "phase": k + 1, "vds": topo.vds(z, k), "how": kind_next,
                                      "i": i_vec[k], "since_lo": t - t_lo[k]})
                chan[k] = True; state[k] = HIGH; t_on[k] = t
                if k == 0:
                    pre = (v_full.copy(), i_vec.copy())
                    topo, z = change(conducting(), v_full, i_vec)
                    v_new, i_new = topo.to_full(z)
                    if any(s != LOW for s in state[1:]):
                        raise RuntimeError(f"section with phases not all LOW: {state}")
                    log.update(period=t, pre_section=pre)
                    return v_new, i_new, log
            topo, z = change(conducting(), v_full, i_vec)
        raise RuntimeError("no phase-1 turn-on within t_max")

    def _keeps_diode(self, cond_after_channel_off, j, z, topo, chan, diode):
        """After a channel turns off: does the device's diode carry the current (reverse, source -> drain)?"""
        cur = topo.device_current_affine().get(j)
        if cur is None:
            return False
        a, b = cur
        return float(a @ z + b) < -self.tol_i

    def _event_functions(self, topo, chan, diode, state):
        """Affine event functions f(z) = a.z + b that fire when they fall through zero."""
        n, funcs = self.ckt.n, []
        dev = topo.device_current_affine()
        for j in range(2 * n):
            if not (chan[j] or diode[j]):
                funcs.append((("diode_on", j), lambda z, j=j: topo.vds(z, j), self.tol_v))
            elif diode[j] and not chan[j]:
                a, b = dev[j]
                funcs.append((("diode_off", j), lambda z, a=a, b=b: -(a @ z + b), self.tol_i))
        if state[0] == LOW:
            funcs.append((("cmp1", 0), lambda z: z[topo.m] - self.ctl.i_target, self.tol_i))
        return funcs

    def _first_state_event(self, topo, z0, funcs, horizon, t_abs=0.0, state=None):
        """Earliest fall-through of any event function in [0, horizon] on the exact trajectory."""
        if not funcs:
            return None
        f0 = [f(z0) for _, f, _ in funcs]
        for (key, f, tol), v in zip(funcs, f0):
            if v < -tol:
                return 0.0, key                              # level-triggered: already violated
        # a function is armed once it has left the zero band, so a function that sits at zero right after
        # an event does not fire again, while one that starts slightly positive and falls is still caught
        armed = [v > tol for (_, _, tol), v in zip(funcs, f0)]
        z, t = z0.copy(), 0.0
        prev = f0
        while t < horizon:
            step = min(self.h, horizon - t)
            z1 = topo.step_h(z) if step == self.h else topo.propagate(z, step)
            cur = [f(z1) for _, f, _ in funcs]
            if self._hook is not None:
                self._hook(topo, z1, t_abs + t + step, state)
            hits = [idx for idx, (a, b) in enumerate(zip(prev, cur)) if armed[idx] and a > 0.0 and b <= 0.0]
            armed = [ar or c > funcs[idx][2] for idx, (ar, c) in enumerate(zip(armed, cur))]
            if hits:
                best = None
                for idx in hits:
                    f = funcs[idx][1]
                    root = brentq(lambda s: f(topo.propagate(z, s)), 0.0, step, xtol=1e-18, rtol=1e-14)
                    if best is None or root < best[0]:
                        best = (root, funcs[idx][0])
                return t + best[0], best[1]
            z, t, prev = z1, t + step, cur
        return None


def valley_after_lowoff(emap: ExactEventMap, v_full, i, phase: int, horizon=40e-9):
    """Self-consistency of the predictive delay (D43 Section 5): from a section, run to phase `phase`'s
    low-side turn-off and then let its node ring with the high side held off (no turn-on), returning the
    time of the first minimum of Vds(SH_phase) after the turn-off and that minimum. None if Vds never falls
    (a diode-clamped, non-ringing node)."""
    import dataclasses
    ctl = emap.ctl
    d = list(ctl.d_high); d[phase - 1] = horizon
    probe = ExactEventMap(emap.ckt, dataclasses.replace(ctl, d_high=tuple(d), t_restart_high=horizon + 1e-9), emap.h)
    probe.tol_v, probe.tol_i = emap.tol_v, emap.tol_i
    trace = []

    def hook(topo, z, t, state):
        if state[phase - 1] == UP:
            trace.append((t, topo.vds(z, phase - 1)))

    probe._hook = hook
    try:
        probe.run_cycle(v_full, i)
    except RuntimeError:
        pass
    if len(trace) < 3:
        return None
    ts, vs = np.array([x[0] for x in trace]), np.array([x[1] for x in trace])
    t_lo = ts[0]
    for idx in range(1, len(vs) - 1):
        if vs[idx] <= vs[idx - 1] and vs[idx] < vs[idx + 1]:
            y0, y1, y2 = vs[idx - 1], vs[idx], vs[idx + 1]            # parabola through the grid minimum
            den = y0 - 2 * y1 + y2
            off = 0.5 * (y0 - y2) / den if den > 0 else 0.0
            step = ts[idx] - ts[idx - 1]
            return ts[idx] + off * step - t_lo, y1 - 0.25 * (y0 - y2) * off
    return None


def orbit(emap: ExactEventMap, s0, tol=1e-9, max_iter=40, fd=1e-6):
    """Newton on the section map F(s) - s with a finite-difference Jacobian (D43 Section 5).
    Returns (s*, J at s*, residual history, last log)."""
    def f(s):
        v, i = section_full(s, emap.ckt)
        v1, i1, log = emap.run_cycle(v, i)
        return section_free(v1, i1, emap.ckt), log

    s = np.array(s0, float)
    hist = []
    for _ in range(max_iter):
        fs, log = f(s)
        r = fs - s
        hist.append(float(np.max(np.abs(r))))
        J = np.zeros((len(s), len(s)))
        for c in range(len(s)):
            ds = np.zeros(len(s)); ds[c] = fd * max(1.0, abs(s[c]))
            J[:, c] = (f(s + ds)[0] - f(s - ds)[0]) / (2 * ds[c])
        if hist[-1] < tol:
            return s, J, hist, log
        step = np.linalg.solve(J - np.eye(len(s)), -r)
        lam = 1.0
        while lam > 1e-3:                       # damped Newton
            try:
                fn = f(s + lam * step)[0] - (s + lam * step)
                if np.max(np.abs(fn)) < hist[-1]:
                    break
            except (RuntimeError, ValueError):      # a trial state that breaks the cycle is rejected
                pass
            lam *= 0.5
        s = s + lam * step
    return s, J, hist, log


def section_free(v_full, i, ckt: Circuit = Circuit()):
    """Section coordinates free at a phase-1 turn-on (D43 Section 4): x1, a2..a(N-1), out, i1..iN."""
    names = ckt.nodes
    keep = ["x1"] + [f"a{k}" for k in range(2, ckt.n)] + ["out"]
    return np.array([v_full[names.index(nm)] for nm in keep] + list(i))


def section_full(s, ckt: Circuit = Circuit()):
    """Inverse of section_free: a1 = Vin (SH1 conducting), x2..xN = 0 (SLk conducting)."""
    v = dict.fromkeys(ckt.nodes, 0.0)
    v["a1"] = ckt.vin
    keep = ["x1"] + [f"a{k}" for k in range(2, ckt.n)] + ["out"]
    for nm, val in zip(keep, s[:len(keep)]):
        v[nm] = val
    return np.array([v[nm] for nm in ckt.nodes]), np.array(s[len(keep):])
