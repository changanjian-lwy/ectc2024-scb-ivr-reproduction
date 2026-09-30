"""P24 four-phase SCB: event map with nonlinear Coss(V) and the reverse-conduction drop (D46).

Extends D45 (p24_nonlinear_event_map, unchanged). A device that conducts only in reverse (gate off) is no longer an
ideal diode that merges its nodes. It carries I_SD = n (V_SD - Vf) / R: a conductance n/R and a constant term in the
node equations (symbolic_derivations/03_P24_native/D46). Consequences in the period map (D43's run_cycle, copied):
- the topology is keyed by the channel set (merged) and the reverse-conducting set (resistive);
- reverse conduction starts when V_DS falls through -Vf, and ends when its current falls through zero;
- a channel that turns off while carrying reverse current is not taken over at once: its node first travels to -Vf;
- the low-side turn-on decision (the ZVS comparator) is taken at V_DS = 0, as in the physical model, then waits t_d;
- the reverse-conduction energy and time are integrated per switch on the dense output.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.linalg.lapack import dposv
from scipy.optimize import brentq

from .p24_exact_event_map import DOWN, HIGH, LOW, UP, Circuit, Control
from .p24_nonlinear_event_map import NonlinearEventMap, _NLTopology


class _DropTopology(_NLTopology):
    """D45's topology over the channel set; reverse-conducting devices enter the node rows as n/R and n Vf / R."""

    def __init__(self, ckt, chan, rdiode, h, coss_dev, n_dev, rtol, atol, chunk, vf, r_dev):
        super().__init__(ckt, tuple(chan), h, coss_dev, n_dev, rtol, atol, chunk)
        self.rdiode, self.vf = tuple(rdiode), vf
        pos = {j: k for k, j in enumerate(self.branch_dev)}
        rows, gd = [], []
        for j, on in enumerate(self.rdiode):
            if on:
                if j not in pos:
                    raise ValueError(f"reverse-conducting device {j} between merged nodes")
                rows.append(pos[j]); gd.append(n_dev[j] / r_dev)
        self.drow, self.dg = np.array(rows, int), np.array(gd, float)
        self.ddev = [self.branch_dev[k] for k in rows]
        self.Ed = self.E[self.drow] if rows else np.zeros((0, self.m))
        self.e0d = self.e0[self.drow] if rows else np.zeros(0)

    def diode_ids(self, v):
        """I_DS (drain -> source) of each reverse-conducting device; negative while it conducts."""
        return self.dg * (self.Ed @ v + self.e0d + self.vf)

    def rhs(self, t, z):
        m = self.m
        v, i = z[:m], z[m:]
        if m:
            b = -self.gg @ v + self.bi @ i
            if len(self.drow):
                b = b - self.Ed.T @ self.diode_ids(v)            # current leaves the drain group, enters the source
            _, vdot, info = dposv(self.jc(v), b)
            if info:
                raise np.linalg.LinAlgError(f"capacitance matrix not positive definite ({info})")
        else:
            vdot = np.zeros(0)
        idot = self.K[m:] @ z + self.k0[m:]
        return np.concatenate([vdot, idot])

    def _device_currents(self, z):
        """D45's KCL for the channel devices, with the reverse-conducting devices' currents as known terms; the
        returned dict also holds those."""
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
        vv = z[:m]
        ids_d = dict(zip(self.ddev, self.diode_ids(vv))) if len(self.drow) else {}
        for j, cur in ids_d.items():
            _, d, s = ckt.devices[j]
            if d in leave:
                leave[d] += cur
            if s in leave:
                leave[s] -= cur
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
        out = dict(zip(cond, sol))
        out.update({j: float(c) for j, c in ids_d.items()})
        return out


class DropEventMap(NonlinearEventMap):
    """D45's map with the reverse-conduction drop (D46). vf (V) and r_dev (Ohm) per device."""

    def __init__(self, ckt: Circuit = Circuit(), ctl: Control = Control(), h: float = 0.25e-9, coss=None,
                 n_high: int = 2, n_low: int = 3, rtol: float = 1e-11, atol: float = 1e-10, chunk: float = 8e-9,
                 vf: float = 2.0894, r_dev: float = 6.013e-3):
        super().__init__(ckt, ctl, h, coss, n_high, n_low, rtol, atol, chunk)
        self.vf, self.r_dev = vf, r_dev
        self._dtopo = {}

    def clone(self, ctl: Control):
        other = DropEventMap(self.ckt, ctl, self.h, self.coss, self.n_high, self.n_low, self.rtol, self.atol,
                             self.chunk, self.vf, self.r_dev)
        other.tol_v, other.tol_i = self.tol_v, self.tol_i
        return other

    def topo2(self, chan, diode):
        key = (tuple(bool(c) for c in chan), tuple(bool(d) and not c for c, d in zip(chan, diode)))
        if key not in self._dtopo:
            self._dtopo[key] = _DropTopology(self.ckt, key[0], key[1], self.h, self.coss_dev, self.n_dev, self.rtol,
                                             self.atol, self.chunk, self.vf, self.r_dev)
        return self._dtopo[key]

    def _keeps_diode(self, *args):
        return False                                   # the node must first travel to -Vf (diode_on then fires)

    def _first_state_event(self, topo, z0, funcs, horizon, t_abs=0.0, state=None):
        """D45's scan, but an event is placed where its function has actually crossed (f <= 0), not at Brent's
        estimate, which can sit a few nV short. With the diode's 500 S that residue reads as a microampere of
        forward current and would end the conduction at once, an endless on/off chain (D46 Section 7)."""
        z0 = np.asarray(z0, float)
        if not funcs:
            return super()._first_state_event(topo, z0, funcs, horizon, t_abs, state)
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
                    lo, hi = root, step
                    if f(topo.dense(z0, t + root)) > 0.0:         # not yet crossed: bisect to the first crossed time
                        for _ in range(200):
                            mid = 0.5 * (lo + hi)
                            if not lo < mid < hi:
                                break
                            if f(topo.dense(z0, t + mid)) > 0.0:
                                lo = mid
                            else:
                                hi = mid
                        root = hi
                    if best is None or root < best[0]:
                        best = (root, funcs[idx][0])
                return t + best[0], best[1]
            t, prev = t + step, cur
        return None

    def _drop_events(self, topo, chan, diode, state, t_zvs):
        n, funcs = self.ckt.n, []
        for j in range(2 * n):
            if not (chan[j] or diode[j]):
                funcs.append((("diode_on", j), lambda z, j=j: topo.vds(z, j) + self.vf, self.tol_v))
            elif diode[j] and not chan[j]:
                k = topo.ddev.index(j)
                funcs.append((("diode_off", j), lambda z, k=k: -float(topo.diode_ids(z[:topo.m])[k]), self.tol_i))
        for k in range(n):                            # the low-side ZVS comparator, at V_DS = 0
            if state[k] == DOWN and t_zvs[k] is None and not (chan[n + k] or diode[n + k]):
                funcs.append((("zvs", n + k), lambda z, j=n + k: topo.vds(z, j), self.tol_v))
        if state[0] == LOW:
            funcs.append((("cmp1", 0), lambda z: z[topo.m] - self.ctl.i_target, self.tol_i))
        return funcs

    def _energy(self, topo, z0, tau, acc_e, acc_t):
        """Integrate V_SD * I_SD of each reverse-conducting device over [0, tau] from z0 (Simpson, <= 25 ps)."""
        if not len(topo.drow) or tau <= 0.0:
            return
        k = max(2, 2 * math.ceil(tau / 50e-12))
        ts = np.linspace(0.0, tau, k + 1)
        p = []
        for t in ts:
            z = topo.dense(z0, t) if t > 0 else z0
            v = z[:topo.m]
            vds = topo.Ed @ v + topo.e0d
            p.append(np.maximum(-topo.diode_ids(v), 0.0) * (-vds))
        p = np.array(p)
        w = np.ones(k + 1); w[1:-1:2] = 4.0; w[2:-1:2] = 2.0
        e = (tau / k / 3.0) * (w @ p)
        for idx, j in enumerate(topo.ddev):
            acc_e[j] += float(e[idx]); acc_t[j] += tau

    # ---- one period: D43's run_cycle, with the drop's topology, events and energy ----
    def run_cycle(self, v0, i0, record=False, t_max=3e-6):
        ckt, ctl, n = self.ckt, self.ctl, self.ckt.n
        chan = [False] * (2 * n); diode = [False] * (2 * n)
        chan[0] = True
        for k in range(1, n):
            chan[n + k] = True
        state = [HIGH] + [LOW] * (n - 1)
        t_on = [0.0] + [None] * (n - 1); t_off = [None] * n; t_lo = [None] * n; t_lon = [0.0] * n
        t_zvs = [None] * n; fired = [False] * n
        slots = [None] + [k * ctl.t0 / n for k in range(1, n)]
        log = {"lowoff": [], "turnon": [], "events": [], "rev_energy_j": [0.0] * (2 * n), "rev_time_s": [0.0] * (2 * n)}
        topo = self.topo2(chan, diode)
        z = self.reinit(np.asarray(v0, float), np.asarray(i0, float), topo)
        t = 0.0
        same_t = [0.0, 0]

        def change(v_full, i_vec):
            tp = self.topo2(chan, diode)
            return tp, self.reinit(v_full, i_vec, tp)

        while t < t_max:
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
            funcs = self._drop_events(topo, chan, diode, state, t_zvs)
            ev = self._first_state_event(topo, z, funcs, max(t_next - t, 0.0), t, state)
            if ev is not None and ev[0] < t_next - t:
                tau, key = ev
                self._energy(topo, z, tau, log["rev_energy_j"], log["rev_time_s"])
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
                elif kind == "diode_off":
                    diode[j] = False
                elif kind == "zvs":
                    t_zvs[j - n] = t                     # low-side ZVS decision (no topology change)
                    continue
                elif kind == "cmp1":
                    log["lowoff"].append({"t": t, "phase": 1, "i": i_vec[0], "how": "current"})
                    chan[n + 0] = False; state[0] = UP; t_lo[0] = t
                topo, z = change(v_full, i_vec)
                continue
            self._energy(topo, z, t_next - t, log["rev_energy_j"], log["rev_time_s"])
            z = topo.propagate(z, t_next - t); t = t_next
            v_full, i_vec = topo.to_full(z)
            k = k_next
            if kind_next == "high_off":
                chan[k] = False; state[k] = DOWN; t_off[k] = t; t_zvs[k] = None
            elif kind_next == "low_on":
                chan[n + k] = True; diode[n + k] = False; state[k] = LOW; t_lon[k] = t
            elif kind_next in ("low_off", "low_off_restart"):
                log["lowoff"].append({"t": t, "phase": k + 1, "i": i_vec[k], "how": kind_next})
                chan[n + k] = False; state[k] = UP; t_lo[k] = t; fired[k] = True
            elif kind_next in ("high_on", "high_restart"):
                log["turnon"].append({"t": t, "phase": k + 1, "vds": topo.vds(z, k), "how": kind_next,
                                      "i": i_vec[k], "since_lo": t - t_lo[k]})
                chan[k] = True; diode[k] = False; state[k] = HIGH; t_on[k] = t
                if k == 0:
                    pre = (v_full.copy(), i_vec.copy())
                    topo, z = change(v_full, i_vec)
                    v_new, i_new = topo.to_full(z)
                    if any(s != LOW for s in state[1:]) or any(diode):
                        raise RuntimeError(f"section with phases not all LOW or a diode on: {state} {diode}")
                    log.update(period=t, pre_section=pre)
                    return v_new, i_new, log
            topo, z = change(v_full, i_vec)
        raise RuntimeError("no phase-1 turn-on within t_max")
