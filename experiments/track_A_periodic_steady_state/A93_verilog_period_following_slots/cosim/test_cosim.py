"""A93 co-simulation bridge (copied from A92's), RTL: A93's rtl/. Addition: cfg "slot_follow" and "slot_guard"
drive the new RTL inputs (default 0); nothing else changes.

A92 docstring follows.
A92 co-simulation bridge (copied from A91's). Additions (BOUNDARY.md Section 4), RTL: A92's rtl/:
- error reports for the error-based correctors: at a low-side turn-on that came after the zero crossing,
  ml_err = actual edge - crossing; at a measured high-side turn-on that was not early, m_err = actual edge - valley
  (the minimum V_DS); both rounded to the LSB and sent with A89's reports (same valid pulses) in every run. The RTL
  uses them only with cfg "err_low" / "err_high". High-side turn-on records gain "early" and "err_s".
- cfg "err_low", "err_high", "el_tgt_ps", "eh_tgt_ps", "err_shift" drive the new RTL inputs (default 0).

A91 docstring follows.
A91 co-simulation bridge (copied from A89's). Additions (BOUNDARY.md), off unless cfg "driver" is given:
- driver model: every gate edge, including those scheduled by A81's asynchronous front end, is applied at
  t_cmd + t_drv + delta; delta = m for low-side edges (0 for high-side ones) plus an independent Gaussian jitter of
  sigma per edge (seeded);
- cross-conduction check: an applied turn-on while the same phase's complementary switch conducts is counted (time,
  phase); with cfg "stop_on_overlap" the run ends there (ideal 0.1 uOhm switches make the rest meaningless).

A89 docstring follows.
A89 co-simulation bridge (copied from A85's = A83's). Additions:
- plant: A88's simulator (a88_transient, imported read-only) instead of A79's byte copy; cfg "nonlinear_coss" and
  "rev_drop" switch on the datasheet Coss(V) and the Fig. 8 reverse drop (A88's fit). With both off the stepping is
  the old one. With rev_drop, A87's rules: reverse conduction only below V_DS = -Vf, cut above it, energy recorded.
- zero-crossing TDC (cfg "low_pred"): after each high-side turn-off, the time the low-side V_DS first reaches 0
  (interpolated within the step); at the low-side turn-on edge it reports early (not crossed) or the crossing time
  after the turn-off, rounded to the LSB, as a one-cycle pulse (ml_valid, ml_early, ml_tv) to the RTL's timed
  low side (A89). Low-side edges are recorded in every run; reports are sent only with low_pred.
- per section: reverse-conduction energy and time per switch.

A85/A83 docstring follows.
A83 co-simulation bridge (copied from A81's). Addition (cfg "learn_at_restart"): the front end also measures
after a restart turn-on (A82 / D43 corrector fix); the RTL (A81, unchanged) accepts every measurement pulse.

A81 docstring follows.
A81 co-simulation bridge (copied from A80's). Addition: the asynchronous front end of phase 1 (cfg "async"):
while the controller raises arm1, a comparator + latch fires at the plant step where i1 <= threshold; it turns
SL1 off at t + t_async + t_drv and, through the delay line (dt_pred[0]), SH1 on at t + t_async + dt_pred + t_drv;
a TDC reports t + t_async (125 ps LSB) to the controller one clock later (a_valid, a_tlo).

A80 docstring follows.
A80 co-simulation bridge (copied from A77's): the full module controller (rtl/scb_ctrl.v: mode S start-up,
handover, mode P, voltage loop) closes the loop around the A79 Python plant (cosim/plant_a79.py, an unmodified
copy of A79's a79_transient.py) from the all-zero state, with the input ramp, the load connection and the
handover request as in A73/A79, and a 12-bit ADC sample of Vo at each phase-1 turn-on.

A77 docstring follows.
A77 co-simulation bridge: the Verilog controller (rtl/scb_ctrl.v, run by Icarus Verilog) closes the loop
around the A76 Python plant.

Each clock cycle n covers the plant window [n*T_clk, (n+1)*T_clk):
1. After the rising edge, read the gate-edge requests of window n. Each edge is applied to the plant at
   (window + fine) * LSB + t_drv (gate-driver delay).
2. At the falling edge, with HDL time paused, integrate the plant through the window. Edges are applied at their
   times, with the A73 diode_check and the Euler restart after every topology change.
3. Sample the comparators at the window end and write them back; the controller's 2-FF synchroniser picks them up.
   Measurements taken at plant edges return as one-cycle pulses:
   - predictive early/late/flat and the valley time;
   - the residual-current sign for the trim.

Configuration: JSON file named by the COSIM_CFG environment variable (see run_cosim.py).
"""
import heapq
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

HERE = Path(__file__).resolve().parent
A88 = HERE.parent.parent / "A88_p24_predictive_low_side_turn_on"      # A89: the plant, read-only
sys.path.insert(0, str(A88))
from a88_transient import Params, Sim, fit_fig8  # noqa: E402

N, TW, CW = 4, 32, 8


def pack(values, width):
    out = 0
    for k, v in enumerate(values):
        out |= (int(v) & ((1 << width) - 1)) << (k * width)
    return out


def field(value, k, width):
    return (int(value) >> (k * width)) & ((1 << width) - 1)


def signed(v, width):
    return v - (1 << width) if v & (1 << (width - 1)) else v


class Plant:
    """The A76 plant stepped by the bridge. Switch order: SH1..SHN, SL1..SLN (A72 topology())."""

    def __init__(self, p, y0, gh, gl):
        self.load_on = False
        self.vds_max = [0.0] * (2 * p.n)
        self.ipk = 0.0
        self.p, self.sim, self.n = p, Sim(p), p.n
        self.nv = self.sim.nv
        self.y = np.array(y0, dtype=float)
        self.t = 0.0
        self.gh, self.gl = list(gh), list(gl)
        self.diode = [False] * (2 * self.n)
        self.euler_left = 2
        self.steps = 0
        self.v_on = -p.rev_vf if p.rev_drop else 0                    # A89: reverse turn-on / cut threshold
        self.rev_e = [0.0] * (2 * self.n); self.rev_t = [0.0] * (2 * self.n)   # A89: since the last section
        self.last_donly = [False] * (2 * self.n)

    def gates(self):
        return self.gh + self.gl

    def vds(self, j):
        return self.sim.vds(self.y, j, self.p.vin_at(self.t))

    def _advance(self, h):
        """One step with A73's diode_check: a diode-only branch whose Vds ends > 0 is cut and the step redone."""
        n, g = self.n, self.gates()
        d = list(self.diode)
        euler = self.euler_left > 0
        for _ in range(2 * n + 1):
            cond = tuple(bool(a or b) for a, b in zip(g, d))
            donly = tuple(bool(b and not a) for a, b in zip(g, d)) if self.p.rev_drop else None   # A89
            y1 = self.sim.step(self.y, cond, h, euler, self.t, self.load_on, donly)
            vin1 = self.p.vin_at(self.t + h)
            bad = [j for j in range(2 * n) if d[j] and not g[j] and self.sim.vds(y1, j, vin1) > self.v_on]
            if not bad:
                break
            for j in bad:
                d[j] = False
        if d != self.diode:
            self.diode = d
            self.euler_left = 2
        self.last_donly = list(donly) if donly is not None else [False] * (2 * n)
        self.y = y1
        self.t += h
        self.euler_left = max(0, self.euler_left - 1)
        vd = [self.sim.vds(self.y, j, self.p.vin_at(self.t)) for j in range(2 * n)]
        if self.p.rev_drop:                                          # A89: reverse-conduction energy (A87)
            for j in range(2 * n):
                if self.last_donly[j]:
                    isd = self.sim.nsw[j] * (-vd[j] - self.p.rev_vf) / self.p.rev_r
                    if isd > 0:
                        self.rev_e[j] += -vd[j] * isd * h; self.rev_t[j] += h
        self.vds_max = [max(a, b) for a, b in zip(self.vds_max, vd)]          # peak Vds per switch
        self.ipk = max(self.ipk, float(np.max(np.abs(self.y[self.nv:]))))     # peak phase current
        new_d = [(not g[j]) and vd[j] < self.v_on for j in range(2 * n)]
        if new_d != self.diode:
            self.diode = new_d
            self.euler_left = 2
        self.steps += 1

    def integrate_to(self, t_target, on_step):
        while self.t < t_target - 1e-18:
            self._advance(min(self.p.h, t_target - self.t))
            on_step()

    def set_gate(self, j, level):
        if j < self.n:
            self.gh[j] = bool(level)
        else:
            self.gl[j - self.n] = bool(level)
        self.euler_left = 2


@cocotb.test()
async def cosim(dut):
    cfg_path = Path(os.environ["COSIM_CFG"])
    cfg = json.loads(cfg_path.read_text())
    ref = json.loads((cfg_path.parent / cfg["init_run"]).resolve().read_text())
    t_clk = cfg["t_clk_ns"] * 1e-9
    fb = int(cfg["fb"])
    lsb = t_clk / (1 << fb)
    t_drv = cfg["t_drv_ns"] * 1e-9
    i_tgt, lsb_a, v_hys = cfg["i_target"], cfg["trim_lsb_a"], cfg["v_hys"]
    to_lsb = lambda s: int(round(s / lsb))

    # Plant: the reference (Python) run's P24 circuit and sequence, from the all-zero state with phase 1 HIGH
    # and phases 2..N LOW (A73's initial state, which the controller's reset assumes).
    pr = ref["params"]
    keep = ("n", "vin", "L", "R", "c_high", "c_low", "cs", "co", "load_kind", "r_load", "i_load", "g_on", "h",
            "t_ramp", "t_load", "t_hand")
    extra = {}
    if cfg.get("nonlinear_coss", 0):                                  # A89: device realism of A86-A88
        extra["nonlinear_coss"] = True
    if cfg.get("rev_drop", 0):
        vf, rr, _ = fit_fig8(10.0, 100.0)
        extra.update(rev_drop=True, rev_vf=vf, rev_r=rr)
    p = Params(**{k: pr[k] for k in keep}, diode_check=True, **extra)
    plant = Plant(p, [0.0] * (Sim(p).nv + N), gh=[True] + [False] * (N - 1), gl=[False] + [True] * (N - 1))
    nv = plant.nv
    io = plant.sim.idx["out"]
    adc_lsb, adc_max = cfg["adc_lsb_v"], (1 << 12) - 1

    # Controller initial registers: the predictive delay starts at half the node resonance period, as in
    # the Python rule; the trim codes start at 0 (threshold = target).
    dt_init = [to_lsb(cfg["dt_init_ns"] * 1e-9)] * N
    trim_init = [0] * N

    cocotb.start_soon(Clock(dut.clk, cfg["t_clk_ns"], unit="ns").start())
    dut.rst.value = 1
    dut.cfg_ton.value = to_lsb(cfg["ton_ns"] * 1e-9)
    dut.cfg_rs_high.value = to_lsb(cfg["rs_high_ns"] * 1e-9)
    dut.cfg_rs_low.value = to_lsb(cfg["rs_low_ns"] * 1e-9)
    dut.cfg_dt_step.value = max(1, to_lsb(cfg["dt_step_ns"] * 1e-9))
    dut.cfg_dt_max.value = to_lsb(cfg["dt_max_ns"] * 1e-9)
    dut.cfg_slot.value = pack([to_lsb(k * cfg["t0_ns"] * 1e-9 / N) for k in range(1, N)], TW)
    dut.cfg_pred.value = 1
    dut.cfg_zvs_react.value = 0
    dut.cfg_trim.value = int(cfg["trim"])
    dut.cfg_fine.value = int(cfg["fine"])
    dut.dt_init.value = pack(dt_init, TW)
    dut.trim_init.value = pack(trim_init, CW)
    for s in ("cmp_i", "cmp_zl", "cmp_zh", "cmp_valley", "m_valid", "m_early", "m_flat", "r_valid", "r_below"):
        getattr(dut, s).value = 0
    dut.m_tv.value = 0
    dut.cfg_start_s.value = 1
    dut.hand_req.value = 0
    dut.cfg_t0.value = to_lsb(cfg["t0_ns"] * 1e-9)
    dut.cfg_tdead.value = to_lsb(cfg["tdead_ns"] * 1e-9)
    dut.cfg_ton_min.value = to_lsb(0.5 * cfg["ton_ns"] * 1e-9)
    dut.cfg_ton_max.value = to_lsb(2.0 * cfg["ton_ns"] * 1e-9)
    dut.cfg_vloop.value = int(cfg["vloop"])
    dut.cfg_vref_code.value = int(round(cfg["vref_v"] / adc_lsb))
    # ki in ns of Ton per V -> Ton LSB per ADC LSB, 16 fractional bits
    dut.cfg_ki.value = int(round(cfg["ki_ns_per_v"] * adc_lsb / (lsb * 1e9) * 65536))
    dut.adc_valid.value = 0
    dut.adc_code.value = 0
    dut.cfg_low_pred.value = int(cfg.get("low_pred", 0))            # A89
    dut.dtl_init.value = pack([to_lsb(cfg.get("dtl_init_ns", 2.15) * 1e-9)] * N, TW)
    dut.cfg_dtl_step.value = max(1, to_lsb(cfg.get("dtl_step_ns", 0.05) * 1e-9))
    dut.cfg_dtl_max.value = to_lsb(cfg.get("dtl_max_ns", 10.0) * 1e-9)
    dut.ml_valid.value = 0; dut.ml_early.value = 0; dut.ml_tv.value = 0
    dut.cfg_err_low.value = int(cfg.get("err_low", 0))               # A92
    dut.cfg_err_high.value = int(cfg.get("err_high", 0))
    dut.cfg_el_tgt.value = to_lsb(cfg.get("el_tgt_ps", 0.0) * 1e-12)
    dut.cfg_eh_tgt.value = to_lsb(cfg.get("eh_tgt_ps", 0.0) * 1e-12)
    dut.cfg_err_shift.value = int(cfg.get("err_shift", 0))
    dut.ml_err.value = 0; dut.m_err.value = 0
    dut.cfg_slot_follow.value = int(cfg.get("slot_follow", 0))        # A93
    dut.cfg_slot_guard.value = int(cfg.get("slot_guard", 0))
    dut.cfg_blank.value = to_lsb(cfg.get("blank_ns", 0.0) * 1e-9)     # A89 amendment: comparator blanking
    dut.cfg_async.value = int(cfg.get("async", 0))
    dut.a_valid.value = 0
    dut.a_tlo.value = 0
    t_async = cfg.get("t_async_ns", 1.0) * 1e-9
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    # Plant-side bookkeeping for the comparators and the measurements.
    vmin = [None] * N; t_vmin = [None] * N; v_lo = [None] * N; t_lo_act = [None] * N
    pend = []                                   # heap of (t_apply, seq, j, level, meta)
    seq = [0]
    meas_m = {}; meas_r = {}                    # phase -> measurement to deliver
    adc = []                                     # pending ADC sample of Vo (taken at phase 1's turn-on)
    st = {"mode_p": 0, "ton": 0, "t_mode_p": None}
    lat = {"armed": False, "fired": False, "dt0": 0, "report": None, "fires": 0}   # A81 front end of phase 1
    sections, turnons, lowoffs = [], [], []
    drv = cfg.get("driver")                                      # A91: driver timing model
    rng = np.random.default_rng(int(drv.get("seed", 1))) if drv else None
    ovl = {"count": 0, "first": None, "stop": False}

    def t_apply(t_cmd, j):
        """A91: the time the plant sees an edge commanded at t_cmd on switch j."""
        if not drv:
            return t_cmd + t_drv
        d = t_drv + (drv.get("m_ns", 0.0) * 1e-9 if j >= N else 0.0)
        if drv.get("sigma_ps", 0.0) > 0.0:
            d += rng.normal(0.0, drv["sigma_ps"] * 1e-12)
        return t_cmd + d
    t_hoff = [None] * N; t_cross = [None] * N; v_prev = [None] * N; t_prev = [None] * N   # A89: zero-crossing TDC
    meas_l = {}; lowons = []
    trim_now = list(trim_init)
    t_end = cfg["t_end_us"] * 1e-6
    t0w = time.time()

    def on_step():
        if lat["armed"] and not lat["fired"] and plant.y[nv] <= i_tgt + trim_now[0] * lsb_a:   # A81 latch fires
            lat["fired"] = True; lat["fires"] += 1
            t_cmd = plant.t + t_async
            heapq.heappush(pend, (t_apply(t_cmd, N + 0), seq[0], N + 0, 0, {"how": None, "bind": True})); seq[0] += 1
            heapq.heappush(pend, (t_apply(t_cmd + lat["dt0"] * lsb, 0), seq[0], 0, 1, {"how": 0, "bind": False})); seq[0] += 1
            lat["report"] = int(round(t_cmd / lsb))
        for k in range(N):                                      # A89: first V_DS(SL_k) <= 0 after the turn-off
            if t_hoff[k] is not None and t_cross[k] is None and not plant.gh[k] and not plant.gl[k]:
                v = plant.vds(N + k)
                if v <= 0.0:
                    vp, tp = v_prev[k], t_prev[k]
                    t_cross[k] = (tp + (plant.t - tp) * vp / (vp - v)) if (vp is not None and vp > 0.0) else plant.t
                v_prev[k] = v; t_prev[k] = plant.t
        for k in range(N):
            if vmin[k] is not None and not plant.gh[k] and not plant.gl[k]:
                v = plant.vds(k)
                if v < vmin[k]:
                    vmin[k] = v; t_vmin[k] = plant.t

    dbg = cfg.get("debug_edges_us")                            # A89 diagnostics only: log every applied edge
    edges_log = []

    def apply(j, level, meta):
        k = j % N
        if level and (plant.gl[k] if j < N else plant.gh[k]):   # A91: turn-on against a conducting complement
            ovl["count"] += 1
            if ovl["first"] is None:
                ovl["first"] = {"t_s": plant.t, "phase": k + 1, "switch": "SH" if j < N else "SL", "mode_p": st["mode_p"]}
            if cfg.get("stop_on_overlap", 0):
                ovl["stop"] = True
        if dbg and dbg[0] * 1e-6 <= plant.t <= dbg[1] * 1e-6:
            edges_log.append({"t_s": plant.t, "j": j, "level": int(level), "mode_p": st["mode_p"],
                              "vds": [round(plant.vds(q), 3) for q in range(2 * N)],
                              "i": [round(float(x), 2) for x in plant.y[nv:]], "gh": list(plant.gh), "gl": list(plant.gl)})
        if j < N and level:                     # high-side turn-on edge
            v = plant.vds(k)
            rec = {"t_s": plant.t, "phase": k + 1, "how": meta["how"], "vds_v": float(v),
                   "i_a": float(plant.y[nv + k])}
            turnons.append(rec)
            if (meta["how"] == 0 or (meta["how"] == 3 and cfg.get("learn_at_restart", 0))) and vmin[k] is not None:
                # early: the minimum was lowered by the step that landed on this edge (node still falling),
                # the same test as A75's "Vds at the edge below the minimum of the previous steps"
                early = t_vmin[k] is not None and abs(t_vmin[k] - plant.t) < 1e-15 and t_vmin[k] > t_lo_act[k]
                dip = vmin[k] < v_lo[k] - v_hys and t_vmin[k] > t_lo_act[k]
                err = 0 if early else max(0, to_lsb(plant.t - t_vmin[k]))      # A92: edge - valley
                meas_m[k] = (early, not early and not dip, max(0, to_lsb(t_vmin[k] - t_lo_act[k])), err)
                rec["early"] = bool(early); rec["err_s"] = None if early else plant.t - t_vmin[k]
            vmin[k] = None
            if k == 0:
                vo, vin = float(plant.y[io]), p.vin_at(plant.t)
                ia = [plant.sim.idx[f"a{q}"] for q in range(1, N)]; ix = [plant.sim.idx[f"x{q}"] for q in range(1, N)]
                sections.append({"t_s": plant.t, "v": plant.y[:nv].tolist(), "i": plant.y[nv:].tolist(),
                                 "vo": vo, "vin_v": vin, "mode_p": st["mode_p"], "ton_lsb": st["ton"],
                                 "vcs_v": [float(plant.y[a] - plant.y[x]) for a, x in zip(ia, ix)],
                                 "rev_energy_j": list(plant.rev_e), "rev_time_s": list(plant.rev_t)})   # A89
                plant.rev_e = [0.0] * (2 * N); plant.rev_t = [0.0] * (2 * N)
                adc.append(min(max(int(round(vo / adc_lsb)), 0), adc_max))
        if j < N and not level:                 # A89: high-side turn-off edge starts the zero-crossing TDC
            t_hoff[k] = plant.t; t_cross[k] = None; v_prev[k] = None; t_prev[k] = None
        if j >= N and level and t_hoff[k] is not None:    # A89: low-side turn-on edge
            crossed = t_cross[k] is not None
            rel = (t_cross[k] - t_hoff[k]) if crossed else None
            lowons.append({"t_s": plant.t, "phase": k + 1, "vds_v": float(plant.vds(N + k)), "mode_p": st["mode_p"],
                           "crossed": crossed, "t_cross_rel_s": rel, "t_since_off_s": plant.t - t_hoff[k]})
            if cfg.get("low_pred", 0) and st["mode_p"]:
                meas_l[k] = (not crossed, 0 if not crossed else max(0, to_lsb(rel)),
                             0 if not crossed else max(0, to_lsb(plant.t - t_cross[k])))      # A92: edge - crossing
            t_hoff[k] = None; t_cross[k] = None
        if j >= N and not level:                # low-side turn-off edge
            i_e = float(plant.y[nv + k])
            lowoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": i_e, "bind_cur": meta["bind"]})
            if meta["bind"]:
                meas_r[k] = i_e < i_tgt
            vmin[k] = v_lo[k] = plant.vds(k); t_vmin[k] = t_lo_act[k] = plant.t
        plant.set_gate(j, level)

    while plant.t < t_end and not ovl["stop"]:
        await RisingEdge(dut.clk)
        await ReadOnly()
        w = int(dut.win_q.value)
        how = int(dut.on_how.value); bind = int(dut.lo_bind_cur.value)
        trim_now = [signed(field(dut.trim.value, k, CW), CW) for k in range(N)]
        st["ton"] = int(dut.ton_now.value)
        if int(dut.mode_p.value) and not st["mode_p"]:
            st["t_mode_p"] = w * lsb
        st["mode_p"] = int(dut.mode_p.value)
        if int(dut.arm1.value):
            lat["armed"] = True
        else:
            lat["armed"] = False; lat["fired"] = False
        lat["dt0"] = field(dut.dt_pred.value, 0, TW)
        for k in range(N):
            for gate, ev, lvl, fine in (("H", dut.gh_ev, dut.gh_lvl, dut.gh_fine), ("L", dut.gl_ev, dut.gl_lvl, dut.gl_fine)):
                if field(ev.value, k, 1):
                    t_cmd = (w + field(fine.value, k, fb)) * lsb
                    j = k if gate == "H" else N + k
                    meta = {"how": field(how, k, 3), "bind": bool(field(bind, k, 1))}
                    heapq.heappush(pend, (t_apply(t_cmd, j), seq[0], j, field(lvl.value, k, 1), meta))
                    seq[0] += 1
        await FallingEdge(dut.clk)
        # one-cycle measurement pulses from the previous window
        mv = me = mf = rv = rb = 0; mtv = [0] * N; merr = [0] * N
        for k, (early, flat, tv, err) in meas_m.items():
            mv |= 1 << k; me |= int(early) << k; mf |= int(flat) << k; mtv[k] = tv; merr[k] = err
        for k, below in meas_r.items():
            rv |= 1 << k; rb |= int(below) << k
        ml_v = ml_e = 0; ml_t = [0] * N; ml_r = [0] * N             # A89: zero-crossing reports (A92: + error)
        for k, (early, tv, err) in meas_l.items():
            ml_v |= 1 << k; ml_e |= int(early) << k; ml_t[k] = tv; ml_r[k] = err
        meas_l.clear()
        dut.ml_valid.value = ml_v; dut.ml_early.value = ml_e; dut.ml_tv.value = pack(ml_t, TW)
        dut.ml_err.value = pack(ml_r, TW); dut.m_err.value = pack(merr, TW)
        meas_m.clear(); meas_r.clear()
        dut.m_valid.value = mv; dut.m_early.value = me; dut.m_flat.value = mf; dut.m_tv.value = pack(mtv, TW)
        dut.r_valid.value = rv; dut.r_below.value = rb
        dut.a_valid.value = int(lat["report"] is not None)
        dut.a_tlo.value = lat["report"] or 0
        lat["report"] = None
        dut.adc_valid.value = int(bool(adc))
        dut.adc_code.value = adc[-1] if adc else 0
        adc.clear()
        dut.hand_req.value = int(plant.t >= p.t_hand)
        plant.load_on = plant.t >= p.t_load
        # plant through window [w, w + 2^fb) LSB
        t_win_end = (w + (1 << fb)) * lsb
        while pend and pend[0][0] < t_win_end:
            ta, _, j, lvl, meta = heapq.heappop(pend)
            plant.integrate_to(ta, on_step)
            apply(j, lvl, meta)
            if ovl["stop"]:                                     # A91: no integration through a shoot-through
                break
        if ovl["stop"]:
            break
        plant.integrate_to(t_win_end, on_step)
        # comparators sampled at the window end
        ci = czl = czh = cva = 0
        for k in range(N):
            ci |= int(plant.y[nv + k] <= i_tgt + trim_now[k] * lsb_a) << k
            czl |= int(plant.vds(N + k) <= 0.0) << k
            czh |= int(plant.vds(k) <= 0.0) << k
            if vmin[k] is not None:
                cva |= int(plant.vds(k) >= vmin[k] + v_hys) << k
        dut.cmp_i.value = ci; dut.cmp_zl.value = czl; dut.cmp_zh.value = czh; dut.cmp_valley.value = cva

    await RisingEdge(dut.clk)
    await ReadOnly()
    out = {"cfg": cfg, "t_end_s": plant.t, "steps": plant.steps, "wall_s": time.time() - t0w,
           "late_fires": [field(dut.late_fires.value, k, 16) for k in range(N)],
           "trim_final": [signed(field(dut.trim.value, k, CW), CW) for k in range(N)],
           "dt_pred_final_ns": [field(dut.dt_pred.value, k, TW) * lsb * 1e9 for k in range(N)],
           "t_mode_p_s": st["t_mode_p"], "ton_final_lsb": int(dut.ton_now.value), "lsb_s": lsb,
           "vds_max_v": plant.vds_max, "ipk_a": plant.ipk, "async_fires": lat["fires"],
           "sections": sections, "turnons_last": turnons[-1000:], "lowoffs_last": lowoffs[-1000:],
           "dtl_final_ns": [field(dut.dtl.value, k, TW) * lsb * 1e9 for k in range(N)],     # A89
           "edges_log": edges_log, "driver": drv, "overlaps": ovl["count"], "first_overlap": ovl["first"],
           "status": "OVERLAP_STOP" if ovl["stop"] else "COMPLETED", "lowons_last": lowons[-1000:], "plant_flags": {"nonlinear_coss": p.nonlinear_coss, "rev_drop": p.rev_drop,
                                                            "rev_vf": p.rev_vf, "rev_r": p.rev_r}}
    (cfg_path.parent / cfg["out"]).write_text(json.dumps(out))
    dut._log.info(f"co-sim done: t {plant.t * 1e6:.2f} us, {len(sections)} sections, wall {out['wall_s']:.0f} s")
