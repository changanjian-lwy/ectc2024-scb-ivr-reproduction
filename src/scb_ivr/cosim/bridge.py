"""Co-simulation bridge: the Verilog controller (rtl/, run by Icarus Verilog through cocotb) closes the loop around
the P24 plant (plant.py, selected by cfg "plant_impl": "kernel2" (default, C step loop), "kernel", "fast" or
"reference"; all bit-identical).
Run through run.py. Configuration: the JSON file named by COSIM_CFG; optional overrides from run.py: COSIM_OUT
(output path), COSIM_T_END_US (stop time), COSIM_PROVENANCE (JSON added to the output). An output path ending in
".gz" is written gzip-compressed. Derived from A94's bridge (see CHANGELOG.md); the loop itself is unchanged.

Time base. Each 4 ns clock cycle n covers the plant window [n*T_clk, (n+1)*T_clk), LSB = T_clk / 2^fb:
1. after the rising edge the bridge reads the controller's gate-edge requests of window n and schedules each at
   t_cmd + t_drv (+ the optional driver model), t_cmd = (window + fine) * LSB;
2. at the falling edge, with HDL time paused, it integrates the plant through the window, applying the edges at
   their times (A73's diode_check; Euler restart after every topology change);
3. it samples the comparators at the window end (current <= target + trim, low/high V_DS <= 0, valley) and writes
   them back; measurements taken at plant edges return as one-cycle pulses in the next window.

Plant (cfg): the circuit of the run named by "init_run" (A79 r1: P24, resistive load), from the all-zero state, phase
1 HIGH and phases 2..N LOW, input ramp, load connection at t_load and handover request at t_hand (cfg "t_load_us" /
"t_hand_us" override them, A103); "nonlinear_coss" (datasheet Coss(V), A86) and "rev_drop" (Fig. 8 reverse
conduction Vf + R per device, A87; reverse energy and time recorded per section).

Controller-side analog functions modelled here:
- phase 1's asynchronous front end ("async"): while arm1 is high, a latch fires at the plant step where
  i1 <= target + trim; it turns SL1 off at t + t_async + t_drv and SH1 on dt_pred later, and a TDC reports
  t + t_async (a_valid, a_tlo);
- the predictive-valley measurement at each predictive turn-on (and at restart turn-ons with "learn_at_restart"):
  early / flat / valley time after the actual low-side turn-off (m_valid, m_early, m_flat, m_tv) and the error of
  the actual edge against the valley (m_err);
- the zero-crossing TDC of the timed low side ("low_pred", mode P): at each low-side turn-on, early or the crossing
  time after the actual high-side turn-off (ml_valid, ml_early, ml_tv) and the edge's error against the crossing
  (ml_err);
- the residual-current sign at current-decided turn-offs (trim) and a 12-bit ADC sample of Vo at each phase-1
  turn-on (voltage loop).

Driver model ("driver", optional): low-side edges m later than high-side ones, plus independent Gaussian jitter of
sigma per edge (seeded), on every edge or, with "jitter_edges" "high" / "low", on that side's edges only; a turn-on
applied while the same phase's complement conducts is counted, and with "stop_on_overlap" the run ends there.

RTL configuration from cfg: timing (ton, t0, tdead, restarts, dt_init/step/max), trim, fine, voltage loop (ki; kp
from A104), async, low_pred (dtl_init/step/max), blank, the error-based correctors (err_low, err_high, el_tgt_ps,
eh_tgt_ps, err_shift), the slot rules (slot_follow, slot_guard, slot_avg) and the timed phase-1 turn-off (lo_pred,
lo_learn, lo_tgt_ps, lo_adm, lo_smax, lo_ff, lo_kff; the bridge then measures phase 1's crossing of i_target and
reports it at the turn-off); keys absent from cfg take the values that reproduce the earlier experiments.

Output (cfg "out"): sections at every phase-1 turn-on (state, Vo, Ton, flying-capacitor voltages, reverse energy),
the last 1000 turn-ons, low-side turn-offs and turn-ons, the controller's final registers, peak V_DS and current,
plant steps and wall time, driver/overlap status (cfg "records_last", default 1000, sets the record lengths).
Load step (cfg "load_step" {"t_us", "i_a"}, A100): i_a drawn from the output from t_us on, on top of the load.
Auxiliary commutation branches (cfg "aux" {"lr_nh", "alpha", "rds_on_mohm" 1.3, "r_lr_mohm" 0.2, "cm_uf" 1.0,
"vm0_v" 0.0 (or one per branch), "phases" 1..N, "valley_zero" 0, "t_en_us" 0}, A101, A102): per phase Lr and a
bidirectional switch (2 dies of alpha x EPC2067 in series, 2 RDS(on) / alpha) from Cm (precharged to vm0_v) to x_k,
switched with the low side complemented and opening at zero current; with t_en_us > 0 the branches stay open until
the first window at or after t_en_us and each starts at its next low-side turn-off; with "valley_zero" 1 the high
side's valley measurement stops at its first V_DS <= 0 (in A101 this made the turn-off currents of phases 2-4
unstable; the plain valley measurement is stable). Sections add Cm's voltages and each branch's int i^2 dt and
extremes since the last section. Every run records the phase current (and
the branch current, 0 without one) at each high-side turn-off ("highoffs_last").
"""
import gzip
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
sys.path.insert(0, str(HERE.parents[1]))                              # src/, for the package
from scb_ivr.cosim.circuit import PROJECT, fit_fig8  # noqa: E402
from scb_ivr.cosim.circuit import CircuitParams as Params  # noqa: E402
from scb_ivr.cosim.plant import FastPlant, KernelPlant, KernelPlant2, Monitors, ReferencePlant  # noqa: E402
PLANTS = {"kernel": KernelPlant, "kernel2": KernelPlant2, "fast": FastPlant, "reference": ReferencePlant}

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


@cocotb.test()
async def cosim(dut):
    prof = None
    if os.environ.get("COSIM_PROFILE"):                                 # optional: cProfile of the whole run
        import cProfile
        prof = cProfile.Profile(); prof.enable()
    cfg_path = Path(os.environ["COSIM_CFG"])
    cfg = json.loads(cfg_path.read_text())
    init = (cfg_path.parent / cfg["init_run"]).resolve()
    if not init.exists():                                              # presets name it relative to the project
        init = (PROJECT / cfg["init_run"]).resolve()
    ref = json.loads(init.read_text())
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
    for key, name in (("t_load_us", "t_load"), ("t_hand_us", "t_hand")):  # A103: start-up sequence timing
        if key in cfg:
            extra[name] = float(cfg[key]) * 1e-6
    if cfg.get("load_step"):                                          # A100: a load current step
        extra.update(i_step=float(cfg["load_step"]["i_a"]), t_step=float(cfg["load_step"]["t_us"]) * 1e-6)
    aux = cfg.get("aux")                                              # A101: auxiliary commutation branches
    if aux:
        r_bds = 2 * aux.get("rds_on_mohm", 1.3) * 1e-3 / aux["alpha"]
        extra.update(aux_phases=tuple(aux.get("phases", range(1, N + 1))), aux_l=aux["lr_nh"] * 1e-9,
                     aux_r=r_bds + aux.get("r_lr_mohm", 0.2) * 1e-3, aux_c=aux.get("cm_uf", 1.0) * 1e-6,
                     aux_vm0=tuple(aux["vm0_v"]) if isinstance(aux.get("vm0_v"), list) else aux.get("vm0_v", 0.0))
    p = Params(**{k: pr[k] for k in keep if k not in extra}, diode_check=True, **extra)
    na = len(p.aux_phases)
    vm0 = list(p.aux_vm0) if isinstance(p.aux_vm0, (list, tuple)) else [p.aux_vm0] * na   # A102: per branch
    y0 = [0.0] * (2 * N) + vm0 + [0.0] * N + [0.0] * na   # 2N node voltages (+ Cm nodes), N currents (+ branches)
    plant = PLANTS[cfg.get("plant_impl", "kernel2")](p, y0, gh=[True] + [False] * (N - 1), gl=[False] + [True] * (N - 1))
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
    dut.cfg_kp.value = int(round(cfg.get("kp_ns_per_v", 0.0) * adc_lsb / (lsb * 1e9) * 65536))   # A104
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
    dut.cfg_slot_avg.value = int(cfg.get("slot_avg", 0))              # A97
    dut.cfg_lo_pred.value = int(cfg.get("lo_pred", 0))                # A99: timed phase-1 turn-off
    dut.cfg_lo_learn.value = int(cfg.get("lo_learn", 0))
    dut.cfg_lo_tgt.value = to_lsb(cfg.get("lo_tgt_ps", 0.0) * 1e-12)
    dut.mlo_valid.value = 0; dut.mlo_early.value = 0; dut.mlo_err.value = 0
    dut.cfg_lo_adm.value = int(cfg.get("lo_adm", 0))                  # A100: adaptive dlo step
    dut.cfg_lo_smax.value = int(cfg.get("lo_smax", 0))
    dut.cfg_lo_ff.value = int(cfg.get("lo_ff", 0))                    # A100: Ton feedforward to dlo
    dut.cfg_lo_kff.value = int(cfg.get("lo_kff", 0))
    dut.cfg_blank.value = to_lsb(cfg.get("blank_ns", 0.0) * 1e-9)     # A89 amendment: comparator blanking
    dut.cfg_async.value = int(cfg.get("async", 0))
    dut.a_valid.value = 0
    dut.a_tlo.value = 0
    t_async = cfg.get("t_async_ns", 1.0) * 1e-9
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    # Plant-side bookkeeping for the comparators and the measurements.
    v_lo = [None] * N; t_lo_act = [None] * N
    mon = Monitors(N, vmin_zero=int(aux.get("valley_zero", 0)) if aux else 0)   # zero-crossing TDC and valley tracking
    #   (shared with KernelPlant2's C loop); A101 option: the high side's minimum stops at its first V_DS <= 0
    use_c = hasattr(plant, "attach_monitors")
    if use_c:
        plant.attach_monitors(mon)
    t_en = aux.get("t_en_us", 0.0) * 1e-6 if aux else 0.0             # A102: branches disarmed until t_en
    en = {"t": None if t_en > 0 else 0.0}
    if t_en > 0:
        plant.aux_armed = [False] * na; plant.aux_cmd = [False] * na; plant.aux_on = [False] * na
    pend = []                                   # heap of (t_apply, seq, j, level, meta)
    seq = [0]
    meas_m = {}; meas_r = {}                    # phase -> measurement to deliver
    adc = []                                     # pending ADC sample of Vo (taken at phase 1's turn-on)
    st = {"mode_p": 0, "ton": 0, "t_mode_p": None}
    lat = {"armed": False, "fired": False, "dt0": 0, "report": None, "fires": 0}   # A81 front end of phase 1
    sections, turnons, lowoffs = [], [], []
    highoffs = []                                                # A101: phase (and branch) currents at high-side turn-offs
    im = [plant.sim.idx[f"m{k}"] for k in p.aux_phases]
    drv = cfg.get("driver")                                      # A91: driver timing model
    rng = np.random.default_rng(int(drv.get("seed", 1))) if drv else None
    ovl = {"count": 0, "first": None, "stop": False}

    def t_apply(t_cmd, j):
        """A91: the time the plant sees an edge commanded at t_cmd on switch j."""
        if not drv:
            return t_cmd + t_drv
        d = t_drv + (drv.get("m_ns", 0.0) * 1e-9 if j >= N else 0.0)
        edges = drv.get("jitter_edges", "all")                   # A98: "high" or "low" restricts the jitter
        if drv.get("sigma_ps", 0.0) > 0.0 and (edges == "all" or (edges == "high") == (j < N)):
            d += rng.normal(0.0, drv["sigma_ps"] * 1e-12)
        return t_cmd + d
    meas_l = {}; lowons = []
    trim_now = list(trim_init)
    t_end = float(os.environ.get("COSIM_T_END_US", cfg["t_end_us"])) * 1e-6
    t0w = time.time()

    def latch_fire():                                            # A81 latch fires
        lat["fired"] = True; lat["fires"] += 1
        t_cmd = plant.t + t_async
        heapq.heappush(pend, (t_apply(t_cmd, N + 0), seq[0], N + 0, 0, {"how": None, "bind": True})); seq[0] += 1
        heapq.heappush(pend, (t_apply(t_cmd + lat["dt0"] * lsb, 0), seq[0], 0, 1, {"how": 0, "bind": False})); seq[0] += 1
        lat["report"] = int(round(t_cmd / lsb))

    mlo = {"armed": False, "t": None, "report": None, "t_timed": None}   # A99: crossing measurement of phase 1
    lo_reports = []

    def mlo_fire():                                              # A99: phase 1's current reaches the target
        mlo["t"] = plant.t

    def on_step():
        if lat["armed"] and not lat["fired"] and plant.y[nv] <= i_tgt + trim_now[0] * lsb_a:
            latch_fire()
        if mlo["armed"] and mlo["t"] is None and plant.y[nv] <= i_tgt:
            mlo_fire()
        mon.py_step(plant)                                       # A89 zero-crossing TDC, valley tracking

    trace = {"path": os.environ.get("COSIM_TRACE"), "h": None, "digests": []}
    if trace["path"]:                                  # optional process trace: a running hash of the plant state
        import hashlib
        trace["h"] = hashlib.blake2b(digest_size=16)

    def integrate_to(t_target):
        if use_c:
            if not (lat["armed"] and not lat["fired"]) and mlo["armed"] and mlo["t"] is None:
                latch = (True, i_tgt, mlo_fire)                    # A99: measurement only
            else:
                latch = (lat["armed"] and not lat["fired"], i_tgt + trim_now[0] * lsb_a, latch_fire)
            plant.integrate_to(t_target, None, monitors=mon, latch=latch)
        else:
            plant.integrate_to(t_target, on_step)
        if trace["h"] is not None:                    # checkpoint: t, y, diode flags, Euler counter
            trace["h"].update(np.float64(plant.t).tobytes() + np.asarray(plant.y, dtype=np.float64).tobytes()
                              + bytes(int(bool(x)) for x in plant.diode) + int(plant.euler_left).to_bytes(4, "little"))
            trace["digests"].append(trace["h"].hexdigest())

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
            if (meta["how"] == 0 or (meta["how"] == 3 and cfg.get("learn_at_restart", 0))) and mon.vmin_set[k]:
                # early: the minimum was lowered by the step that landed on this edge (node still falling),
                # the same test as A75's "Vds at the edge below the minimum of the previous steps"
                tv, vm = float(mon.t_vmin[k]), float(mon.vmin[k])
                early = abs(tv - plant.t) < 1e-15 and tv > t_lo_act[k]
                dip = vm < v_lo[k] - v_hys and tv > t_lo_act[k]
                err = 0 if early else max(0, to_lsb(plant.t - tv))      # A92: edge - valley
                meas_m[k] = (early, not early and not dip, max(0, to_lsb(tv - t_lo_act[k])), err)
                rec["early"] = bool(early); rec["err_s"] = None if early else plant.t - tv
            mon.vmin_set[k] = 0
            if k == 0:
                vo, vin = float(plant.y[io]), p.vin_at(plant.t)
                ia = [plant.sim.idx[f"a{q}"] for q in range(1, N)]; ix = [plant.sim.idx[f"x{q}"] for q in range(1, N)]
                sections.append({"t_s": plant.t, "v": plant.y[:nv].tolist(), "i": plant.y[nv:].tolist(),
                                 "vo": vo, "vin_v": vin, "mode_p": st["mode_p"], "ton_lsb": st["ton"],
                                 "vcs_v": [float(plant.y[a] - plant.y[x]) for a, x in zip(ia, ix)],
                                 "rev_energy_j": list(plant.rev_e), "rev_time_s": list(plant.rev_t)})   # A89
                plant.rev_e = [0.0] * (2 * N); plant.rev_t = [0.0] * (2 * N)
                if na:                                          # A101: Cm voltages, branch int i^2 dt and extremes
                    sections[-1].update(vm_v=[float(plant.y[x]) for x in im], aux_i2s=[float(x) for x in plant.aux_e2],
                                        aux_imax_a=[float(x) for x in plant.aux_imax],
                                        aux_imin_a=[float(x) for x in plant.aux_imin])
                    plant.aux_e2 = [0.0] * na; plant.aux_imax = [0.0] * na; plant.aux_imin = [0.0] * na
                adc.append(min(max(int(round(vo / adc_lsb)), 0), adc_max))
        if j < N and not level:                 # A89: high-side turn-off edge starts the zero-crossing TDC
            mon.hoff_set[k] = 1; mon.t_hoff[k] = plant.t; mon.cross_set[k] = 0; mon.vprev_valid[k] = 0
            ib = [plant.y[c] for a, c in enumerate(plant.aux_col) if plant.aux_k[a] == k]   # A101: and its branch
            highoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": float(plant.y[nv + k]),
                             "i_aux_a": float(ib[0]) if ib else 0.0})
        if j >= N and level and mon.hoff_set[k]:    # A89: low-side turn-on edge
            crossed = bool(mon.cross_set[k])
            th, tc = float(mon.t_hoff[k]), float(mon.t_cross[k])
            rel = (tc - th) if crossed else None
            lowons.append({"t_s": plant.t, "phase": k + 1, "vds_v": float(plant.vds(N + k)), "mode_p": st["mode_p"],
                           "crossed": crossed, "t_cross_rel_s": rel, "t_since_off_s": plant.t - th})
            if cfg.get("low_pred", 0) and st["mode_p"]:
                meas_l[k] = (not crossed, 0 if not crossed else max(0, to_lsb(rel)),
                             0 if not crossed else max(0, to_lsb(plant.t - tc)))      # A92: edge - crossing
            mon.hoff_set[k] = 0; mon.cross_set[k] = 0
        if j == N and level and st.get("lo_timed"):  # A99: phase 1's low side on: measure its crossing
            mlo["armed"] = True; mlo["t"] = None
        if j == N and not level and mlo["armed"]:     # A99: its timed turn-off: report turn-off - crossing
            early = mlo["t"] is None
            mlo["report"] = (early, 0 if early else max(0, to_lsb(plant.t - mlo["t"])))
            lo_reports.append({"t_s": plant.t, "early": early, "err_s": None if early else plant.t - mlo["t"],
                               "i_a": float(plant.y[nv])})
            mlo["armed"] = False
        if j >= N and not level:                # low-side turn-off edge
            i_e = float(plant.y[nv + k])
            lowoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": i_e, "bind_cur": meta["bind"]})
            if meta["bind"]:
                meas_r[k] = i_e < i_tgt
            v_lo[k] = plant.vds(k); t_lo_act[k] = plant.t
            mon.vmin_set[k] = 1; mon.vmin[k] = v_lo[k]; mon.t_vmin[k] = t_lo_act[k]
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
        if cfg.get("lo_pred", 0):                                # A99
            st["lo_timed"] = int(dut.lo_timed1.value)
            if st["lo_timed"] and mlo["t_timed"] is None:
                mlo["t_timed"] = w * lsb
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
        if cfg.get("lo_pred", 0):                                # A99: one-cycle crossing report
            rep = mlo["report"]; mlo["report"] = None
            dut.mlo_valid.value = int(rep is not None)
            dut.mlo_early.value = int(rep[0]) if rep else 0
            dut.mlo_err.value = rep[1] if rep else 0
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
        if en["t"] is None and plant.t >= t_en:                  # A102: arm the branches (each starts at its
            plant.aux_armed = [True] * na; en["t"] = plant.t     # next low-side turn-off)
        # plant through window [w, w + 2^fb) LSB
        t_win_end = (w + (1 << fb)) * lsb
        while pend and pend[0][0] < t_win_end:
            ta, _, j, lvl, meta = heapq.heappop(pend)
            integrate_to(ta)
            apply(j, lvl, meta)
            if ovl["stop"]:                                     # A91: no integration through a shoot-through
                break
        if ovl["stop"]:
            break
        integrate_to(t_win_end)
        # comparators sampled at the window end
        ci = czl = czh = cva = 0
        for k in range(N):
            ci |= int(plant.y[nv + k] <= i_tgt + trim_now[k] * lsb_a) << k
            czl |= int(plant.vds(N + k) <= 0.0) << k
            czh |= int(plant.vds(k) <= 0.0) << k
            if mon.vmin_set[k]:
                cva |= int(plant.vds(k) >= float(mon.vmin[k]) + v_hys) << k
        dut.cmp_i.value = ci; dut.cmp_zl.value = czl; dut.cmp_zh.value = czh; dut.cmp_valley.value = cva

    await RisingEdge(dut.clk)
    await ReadOnly()
    keep_n = int(cfg.get("records_last", 1000))                      # A100: longer records on request
    out = {"cfg": cfg, "t_end_s": plant.t, "steps": plant.steps, "wall_s": time.time() - t0w,
           "late_fires": [field(dut.late_fires.value, k, 16) for k in range(N)],
           "trim_final": [signed(field(dut.trim.value, k, CW), CW) for k in range(N)],
           "dt_pred_final_ns": [field(dut.dt_pred.value, k, TW) * lsb * 1e9 for k in range(N)],
           "t_mode_p_s": st["t_mode_p"], "ton_final_lsb": int(dut.ton_now.value), "lsb_s": lsb,
           "vds_max_v": plant.vds_max, "ipk_a": plant.ipk, "async_fires": lat["fires"],
           "sections": sections, "turnons_last": turnons[-keep_n:], "lowoffs_last": lowoffs[-keep_n:],
           "dtl_final_ns": [field(dut.dtl.value, k, TW) * lsb * 1e9 for k in range(N)],     # A89
           "edges_log": edges_log, "driver": drv, "overlaps": ovl["count"], "first_overlap": ovl["first"],
           "status": "OVERLAP_STOP" if ovl["stop"] else "COMPLETED", "lowons_last": lowons[-keep_n:], "plant_flags": {"nonlinear_coss": p.nonlinear_coss, "rev_drop": p.rev_drop,
                                                            "rev_vf": p.rev_vf, "rev_r": p.rev_r}}
    if cfg.get("lo_pred", 0):                                    # A99
        out.update(t_lo_timed_s=mlo["t_timed"], dlo1_final_lsb=int(dut.dlo1.value), lo_reports_last=lo_reports[-keep_n:])
    out["highoffs_last"] = highoffs[-keep_n:]                    # A101
    if na:
        out["aux_params"] = {"phases": list(p.aux_phases), "l_h": p.aux_l, "r_ohm": p.aux_r, "c_f": p.aux_c,
                             "vm0_v": vm0, "valley_zero": int(mon.vmin_zero), "t_en_us": t_en * 1e6,
                             "t_armed_s": en["t"]}
    out["provenance"] = dict(json.loads(os.environ.get("COSIM_PROVENANCE", "{}")),
                             plant_impl=cfg.get("plant_impl", "kernel2"), t_end_us_override=os.environ.get("COSIM_T_END_US"))
    if prof is not None:
        prof.disable(); prof.dump_stats(os.environ["COSIM_PROFILE"])
    if trace["h"] is not None:
        Path(trace["path"]).write_text(json.dumps({"checkpoints": len(trace["digests"]), "digests": trace["digests"]}))
    dest = Path(os.environ.get("COSIM_OUT") or (cfg_path.parent / cfg["out"]))
    text = json.dumps(out)
    if dest.suffix == ".gz":
        with gzip.open(dest, "wt") as fh:
            fh.write(text)
    else:
        dest.write_text(text)
    dut._log.info(f"co-sim done: t {plant.t * 1e6:.2f} us, {len(sections)} sections, wall {out['wall_s']:.0f} s")
