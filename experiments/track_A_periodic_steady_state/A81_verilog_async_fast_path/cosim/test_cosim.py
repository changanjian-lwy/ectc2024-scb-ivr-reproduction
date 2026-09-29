"""A81 co-simulation bridge (copied from A80's). Addition: the asynchronous front end of phase 1 (cfg "async"):
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
sys.path.insert(0, str(HERE))
from plant_a79 import Params, Sim  # noqa: E402

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
            y1 = self.sim.step(self.y, cond, h, euler, self.t, self.load_on)
            vin1 = self.p.vin_at(self.t + h)
            bad = [j for j in range(2 * n) if d[j] and not g[j] and self.sim.vds(y1, j, vin1) > 0]
            if not bad:
                break
            for j in bad:
                d[j] = False
        if d != self.diode:
            self.diode = d
            self.euler_left = 2
        self.y = y1
        self.t += h
        self.euler_left = max(0, self.euler_left - 1)
        vd = [self.sim.vds(self.y, j, self.p.vin_at(self.t)) for j in range(2 * n)]
        self.vds_max = [max(a, b) for a, b in zip(self.vds_max, vd)]          # peak Vds per switch
        self.ipk = max(self.ipk, float(np.max(np.abs(self.y[self.nv:]))))     # peak phase current
        new_d = [(not g[j]) and vd[j] < 0 for j in range(2 * n)]
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
    p = Params(**{k: pr[k] for k in keep}, diode_check=True)
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
    trim_now = list(trim_init)
    t_end = cfg["t_end_us"] * 1e-6
    t0w = time.time()

    def on_step():
        if lat["armed"] and not lat["fired"] and plant.y[nv] <= i_tgt + trim_now[0] * lsb_a:   # A81 latch fires
            lat["fired"] = True; lat["fires"] += 1
            t_cmd = plant.t + t_async
            heapq.heappush(pend, (t_cmd + t_drv, seq[0], N + 0, 0, {"how": None, "bind": True})); seq[0] += 1
            heapq.heappush(pend, (t_cmd + lat["dt0"] * lsb + t_drv, seq[0], 0, 1, {"how": 0, "bind": False})); seq[0] += 1
            lat["report"] = int(round(t_cmd / lsb))
        for k in range(N):
            if vmin[k] is not None and not plant.gh[k] and not plant.gl[k]:
                v = plant.vds(k)
                if v < vmin[k]:
                    vmin[k] = v; t_vmin[k] = plant.t

    def apply(j, level, meta):
        k = j % N
        if j < N and level:                     # high-side turn-on edge
            v = plant.vds(k)
            rec = {"t_s": plant.t, "phase": k + 1, "how": meta["how"], "vds_v": float(v),
                   "i_a": float(plant.y[nv + k])}
            turnons.append(rec)
            if meta["how"] == 0 and vmin[k] is not None:     # predictive: early / late / flat
                # early: the minimum was lowered by the step that landed on this edge (node still falling),
                # the same test as A75's "Vds at the edge below the minimum of the previous steps"
                early = t_vmin[k] is not None and abs(t_vmin[k] - plant.t) < 1e-15 and t_vmin[k] > t_lo_act[k]
                dip = vmin[k] < v_lo[k] - v_hys and t_vmin[k] > t_lo_act[k]
                meas_m[k] = (early, not early and not dip, max(0, to_lsb(t_vmin[k] - t_lo_act[k])))
            vmin[k] = None
            if k == 0:
                vo, vin = float(plant.y[io]), p.vin_at(plant.t)
                ia = [plant.sim.idx[f"a{q}"] for q in range(1, N)]; ix = [plant.sim.idx[f"x{q}"] for q in range(1, N)]
                sections.append({"t_s": plant.t, "v": plant.y[:nv].tolist(), "i": plant.y[nv:].tolist(),
                                 "vo": vo, "vin_v": vin, "mode_p": st["mode_p"], "ton_lsb": st["ton"],
                                 "vcs_v": [float(plant.y[a] - plant.y[x]) for a, x in zip(ia, ix)]})
                adc.append(min(max(int(round(vo / adc_lsb)), 0), adc_max))
        if j >= N and not level:                # low-side turn-off edge
            i_e = float(plant.y[nv + k])
            lowoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": i_e, "bind_cur": meta["bind"]})
            if meta["bind"]:
                meas_r[k] = i_e < i_tgt
            vmin[k] = v_lo[k] = plant.vds(k); t_vmin[k] = t_lo_act[k] = plant.t
        plant.set_gate(j, level)

    while plant.t < t_end:
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
                    heapq.heappush(pend, (t_cmd + t_drv, seq[0], j, field(lvl.value, k, 1), meta))
                    seq[0] += 1
        await FallingEdge(dut.clk)
        # one-cycle measurement pulses from the previous window
        mv = me = mf = rv = rb = 0; mtv = [0] * N
        for k, (early, flat, tv) in meas_m.items():
            mv |= 1 << k; me |= int(early) << k; mf |= int(flat) << k; mtv[k] = tv
        for k, below in meas_r.items():
            rv |= 1 << k; rb |= int(below) << k
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
           "sections": sections, "turnons_last": turnons[-1000:], "lowoffs_last": lowoffs[-1000:]}
    (cfg_path.parent / cfg["out"]).write_text(json.dumps(out))
    dut._log.info(f"co-sim done: t {plant.t * 1e6:.2f} us, {len(sections)} sections, wall {out['wall_s']:.0f} s")
