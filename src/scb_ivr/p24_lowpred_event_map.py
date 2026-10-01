"""P24 four-phase SCB: D46's event map with a timed (predicted) low-side turn-on (D47).

Extends D46 (p24_drop_event_map, unchanged): phase k's low side turns on at t_off,k + d_low,k, a timed edge, instead
of t_d after the V_DS = 0 comparator; the comparator only timestamps the zero crossing (log["low_cross_rel"], relative
to the high-side turn-off). symbolic_derivations/03_P24_native/D47. The period function is D46's, copied, with only
those two changes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .p24_exact_event_map import DOWN, HIGH, LOW, UP, Control
from .p24_drop_event_map import DropEventMap


@dataclass(frozen=True)
class ControlLP(Control):
    """D43's Control plus the low-side dead times d_low (s) after each phase's high-side turn-off. D53: optional
    per-phase offsets (s) of the on-time (ton_offset) and of the slot (slot_offset, phases 2..N); zero by default,
    which leaves every time unchanged."""
    d_low: tuple = (1.2e-9, 1.2e-9, 1.2e-9, 1.2e-9)
    ton_offset: tuple = (0.0, 0.0, 0.0, 0.0)
    slot_offset: tuple = (0.0, 0.0, 0.0, 0.0)


class LowPredEventMap(DropEventMap):
    """D46's map with the timed low-side turn-on; ctl must be a ControlLP."""

    def clone(self, ctl):
        other = LowPredEventMap(self.ckt, ctl, self.h, self.coss, self.n_high, self.n_low, self.rtol, self.atol,
                                self.chunk, self.vf, self.r_dev)
        other.tol_v, other.tol_i = self.tol_v, self.tol_i
        return other

    # ---- one period: D46's run_cycle, with the timed low-side turn-on (D47) ----
    def run_cycle(self, v0, i0, record=False, t_max=3e-6):
        ckt, ctl, n = self.ckt, self.ctl, self.ckt.n
        chan = [False] * (2 * n); diode = [False] * (2 * n)
        chan[0] = True
        for k in range(1, n):
            chan[n + k] = True
        state = [HIGH] + [LOW] * (n - 1)
        t_on = [0.0] + [None] * (n - 1); t_off = [None] * n; t_lo = [None] * n; t_lon = [0.0] * n
        t_zvs = [None] * n; fired = [False] * n
        slots = [None] + [k * ctl.t0 / n + ctl.slot_offset[k] for k in range(1, n)]
        log = {"lowoff": [], "turnon": [], "events": [], "rev_energy_j": [0.0] * (2 * n), "rev_time_s": [0.0] * (2 * n),
               "low_cross_rel": [None] * n, "low_on_vds": [None] * n}
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
                    timed.append((t_on[k] + (ctl.ton + ctl.ton_offset[k]), k, "high_off"))
                elif state[k] == DOWN:
                    timed.append((t_off[k] + ctl.d_low[k], k, "low_on"))            # D47: a timed edge
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
                    t_zvs[j - n] = t                     # the zero-crossing timestamp (no topology change)
                    log["low_cross_rel"][j - n] = t - t_off[j - n]
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
                log["low_on_vds"][k] = topo.vds(z, n + k)
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
