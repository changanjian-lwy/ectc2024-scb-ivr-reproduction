"""A163: gate-driven switching edges for the plant (CircuitParams.gate_dev, cfg "gate" in the bridge).

Each listed switch (gate_switches; default the high sides) has n parallel devices of the D79 model (EPC's model form,
scb_ivr.p24_gate_model), each driven by gate_v_on / 0 V through its own gate_r_on / gate_r_off (external plus driver;
gate_r_on_ls >= 0 gives the low sides their own turn-on value, A206) in series with the device's R_G, with a
common-source inductance gate_l_cs per device. A command starts the gate moving; the switch's physical state follows
the gate:
- turn-on at V_DS <= 0: conducting at once (as without the model); with gate_zvs_edge (A206) it is an edge instead,
  active from the command with the gate at its present level: the channel equation's third quadrant carries the
  reverse current (in place of the plant's Vf + R fit) while the gate charges. Under an interlock, a turn-on
  commanded at V_DS <= 0 while its complement conducts waits as a turn-on at V_DS > 0 does;
- turn-on at V_DS > 0: open while the gate charges (pending; the C step loop runs one step at a time and track()
  integrates the gate's charge balance with the step's V_DS, so the Miller charge of a moving drain counts) until
  the channel carries ACT_I per device at max(V_DS, gate_v_hand) (a node that already swung to zero hands over as
  the gate passes threshold), then active; conducting from the step at which V_DS <= gate_v_hand (with
  gate_zvs_edge: |V_DS| <= gate_v_hand with the gate at or above that channel start, so a node that swung below zero
  keeps its channel equation until the gate has charged);
- turn-off with forward current: conducting while the gate discharges (pending) until the channel needs gate_v_hand
  of V_DS to carry the switch current, then active; open once the channel carries < ACT_I per device;
- turn-off with zero or reverse current: open at once; with gate_zvs_edge (A206) a conducting switch that carries
  reverse current is an edge instead, active from the command: its channel keeps conducting (third quadrant) while
  the gate discharges, and the plant's Vf + R fit takes over once the gate is below ZVS_OFF_V. For the interlock it
  counts as conducting only while its gate is above the channel start.
Active switches are open in the matrix; their channel current n i_ch(v_gs, V_DS) is a source from drain to source,
solved with the plant state and each gate's charge balance by Newton on the step (trapezoid, or backward Euler with
the plant's Euler steps):
    q_g(v1, d1) - q_g(v0, d0) = (h / 2R)(2 V_drv - v0 - v1) - (L_cs / R)(i_s1 - i_s0),
q_g = q_gs + q_gd, i_s = i_ch + dq_oss/dt (the device's terminal current; q_oss = the plant's Coss per device).
A shoot-through (stats shoot_on) is a turn-on whose channel starts while its complement conducts, physically (its
turn-off still pending or active) when the complement is gate-driven too; low sides keep their own edge times (*_ls_s).
Driver interlock (gate_il; its delay is still counted from the original command; stats il_holds, il_hold_max_s):
- "gate" (A170): a turn-on commanded while its complement conducts (as above) is held, its gate not driven and its
  switch open, until the complement stops conducting; it then starts gate_t_il later as a normal command;
- "threshold" (A171): the gate charges as usual; a turn-on whose channel would start while its complement conducts
  is held there, gate frozen at that level and switch open, and starts gate_t_il after the complement stops.
Gate voltages between edges follow the RC charge with C_in(v_gs, V_DS) at the last known V_DS (no Miller injection);
a pending turn-off's activation time is computed that way (V_DS ~ 0 while it conducts) and the plants stop there.
With gate_miller (A206) an idle gate driven off follows its charge balance with the drain's movement instead
(_follow): after every Python step in which its V_DS moved MILLER_DV, and at its next command. So the dip a falling
drain leaves on a low side's gate is there when that low side is commanded on. Stretches the C loop runs without
stopping are taken with V_DS linear over the stretch.
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np

ACT_I = 0.01            # A per device: channel current that starts / ends an active edge
T_ACTIVE_MAX = 200e-9   # an active edge still running then is ended (counted)
OFF_LOG = 20000         # physical high-side turn-offs kept (the last ones)
MILLER_DV = 0.05        # V: an idle off gate is updated (gate_miller) when its V_DS has moved this much
ZVS_OFF_V = 0.1         # V: a reverse-current turn-off edge (gate_zvs_edge) ends when its gate is below this


def _sp(x):
    return x + math.log1p(math.exp(-x)) if x > 0 else math.log1p(math.exp(x))


def _sig(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


class FastDev:
    """Scalar (math-module) versions of p24_gate_model.Device's channel and gate charges, same expressions."""

    def __init__(self, dev):
        p = dev.p
        self.a1, self.k2, self.k3, self.x0, self.x1 = dev._k()
        self.cg = dev.cg_scale
        self.g = [p[k] for k in ("ags1", "ags2", "ags3", "ags4", "ags5", "ags6", "ags7")]
        self.d1 = p["agd1"]
        self.gd = [(p[a], p[b], p[c]) for a, b, c in (("agd2", "agd3", "agd4"), ("agd5", "agd6", "agd7"),
                                                        ("agd8", "agd9", "agd10"))]

    def i_ch(self, v, d):
        if d > 0:
            return self.a1 * _sp((v - self.k2) / self.k3) * d / (1 + (self.x0 + self.x1 * v) * d)
        w, e = v - d, -d
        return -self.a1 * _sp((w - self.k2) / self.k3) * e / (1 + (self.x0 + self.x1 * w) * e)

    def di_ch(self, v, d, eps=1e-6):
        return ((self.i_ch(v + eps, d) - self.i_ch(v - eps, d)) / (2 * eps),
                (self.i_ch(v, d + eps) - self.i_ch(v, d - eps)) / (2 * eps))

    def q_gs(self, v, vsd):
        a1, a2, a3, a4, a5, a6, a7 = self.g
        return self.cg * (a1 * v + 0.5 * a2 * a4 * _sp((v - a3) / a4) + a5 * a7 * _sp((vsd - a6) / a7))

    def c_gs(self, v):
        a1, a2, a3, a4 = self.g[:4]
        return self.cg * (a1 + 0.5 * a2 * _sig((v - a3) / a4))

    def q_gd(self, w):
        a2, a3, a4 = self.g[1:4]
        q = self.d1 * w + 0.5 * a2 * a4 * _sp((w - a3) / a4)
        for a, b, c in self.gd:
            q += a * c * _sp((w - b) / c)
        return self.cg * q

    def c_gd(self, w):
        a2, a3, a4 = self.g[1:4]
        c = self.d1 + 0.5 * a2 * _sig((w - a3) / a4)
        for a, b, cc in self.gd:
            c += a * _sig((w - b) / cc)
        return self.cg * c

    def q_gate(self, v, d):
        return self.q_gs(v, -d) + self.q_gd(v - d)

    def cin(self, v, d):
        return self.c_gs(v) + self.c_gd(v - d)

    def vgs_for(self, i, d):
        lo, hi = -1.0, 8.0
        for _ in range(60):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if self.i_ch(m, d) < i else (lo, m)
        return 0.5 * (lo + hi)


def p_n(ge):
    return ge.p.n


LS_KEYS = ("delay_on_ls_s", "delay_off_ls_s", "active_on_ls_s", "active_off_ls_s")


def _key(k, j, n):
    """High-side stats key k, or its low-side twin (A169) for switch j >= n."""
    return k if j < n else k[:-2] + "_ls_s"


class GateEdges:
    def __init__(self, plant):
        from scb_ivr.p24_gate_model import load_device
        p = plant.p
        self.plant, self.p = plant, p
        self.dev = load_device(p.gate_dev, temp=p.gate_temp, dk2=p.gate_dk2, cg_scale=p.gate_cg_scale)
        self.fd = FastDev(self.dev)
        self.on_act = {}                               # switch -> callback at its next activation (the bridge's)
        self.next_cb = {}                              # the bridge's callback for the command about to come
        self.off_log = deque(maxlen=OFF_LOG)           # (t_act, phase, i at activation, max i in the edge) high sides
        self.hold_log = deque(maxlen=OFF_LOG)          # A205: (t_hold, switch, t_release) of the interlock's holds
        n2 = 2 * p.n
        self.sw = tuple(sorted(int(j) for j in p.gate_switches))
        self.nsw = plant.sim.nsw
        self.rg = self.dev.r_g
        self.r_on = {j: (p.gate_r_on_ls if (j >= p.n and p.gate_r_on_ls >= 0.0) else p.gate_r_on) for j in self.sw}
        self.zvs_edge = bool(p.gate_zvs_edge)           # A206
        self.miller = bool(p.gate_miller)               # A206
        self.st = {j: dict(phase="idle", drv=False, vgs=0.0, t=0.0, vds=0.0, t_act=math.inf, kind=None, t_cmd=0.0,
                           i_s=0.0, vds_cmd=0.0) for j in self.sw}
        sim = plant.sim
        self.dvec = {}
        for j in self.sw:                              # d V_DS / d y for switch j
            _, d, s = sim.switches[j]
            r = np.zeros(sim.ns)
            if d != "vin":
                r[sim.idx[d]] += 1.0
            if s is not None:
                r[sim.idx[s]] -= 1.0
            self.dvec[j] = r
        self.einc = {j: sim.edge_inc(j) for j in self.sw}
        self.stats = {"on": [0] * n2, "off": [0] * n2, "on_zvs": [0] * n2, "off_rev": [0] * n2, "forced": 0,
                      "newton_max": 0, "steps": 0, "delay_on_s": [math.inf, 0.0], "delay_off_s": [math.inf, 0.0],
                      "active_on_s": [math.inf, 0.0], "active_off_s": [math.inf, 0.0], "didt_on_max_a_ns": 0.0,
                      "didt_off_max_a_ns": 0.0, "vds_cmd_on_max_v": 0.0, "e_total_j": [0.0] * n2,
                      "shoot_on": [0] * n2}
        self.il = bool(p.gate_il)                       # A170 / A171: driver interlock
        self.il_thr = p.gate_il == "threshold"
        if self.il:
            self.stats.update(il_holds=[0] * n2, il_hold_max_s=0.0)
        if self.zvs_edge:                               # A206: turn-ons at V_DS <= 0 that ran as edges
            self.stats.update(zvs_edges=[0] * n2, zvs_waits=[0] * n2, zvs_offs=[0] * n2, e_zvs_j=[0.0] * n2,
                              active_zvs_s=[[math.inf, 0.0] for _ in range(n2)],
                              active_zvs_off_s=[[math.inf, 0.0] for _ in range(n2)])
        self.ls_keys = any(j >= p.n for j in self.sw)    # A169: gate-driven low sides keep their own edge times
        if self.ls_keys:
            self.stats.update({k: [math.inf, 0.0] for k in LS_KEYS})
        self._ext = None                               # (t, y at the previous step's start, gates there, h, active)

    # ---- helpers ----
    def conducts(self, j):
        """Switch j carries channel current: commanded on, or (gate-driven, A169) a turn-off not yet ended."""
        s = self.st.get(j)
        if bool((self.plant.gh + self.plant.gl)[j]):
            return True
        if s is None or s["kind"] != "off" or s["phase"] not in ("pending", "active"):
            return False
        # A206: a reverse-current turn-off conducts (for the interlock) while its gate is above the channel start
        return (not s.get("zvs")) or self.fd.i_ch(s["vgs"], self.p.gate_v_hand) >= ACT_I

    def il_update(self):
        """A170: a held turn-on whose complement stopped conducting starts gate_t_il from now."""
        n2 = 2 * p_n(self)
        for j, s in self.st.items():
            if s["phase"] == "held" and math.isinf(s["t_act"]) and not self.conducts((j + n2 // 2) % n2):
                s["t_act"] = self.plant.t + self.p.gate_t_il

    def r_tot(self, drv, j):
        return (self.r_on[j] if drv else self.p.gate_r_off) + self.rg

    def _cin(self, v, vds):
        return self.fd.cin(v, vds)

    def _relax(self, v, drv, dt, vds, j):
        """Switch j's gate voltage after dt of RC charge toward the drive (RK4 on dv/dt = (V - v) / (R C_in(v));
        within 20 mV of the drive, the exponential with C_in at the drive)."""
        vt, r = (self.p.gate_v_on if drv else 0.0), self.r_tot(drv, j)
        t = 0.0
        while t < dt and abs(vt - v) > 0.02:
            tau = r * self._cin(v, vds)
            hh = min(tau / 8, dt - t)
            f = lambda x: (vt - x) / (r * self._cin(x, vds))
            k1 = f(v); k2 = f(v + 0.5 * hh * k1); k3 = f(v + 0.5 * hh * k2); k4 = f(v + hh * k3)
            v += hh * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            t += hh
        if t < dt:
            v = vt + (v - vt) * math.exp(-(dt - t) / (r * self._cin(vt, vds)))
        return v

    def _follow(self, j, t):
        """A206 (gate_miller): switch j's idle, off-driven gate from its last update to t, with its drain's movement:
        q_g(v1, d1) - q_g(v0, d0) = -(h / 2R)(v0 + v1), V_DS linear in between, in steps of at most tau / 4;
        after more than 10 tau the gate is back at 0 V."""
        s, fd = self.st[j], self.fd
        h, d1 = t - s["t"], float(self.plant.vds(j))
        if h <= 0.0:
            return
        v, d0, r = s["vgs"], s["vds"], self.r_tot(False, j)
        tau = r * fd.cin(v, d0)
        if h > 10.0 * tau:
            s["vgs"], s["vds"], s["t"] = 0.0, d1, t
            return
        m = max(1, int(math.ceil(4.0 * h / tau)))
        hh = h / m
        for k in range(1, m + 1):
            da, db = d0 + (d1 - d0) * (k - 1) / m, d0 + (d1 - d0) * k / m
            q0 = fd.q_gate(v, da) - (0.5 * hh / r) * v
            vb = v
            for _ in range(20):
                dv = (fd.q_gate(vb, db) - q0 + (0.5 * hh / r) * vb) / (fd.cin(vb, db) + 0.5 * hh / r)
                vb -= dv
                if abs(dv) < 1e-10:
                    break
            v = vb
        s["vgs"], s["vds"], s["t"] = v, d1, t

    def _time_to(self, v, drv, v_t, vds, j):
        """Time for switch j's gate to move from v to v_t toward the drive (math.inf if it never gets there)."""
        vt, r = (self.p.gate_v_on if drv else 0.0), self.r_tot(drv, j)
        if (v_t - v) * (vt - v) <= 0:
            return 0.0
        if (vt - v_t) * (vt - v) <= 0:
            return math.inf
        t = 0.0
        while True:
            tau = r * self._cin(v, vds)
            hh = tau / 16
            f = lambda x: (vt - x) / (r * self._cin(x, vds))
            k1 = f(v); k2 = f(v + 0.5 * hh * k1); k3 = f(v + 0.5 * hh * k2); k4 = f(v + hh * k3)
            v1 = v + hh * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            if (v1 - v_t) * (v - v_t) <= 0:
                return t + hh * (v_t - v) / (v1 - v)
            v, t = v1, t + hh

    def _sync(self, j, t):
        s = self.st[j]
        if s["phase"] == "pending" and s["kind"] == "on":     # tracked step by step
            return
        if s["phase"] == "held" and s.get("frozen"):         # A171: held at the activation level
            return
        if s["phase"] != "active" and t > s["t"]:
            if self.miller and s["phase"] == "idle" and not s["drv"]:
                self._follow(j, t)
                return
            s["vgs"] = self._relax(s["vgs"], s["drv"], t - s["t"], s["vds"], j)
            s["t"] = t

    # ---- physical state ----
    def suppressed(self, j):
        """Commanded on but not (yet) conducting."""
        s = self.st.get(j)
        return s is not None and ((s["drv"] and s["phase"] in ("pending", "active")) or s["phase"] == "held")

    def forced(self, j):
        """Commanded off but still conducting (gate above the activation level)."""
        s = self.st.get(j)
        return s is not None and (not s["drv"]) and s["phase"] == "pending"

    def any_active(self):
        return any(s["phase"] == "active" for s in self.st.values())

    def active(self):
        return [j for j, s in self.st.items() if s["phase"] == "active"]

    def next_act(self):
        return min((s["t_act"] for s in self.st.values() if s["phase"] in ("pending", "held")), default=math.inf)

    def tracking(self):
        """A pending turn-on whose gate is integrated after every step."""
        return any(s["phase"] == "pending" and s["kind"] == "on" and math.isinf(s["t_act"]) for s in self.st.values())

    def track(self):
        """After a plant step: each pending turn-on's gate charge balance over the step (trapezoid),
        q_g(v1, d1) - q_g(v0, d0) = (h / 2R)(2 V - v0 - v1); due (t_act = now) once its channel carries ACT_I."""
        pl, fd = self.plant, self.fd
        if self.miller:                                # A206: idle off gates whose drain moved
            for j, s in self.st.items():
                if s["phase"] == "idle" and not s["drv"] and abs(float(pl.vds(j)) - s["vds"]) > MILLER_DV:
                    self._follow(j, pl.t)
        for j, s in self.st.items():
            if not (s["phase"] == "pending" and s["kind"] == "on" and math.isinf(s["t_act"])):
                continue
            h = pl.t - s["t"]
            if h <= 0.0:
                continue
            d1 = float(pl.vds(j))
            v0, d0, r, vt = s["vgs"], s["vds"], self.r_tot(True, j), self.p.gate_v_on
            q0 = fd.q_gate(v0, d0) + (0.5 * h / r) * (2 * vt - v0)
            v1 = v0
            for _ in range(20):
                f = fd.q_gate(v1, d1) - q0 + (0.5 * h / r) * v1
                dv = f / (fd.cin(v1, d1) + 0.5 * h / r)
                v1 -= dv
                if abs(dv) < 1e-10:
                    break
            s["vgs"], s["vds"], s["t"] = v1, d1, pl.t
            if fd.i_ch(v1, max(d1, self.p.gate_v_hand)) >= ACT_I:
                s["t_act"] = pl.t

    # ---- commands ----
    def command(self, j, level, conducting_now):
        """A gate edge on switch j at the plant's present time (before the plant's gate flags change)."""
        pl, s, d = self.plant, self.st[j], self.fd
        t = pl.t
        cb = self.next_cb.pop(j, None)
        try:
            self._command(j, level, conducting_now, pl, s, d, t)
        finally:
            if cb is not None:                         # a pending edge runs it at activation, anything else now
                if s["phase"] in ("pending", "held") and s["kind"] == "on":
                    self.on_act[j] = cb
                else:
                    cb()
            if self.il:                                # A170: this edge may end a hold / start one
                self.il_update()

    def _command(self, j, level, conducting_now, pl, s, d, t):
        self._sync(j, t)
        vds = float(pl.vds(j))
        s["drv"], s["t_cmd"], s["vds_cmd"] = bool(level), t, vds
        if s["phase"] == "active":                    # an edge in progress continues toward the new drive
            s["kind"] = "on" if level else "off"
            return
        if self.miller:                               # A206: the gate's level now belongs to this V_DS
            s["vds"] = vds
        s["phase"], s["t_act"], s["zvs"] = "idle", math.inf, False
        n = self.nsw[j]
        if level and self.il and not self.il_thr and self.conducts((j + p_n(self)) % (2 * p_n(self))):  # A170
            s.update(phase="held", kind="on", drv=False, t_act=math.inf, t_cmd0=t)
            self.stats["il_holds"][j] += 1
            return
        if level:
            if vds <= 0.0:
                self.stats["on_zvs"][j] += 1
                if not self.zvs_edge:
                    return
                s.update(phase="pending", kind="on", vds=vds, t=t, t_act=math.inf)
                if self.il and self.conducts((j + p_n(self)) % (2 * p_n(self))):   # waits as a hard turn-on does
                    self.stats["zvs_waits"][j] += 1
                    if d.i_ch(s["vgs"], self.p.gate_v_hand) >= ACT_I:
                        s["t_act"] = t
                else:                                 # A206: active from now, third-quadrant channel
                    s["t_act"], s["zvs"] = t, True
                    self.stats["zvs_edges"][j] += 1
                return
            self.stats["on"][j] += 1
            self.stats["vds_cmd_on_max_v"] = max(self.stats["vds_cmd_on_max_v"], vds)
            s.update(phase="pending", kind="on", vds=vds, t=t, t_act=math.inf)
            if d.i_ch(s["vgs"], max(vds, self.p.gate_v_hand)) >= ACT_I:
                s["t_act"] = t
        else:
            i_sw = pl.sim.g_sw[j] * vds if conducting_now else 0.0
            if i_sw <= 0.0:
                self.stats["off_rev"][j] += 1
                if self.zvs_edge and conducting_now and i_sw < 0.0:    # A206: the channel conducts until the gate
                    s.update(phase="pending", kind="off", vds=vds, i_s=i_sw / n, t_act=t, zvs=True)   # has discharged
                    self.stats["zvs_offs"][j] += 1
                return
            self.stats["off"][j] += 1
            v_act = d.vgs_for(i_sw / n, self.p.gate_v_hand)
            s.update(phase="pending", kind="off", vds=0.0, i_s=i_sw / n,
                     t_act=t + self._time_to(s["vgs"], False, v_act, 0.0, j))

    def activate_due(self):
        """Pending edges whose time has come become active (gate synced to now); returns them. A callback the bridge
        registered for the switch runs at its activation (the physical turn-on's valley measurement)."""
        pl, done = self.plant, []
        for j, s in self.st.items():                   # A170: held turn-ons whose time has come start now
            if s["phase"] == "held" and s["t_act"] <= pl.t + 1e-18 and s.get("frozen"):    # A171: activates now
                s.update(phase="pending", frozen=False, t=pl.t, vds=float(pl.vds(j)))
                self.stats["il_hold_max_s"] = max(self.stats["il_hold_max_s"], pl.t - s["t_hold"])
                self.hold_log.append((s["t_hold"], j, pl.t))
                continue
            if s["phase"] == "held" and s["t_act"] <= pl.t + 1e-18:
                t0 = s["t_cmd0"]
                s["phase"], s["t_act"] = "idle", math.inf
                self._command(j, True, False, pl, s, self.fd, pl.t)
                s["t_cmd"] = t0
                self.stats["il_hold_max_s"] = max(self.stats["il_hold_max_s"], pl.t - t0)
                self.hold_log.append((t0, j, pl.t))
                if not (s["phase"] == "pending" and s["kind"] == "on"):     # conducting at once (ZVS by now)
                    done.append(j)
                    cb = self.on_act.pop(j, None)
                    if cb is not None:
                        cb()
        for j, s in self.st.items():
            if s["phase"] == "pending" and s["t_act"] <= pl.t + 1e-18:
                if (self.il_thr and s["kind"] == "on"
                        and self.conducts((j + p_n(self)) % (2 * p_n(self)))):      # A171: wait at the threshold
                    s.update(phase="held", frozen=True, t_act=math.inf, t_hold=pl.t)
                    self.stats["il_holds"][j] += 1
                    continue
                self._sync(j, pl.t)
                s["phase"], s["t_act"], s["t_a0"] = "active", math.inf, pl.t
                vds = float(pl.vds(j))
                if s.get("zvs"):                      # A206: no gate delay; the device takes over the current there is
                    if s["kind"] == "off":
                        s["i_s"] = pl.sim.g_sw[j] * vds / self.nsw[j]
                    else:
                        isd = (-vds - self.p.rev_vf) / self.p.rev_r if (self.p.rev_drop and pl.diode[j]) else 0.0
                        s["i_s"] = -max(isd, 0.0)
                    done.append(j)
                    cb = self.on_act.pop(j, None)
                    if cb is not None:
                        cb()
                    continue
                key = _key("delay_on_s" if s["kind"] == "on" else "delay_off_s", j, p_n(self))
                dl = pl.t - s["t_cmd"]
                self.stats[key][0] = min(self.stats[key][0], dl); self.stats[key][1] = max(self.stats[key][1], dl)
                if s["kind"] == "off":                # terminal current = the conducting current now
                    s["i_s"] = pl.sim.g_sw[j] * vds / self.nsw[j]
                    if j < p_n(self):
                        ip = float(pl.y[pl.nv + j])
                        s["off_rec"] = [pl.t, j + 1, ip, ip]
                else:
                    s["i_s"] = 0.0
                    if self.conducts((j + p_n(self)) % (2 * p_n(self))):  # A164 / A169: its complement conducts
                        self.stats["shoot_on"][j] += 1
                done.append(j)
                cb = self.on_act.pop(j, None)
                if cb is not None:
                    cb()
        return done

    # ---- the coupled step ----
    def step(self, y, cond, h, euler, t0, load_on, donly, vin0, vin1, src):  # noqa: C901
        """One plant step with the active switches' channels and gates. cond has the active switches open.
        Returns y1 (the gate voltages are updated in self.st)."""
        sim, dev, p = self.plant.sim, self.fd, self.p
        act = [j for j in self.sw if self.st[j]["phase"] == "active"]
        key = (cond, h, euler, load_on, donly)
        entry = sim.cache.get(key)
        if entry is None:
            from scipy.linalg import lu_factor
            A, fv, fl, frev = sim.system(cond, load_on, donly)
            lhs, rhs_m = (sim.M - h * A, sim.M) if euler else (sim.M - 0.5 * h * A, sim.M + 0.5 * h * A)
            entry = (lu_factor(lhs), rhs_m, fv, fl, lhs, frev if (donly is not None and any(donly)) else None)
            if h == p.h:
                sim.cache[key] = entry
        _, rhs_m, fv, fl, lhs, frev = entry
        ld1 = p.load_at(t0 + h)
        f1 = fv * vin1 + fl * ld1
        if euler:
            rhs = rhs_m @ y + h * f1
        else:
            rhs = rhs_m @ y + 0.5 * h * (f1 + fv * vin0 + fl * p.load_at(t0))
        if frev is not None:
            rhs = rhs + h * frev
        if src is not None:
            rhs = rhs + src
        w1 = h if euler else 0.5 * h
        nl = sim.nl
        if nl is not None:
            r, nn, clin, m = nl["r"], nl["n"], nl["clin"], nl["model"]
            vsw0 = r @ y + nl["vin"] * vin0
            q0 = nn * m.q(vsw0)
        vin_of = lambda j, yy, vin: (vin if sim.switches[j][1] == "vin" else 0.0)
        d0 = {j: float(self.dvec[j] @ y) + vin_of(j, y, vin0) for j in act}
        for j in act:
            s = self.st[j]
            i0 = self.nsw[j] * dev.i_ch(s["vgs"], d0[j])
            if not euler:
                rhs = rhs + 0.5 * h * i0 * self.einc[j]
            s["_i0"] = i0
        qoss = (lambda j, v: self.nsw[j] * float(nl["model"].q(np.array([v]))[0])) if nl is not None else \
            (lambda j, v: (p.c_high if j < p.n else p.c_low) * v)
        coss = (lambda j, v: self.nsw[j] * float(nl["model"].c(np.array([v]))[0])) if nl is not None else \
            (lambda j, v: (p.c_high if j < p.n else p.c_low))
        ns, na = sim.ns, len(act)
        v0 = np.array([self.st[j]["vgs"] for j in act])
        ext = self._ext
        if ext is not None and ext[0] == t0 and ext[3] == h and ext[4] == act:   # linear extrapolation as the guess
            y1 = 2.0 * np.asarray(y, float) - ext[1]
            v1 = 2.0 * v0 - ext[2]
        else:
            y1 = np.array(y, float)
            v1 = v0.copy()
        lcs = p.gate_l_cs
        for it in range(1, 61):
            F = lhs @ y1 - rhs
            J = np.zeros((ns + na, ns + na))
            J[:ns, :ns] = lhs
            if nl is not None:
                vsw1 = r @ y1 + nl["vin"] * vin1
                F = F + r.T @ (nn * m.q(vsw1) - q0 - clin * (vsw1 - vsw0))
                J[:ns, :ns] += (r.T * (nn * m.c(vsw1) - clin)) @ r
            G = np.zeros(na)
            for a, j in enumerate(act):
                s, n, dv, e = self.st[j], self.nsw[j], self.dvec[j], self.einc[j]
                ds = float(dv @ y1) + vin_of(j, y1, vin1)
                ich = dev.i_ch(v1[a], ds)
                gm, gd = dev.di_ch(v1[a], ds)
                F = F - w1 * n * ich * e
                J[:ns, :ns] -= w1 * n * gd * np.outer(e, dv)
                J[:ns, ns + a] = -w1 * n * gm * e
                rr = self.r_tot(s["drv"], j)
                vdrv = p.gate_v_on if s["drv"] else 0.0
                i_s1 = ich + (qoss(j, ds) - qoss(j, d0[j])) / (h * n)
                qg1, qg0 = dev.q_gate(v1[a], ds), dev.q_gate(v0[a], d0[j])
                drive = (h / rr) * (vdrv - v1[a]) if euler else (0.5 * h / rr) * (2 * vdrv - v0[a] - v1[a])
                G[a] = qg1 - qg0 - drive + (lcs / rr) * (i_s1 - s["i_s"])
                cgd = dev.c_gd(v1[a] - ds)
                cin = dev.c_gs(v1[a]) + cgd
                J[ns + a, ns + a] = cin + (h / rr if euler else 0.5 * h / rr) + (lcs / rr) * gm
                J[ns + a, :ns] = (-cgd + (lcs / rr) * (gd + coss(j, ds) / (h * n))) * dv
                s["_ds1"], s["_ich1"], s["_is1"] = ds, ich, i_s1
            z = np.linalg.solve(J, -np.concatenate([F, G]))
            y1 = y1 + z[:ns]
            v1 = v1 + z[ns:]
            if np.abs(z[:ns]).max() < 1e-7 and (na == 0 or np.abs(z[ns:]).max() < 1e-9):
                break
        else:
            raise RuntimeError("gate edge step did not converge")
        self.stats["newton_max"] = max(self.stats["newton_max"], it)
        self.stats["steps"] += 1
        self._pending_commit = (act, v1, d0, h, t0 + h, np.array(y, float), v0)
        return y1

    def commit(self, y1, vin1):
        """After the plant accepted the step: gate states, energies, di/dt, and the end of finished edges."""
        act, v1, d0, h, t1, y0, v0 = self._pending_commit
        self._ext = (t1, y0, v0, h, act)
        pl, p, dev = self.plant, self.p, self.fd
        ended = []
        for a, j in enumerate(act):
            s = self.st[j]
            n, ds1 = self.nsw[j], s["_ds1"]
            ich1 = n * dev.i_ch(v1[a], ds1)
            e = 0.5 * h * (d0[j] * s["_i0"] + ds1 * ich1)
            pl.edge_e[j] += e; self.stats["e_total_j"][j] += e
            didt = abs(ich1 - s["_i0"]) / h * 1e-9
            k = "didt_on_max_a_ns" if s["kind"] == "on" else "didt_off_max_a_ns"
            self.stats[k] = max(self.stats[k], didt)
            s["vgs"], s["t"], s["vds"], s["i_s"] = float(v1[a]), t1, ds1, s["_is1"]
            if s.get("off_rec") is not None:
                s["off_rec"][3] = max(s["off_rec"][3], float(y1[pl.nv + j]))
            if s["drv"]:
                done = ds1 <= p.gate_v_hand
                if self.zvs_edge:                     # A206: the channel holds |V_DS| inside the hand-over level
                    done = abs(ds1) <= p.gate_v_hand and dev.i_ch(float(v1[a]), p.gate_v_hand) >= ACT_I
            else:
                done = abs(ich1) < ACT_I * n
                if self.zvs_edge and ds1 < 0.0 and v1[a] <= ZVS_OFF_V:   # A206: gate discharged in reverse conduction:
                    done = True                                         # the plant's Vf + R fit takes it from here
            if s.get("zvs"):
                self.stats["e_zvs_j"][j] += e
            if t1 - s["t_a0"] >= T_ACTIVE_MAX:
                done = True; self.stats["forced"] += 1
            if done:
                da = t1 - s["t_a0"]
                st = self.stats["active_zvs_s" if s["drv"] else "active_zvs_off_s"][j] if s.get("zvs") else \
                    self.stats[_key("active_on_s" if s["drv"] else "active_off_s", j, p_n(self))]
                st[0] = min(st[0], da); st[1] = max(st[1], da)
                s["phase"], s["zvs"] = "idle", False
                if s.get("off_rec") is not None:
                    self.off_log.append(tuple(s["off_rec"]))
                    s["off_rec"] = None
                ended.append(j)
        if self.il and (ended or (self.zvs_edge and any(self.st[j].get("zvs") and not self.st[j]["drv"] for j in act))):
            self.il_update()                           # A170: an ended turn-off may release its complement (A206: or
        return ended                                   # a reverse-current turn-off whose gate passed the channel start)

    def summary(self):
        out = dict(self.stats)
        for k in ("delay_on_s", "delay_off_s", "active_on_s", "active_off_s") + (LS_KEYS if self.ls_keys else ()):
            out[k] = [None if math.isinf(x) else x for x in out[k]]
        if self.zvs_edge:
            for k in ("active_zvs_s", "active_zvs_off_s"):
                out[k] = [[None if math.isinf(x) else x for x in a] for a in out[k]]
        out["device"], out["model_sha1"] = self.dev.name, self.dev.sha1
        return out
