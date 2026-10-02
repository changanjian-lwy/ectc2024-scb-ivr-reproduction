"""Co-simulation bridge: the Verilog controller (rtl/, run by Icarus Verilog through cocotb) closes the loop around
the P24 plant (plant.py, selected by cfg "plant_impl": "kernel2" (default, C step loop), "kernel", "fast" or
"reference"; all bit-identical).
Run through run.py. Configuration: the JSON file named by COSIM_CFG; optional overrides from run.py: COSIM_OUT
(output path), COSIM_T_END_US (stop time), COSIM_PROVENANCE (JSON added to the output). An output path ending in
".gz" is written gzip-compressed. Derived from A94's bridge (see CHANGELOG.md); since C1 one module's
state and window steps are a ModuleSim and the controller's signals go through Ctl.

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
Line step (cfg "line_step" {"t_us", "dv", "slew_us" 0}, A106): the input changes by dv from t_us, linearly over slew_us.
Circuit values (cfg "circuit" {name: value in SI units}, A107): any of CIRCUIT_KEYS (vin, L, R, c_high, c_low, cs, co,
r_load, i_load, g_on) replaces the init run's value; other names are refused.
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
CIRCUIT_KEYS = ("vin", "L", "R", "c_high", "c_low", "cs", "co", "r_load", "i_load", "g_on")   # A107: cfg "circuit"
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


class Ctl:
    """The controller's signals for one module (C1): get(name) reads a signal as an int, set(name, value) writes it,
    sig(name) is the signal handle. With one module this is the DUT itself."""

    def __init__(self, dut):
        self.dut = dut

    def sig(self, name):
        return getattr(self.dut, name)

    def get(self, name):
        return int(getattr(self.dut, name).value)

    def set(self, name, value):
        getattr(self.dut, name).value = value


class MultiCtl:
    """Module m's slice of the M-module wrapper's signals (scb_multi, C3). clk and rst are shared. Writes go through a
    cache of the packed values shared by the M modules, so that their writes in one phase combine."""
    SHARED = ("clk", "rst")

    def __init__(self, dut, m, n_mod, cache):
        self.dut, self.m, self.n_mod, self.cache = dut, m, n_mod, cache

    def sig(self, name):
        return getattr(self.dut, name)

    def _w(self, name):
        key = ("w", name)
        if key not in self.cache:
            self.cache[key] = len(getattr(self.dut, name)) // self.n_mod
        return self.cache[key]

    def get(self, name):
        if name in self.SHARED:
            return int(getattr(self.dut, name).value)
        return field(int(getattr(self.dut, name).value), self.m, self._w(name))

    def set(self, name, value):
        if name in self.SHARED:
            getattr(self.dut, name).value = value
            return
        w = self._w(name)
        mask = ((1 << w) - 1) << (self.m * w)
        new = (self.cache.get(name, 0) & ~mask) | ((int(value) & ((1 << w) - 1)) << (self.m * w))
        self.cache[name] = new
        getattr(self.dut, name).value = new


def load_cfg():
    cfg_path = Path(os.environ["COSIM_CFG"])
    cfg = json.loads(cfg_path.read_text())
    init = (cfg_path.parent / cfg["init_run"]).resolve()
    if not init.exists():                                              # presets name it relative to the project
        init = (PROJECT / cfg["init_run"]).resolve()
    return cfg_path, cfg, json.loads(init.read_text())


def make_params(cfg, ref):
    """The plant's parameters: the reference (Python) run's P24 circuit and sequence, with cfg's options."""
    pr = ref["params"]
    keep = ("n", "vin", "L", "R", "c_high", "c_low", "cs", "co", "load_kind", "r_load", "i_load", "g_on", "h",
            "t_ramp", "t_load", "t_hand")
    extra = {}
    circuit = cfg.get("circuit") or {}                                # A107: circuit values as scenario inputs (SI units)
    unknown = set(circuit) - set(CIRCUIT_KEYS)
    if unknown:
        raise ValueError(f"cfg 'circuit': not a circuit value: {sorted(unknown)}")
    extra.update({k: float(v) for k, v in circuit.items()})
    if cfg.get("nonlinear_coss", 0):                                  # A89: device realism of A86-A88
        extra["nonlinear_coss"] = True
    if cfg.get("rev_drop", 0):
        vf, rr, _ = fit_fig8(10.0, 100.0)
        extra.update(rev_drop=True, rev_vf=vf, rev_r=rr)
    for key, name in (("t_load_us", "t_load"), ("t_hand_us", "t_hand")):  # A103: start-up sequence timing
        if key in cfg:
            extra[name] = float(cfg[key]) * 1e-6
    if cfg.get("line_step"):                                          # A106: an input step
        ls = cfg["line_step"]
        extra.update(vin_step=float(ls["dv"]), t_vstep=float(ls["t_us"]) * 1e-6, t_vslew=float(ls.get("slew_us", 0.0)) * 1e-6)
    if cfg.get("load_step"):                                          # A100: a load current step
        extra.update(i_step=float(cfg["load_step"]["i_a"]), t_step=float(cfg["load_step"]["t_us"]) * 1e-6)
    aux = cfg.get("aux")                                              # A101: auxiliary commutation branches
    if aux:
        r_bds = 2 * aux.get("rds_on_mohm", 1.3) * 1e-3 / aux["alpha"]
        extra.update(aux_phases=tuple(aux.get("phases", range(1, N + 1))), aux_l=aux["lr_nh"] * 1e-9,
                     aux_r=r_bds + aux.get("r_lr_mohm", 0.2) * 1e-3, aux_c=aux.get("cm_uf", 1.0) * 1e-6,
                     aux_vm0=tuple(aux["vm0_v"]) if isinstance(aux.get("vm0_v"), list) else aux.get("vm0_v", 0.0))
    return Params(**{k: pr[k] for k in keep if k not in extra}, diode_check=True, **extra)


class ModuleSim:
    """One module (C1): its plant (from the all-zero state with phase 1 HIGH and phases 2..N LOW, A73's initial state,
    which the controller's reset assumes), the controller-side analog functions and measurements, and its records.
    Per 4 ns window: read_rising (the controller's edge requests), write_falling (measurement pulses, ADC, handover,
    load), run_window (the plant through the window, edges at their times), sample (the comparators)."""

    def __init__(self, cfg, p, ctl, first_high=True):
        self.cfg, self.p, self.ctl = cfg, p, ctl
        t_clk = cfg["t_clk_ns"] * 1e-9
        self.fb = int(cfg["fb"])
        self.lsb = t_clk / (1 << self.fb)
        self.t_drv = cfg["t_drv_ns"] * 1e-9
        self.i_tgt, self.lsb_a, self.v_hys = cfg["i_target"], cfg["trim_lsb_a"], cfg["v_hys"]
        self.na = na = len(p.aux_phases)
        self.vm0 = list(p.aux_vm0) if isinstance(p.aux_vm0, (list, tuple)) else [p.aux_vm0] * na   # A102: per branch
        y0 = [0.0] * (2 * N) + self.vm0 + [0.0] * N + [0.0] * na   # 2N node voltages (+ Cm nodes), N currents (+ branches)
        g1 = bool(first_high)                                          # C3: a slave resets with phase 1 LOW
        self.plant = PLANTS[cfg.get("plant_impl", "kernel2")](p, y0, gh=[g1] + [False] * (N - 1), gl=[not g1] + [True] * (N - 1))
        self.nv = self.plant.nv
        self.i_out = self.plant.sim.idx["out"]
        self.adc_lsb, self.adc_max = cfg["adc_lsb_v"], (1 << 12) - 1
        # Controller initial registers: the predictive delay starts at half the node resonance period, as in
        # the Python rule; the trim codes start at 0 (threshold = target).
        self.dt_init = [self.to_lsb(cfg["dt_init_ns"] * 1e-9)] * N
        self.trim_init = [0] * N
        self.t_async = cfg.get("t_async_ns", 1.0) * 1e-9

    def to_lsb(self, s):
        return int(round(s / self.lsb))

    def configure(self):
        cfg, c, to_lsb = self.cfg, self.ctl, self.to_lsb
        c.set("rst", 1)
        c.set("cfg_ton", to_lsb(cfg["ton_ns"] * 1e-9))
        c.set("cfg_rs_high", to_lsb(cfg["rs_high_ns"] * 1e-9))
        c.set("cfg_rs_low", to_lsb(cfg["rs_low_ns"] * 1e-9))
        c.set("cfg_dt_step", max(1, to_lsb(cfg["dt_step_ns"] * 1e-9)))
        c.set("cfg_dt_max", to_lsb(cfg["dt_max_ns"] * 1e-9))
        c.set("cfg_slot", pack([to_lsb(k * cfg["t0_ns"] * 1e-9 / N) for k in range(1, N)], TW))
        c.set("cfg_pred", 1)
        c.set("cfg_zvs_react", 0)
        c.set("cfg_trim", int(cfg["trim"]))
        c.set("cfg_fine", int(cfg["fine"]))
        c.set("dt_init", pack(self.dt_init, TW))
        c.set("trim_init", pack(self.trim_init, CW))
        for s in ("cmp_i", "cmp_zl", "cmp_zh", "cmp_valley", "m_valid", "m_early", "m_flat", "r_valid", "r_below"):
            c.set(s, 0)
        c.set("m_tv", 0)
        c.set("cfg_start_s", 1)
        c.set("hand_req", 0)
        c.set("cfg_t0", to_lsb(cfg["t0_ns"] * 1e-9))
        c.set("cfg_tdead", to_lsb(cfg["tdead_ns"] * 1e-9))
        c.set("cfg_ton_min", to_lsb(0.5 * cfg["ton_ns"] * 1e-9))
        c.set("cfg_ton_max", to_lsb(2.0 * cfg["ton_ns"] * 1e-9))
        c.set("cfg_vloop", int(cfg["vloop"]))
        c.set("cfg_vref_code", int(round(cfg["vref_v"] / self.adc_lsb)))
        # ki in ns of Ton per V -> Ton LSB per ADC LSB, 16 fractional bits
        c.set("cfg_ki", int(round(cfg["ki_ns_per_v"] * self.adc_lsb / (self.lsb * 1e9) * 65536)))
        c.set("cfg_kp", int(round(cfg.get("kp_ns_per_v", 0.0) * self.adc_lsb / (self.lsb * 1e9) * 65536)))   # A104
        c.set("cfg_ext_ton", 0); c.set("ext_ton", 0); c.set("ext_slot", 0); c.set("ext_ref", 0)   # C2: set per module
        c.set("adc_valid", 0)
        c.set("adc_code", 0)
        c.set("cfg_low_pred", int(cfg.get("low_pred", 0)))            # A89
        c.set("dtl_init", pack([to_lsb(cfg.get("dtl_init_ns", 2.15) * 1e-9)] * N, TW))
        c.set("cfg_dtl_step", max(1, to_lsb(cfg.get("dtl_step_ns", 0.05) * 1e-9)))
        c.set("cfg_dtl_max", to_lsb(cfg.get("dtl_max_ns", 10.0) * 1e-9))
        c.set("ml_valid", 0); c.set("ml_early", 0); c.set("ml_tv", 0)
        c.set("cfg_err_low", int(cfg.get("err_low", 0)))               # A92
        c.set("cfg_err_high", int(cfg.get("err_high", 0)))
        c.set("cfg_el_tgt", to_lsb(cfg.get("el_tgt_ps", 0.0) * 1e-12))
        c.set("cfg_eh_tgt", to_lsb(cfg.get("eh_tgt_ps", 0.0) * 1e-12))
        c.set("cfg_err_shift", int(cfg.get("err_shift", 0)))
        c.set("ml_err", 0); c.set("m_err", 0)
        c.set("cfg_slot_follow", int(cfg.get("slot_follow", 0)))        # A93
        c.set("cfg_slot_guard", int(cfg.get("slot_guard", 0)))
        c.set("cfg_slot_avg", int(cfg.get("slot_avg", 0)))              # A97
        c.set("cfg_lo_pred", int(cfg.get("lo_pred", 0)))                # A99: timed phase-1 turn-off
        c.set("cfg_lo_learn", int(cfg.get("lo_learn", 0)))
        c.set("cfg_lo_tgt", to_lsb(cfg.get("lo_tgt_ps", 0.0) * 1e-12))
        c.set("mlo_valid", 0); c.set("mlo_early", 0); c.set("mlo_err", 0)
        c.set("cfg_lo_adm", int(cfg.get("lo_adm", 0)))                  # A100: adaptive dlo step
        c.set("cfg_lo_smax", int(cfg.get("lo_smax", 0)))
        c.set("cfg_lo_ff", int(cfg.get("lo_ff", 0)))                    # A100: Ton feedforward to dlo
        c.set("cfg_lo_kff", int(cfg.get("lo_kff", 0)))
        c.set("cfg_blank", to_lsb(cfg.get("blank_ns", 0.0) * 1e-9))     # A89 amendment: comparator blanking
        c.set("cfg_async", int(cfg.get("async", 0)))
        c.set("a_valid", 0)
        c.set("a_tlo", 0)

    def start(self):
        """After the reset: the plant-side bookkeeping for the comparators and the measurements."""
        cfg, p, plant, na = self.cfg, self.p, self.plant, self.na
        self.v_lo = [None] * N; self.t_lo_act = [None] * N
        aux = cfg.get("aux")
        self.mon = Monitors(N, vmin_zero=int(aux.get("valley_zero", 0)) if aux else 0)   # zero-crossing TDC and valley tracking
        #   (shared with KernelPlant2's C loop); A101 option: the high side's minimum stops at its first V_DS <= 0
        self.use_c = hasattr(plant, "attach_monitors")
        if self.use_c:
            plant.attach_monitors(self.mon)
        self.t_en = aux.get("t_en_us", 0.0) * 1e-6 if aux else 0.0     # A102: branches disarmed until t_en
        self.en = {"t": None if self.t_en > 0 else 0.0}
        if self.t_en > 0:
            plant.aux_armed = [False] * na; plant.aux_cmd = [False] * na; plant.aux_on = [False] * na
        self.pend = []                              # heap of (t_apply, seq, j, level, meta)
        self.seq = [0]
        self.meas_m = {}; self.meas_r = {}          # phase -> measurement to deliver
        self.adc = []                               # pending ADC sample of Vo (taken at phase 1's turn-on)
        self.st = {"mode_p": 0, "ton": 0, "t_mode_p": None}
        self.lat = {"armed": False, "fired": False, "dt0": 0, "report": None, "fires": 0}   # A81 front end of phase 1
        self.sections, self.turnons, self.lowoffs = [], [], []
        self.highoffs = []                                       # A101: phase (and branch) currents at high-side turn-offs
        self.im = [plant.sim.idx[f"m{k}"] for k in p.aux_phases]
        self.drv = cfg.get("driver")                             # A91: driver timing model
        self.rng = np.random.default_rng(int(self.drv.get("seed", 1))) if self.drv else None
        self.ovl = {"count": 0, "first": None, "stop": False}
        self.meas_l = {}; self.lowons = []
        self.trim_now = list(self.trim_init)
        self.mlo = {"armed": False, "t": None, "report": None, "t_timed": None}   # A99: crossing measurement of phase 1
        self.lo_reports = []
        self.trace = {"path": os.environ.get("COSIM_TRACE"), "h": None, "digests": []}
        if self.trace["path"]:                         # optional process trace: a running hash of the plant state
            import hashlib
            self.trace["h"] = hashlib.blake2b(digest_size=16)
        self.dbg = cfg.get("debug_edges_us")                    # A89 diagnostics only: log every applied edge
        self.edges_log = []

    def t_apply(self, t_cmd, j):
        """A91: the time the plant sees an edge commanded at t_cmd on switch j."""
        drv = self.drv
        if not drv:
            return t_cmd + self.t_drv
        d = self.t_drv + (drv.get("m_ns", 0.0) * 1e-9 if j >= N else 0.0)
        edges = drv.get("jitter_edges", "all")                   # A98: "high" or "low" restricts the jitter
        if drv.get("sigma_ps", 0.0) > 0.0 and (edges == "all" or (edges == "high") == (j < N)):
            d += self.rng.normal(0.0, drv["sigma_ps"] * 1e-12)
        return t_cmd + d

    def latch_fire(self):                                        # A81 latch fires
        lat, lsb = self.lat, self.lsb
        lat["fired"] = True; lat["fires"] += 1
        t_cmd = self.plant.t + self.t_async
        heapq.heappush(self.pend, (self.t_apply(t_cmd, N + 0), self.seq[0], N + 0, 0, {"how": None, "bind": True})); self.seq[0] += 1
        heapq.heappush(self.pend, (self.t_apply(t_cmd + lat["dt0"] * lsb, 0), self.seq[0], 0, 1, {"how": 0, "bind": False})); self.seq[0] += 1
        lat["report"] = int(round(t_cmd / lsb))

    def mlo_fire(self):                                          # A99: phase 1's current reaches the target
        self.mlo["t"] = self.plant.t

    def on_step(self):
        lat, mlo, plant, nv = self.lat, self.mlo, self.plant, self.nv
        if lat["armed"] and not lat["fired"] and plant.y[nv] <= self.i_tgt + self.trim_now[0] * self.lsb_a:
            self.latch_fire()
        if mlo["armed"] and mlo["t"] is None and plant.y[nv] <= self.i_tgt:
            self.mlo_fire()
        self.mon.py_step(plant)                                  # A89 zero-crossing TDC, valley tracking

    def integrate_to(self, t_target):
        lat, mlo, plant = self.lat, self.mlo, self.plant
        if self.use_c:
            if not (lat["armed"] and not lat["fired"]) and mlo["armed"] and mlo["t"] is None:
                latch = (True, self.i_tgt, self.mlo_fire)              # A99: measurement only
            else:
                latch = (lat["armed"] and not lat["fired"], self.i_tgt + self.trim_now[0] * self.lsb_a, self.latch_fire)
            plant.integrate_to(t_target, None, monitors=self.mon, latch=latch)
        else:
            plant.integrate_to(t_target, self.on_step)
        trace = self.trace
        if trace["h"] is not None:                    # checkpoint: t, y, diode flags, Euler counter
            trace["h"].update(np.float64(plant.t).tobytes() + np.asarray(plant.y, dtype=np.float64).tobytes()
                              + bytes(int(bool(x)) for x in plant.diode) + int(plant.euler_left).to_bytes(4, "little"))
            trace["digests"].append(trace["h"].hexdigest())

    def apply(self, j, level, meta):
        cfg, p, plant, nv, mon, st, mlo, ovl = self.cfg, self.p, self.plant, self.nv, self.mon, self.st, self.mlo, self.ovl
        to_lsb, na = self.to_lsb, self.na
        k = j % N
        if level and (plant.gl[k] if j < N else plant.gh[k]):   # A91: turn-on against a conducting complement
            ovl["count"] += 1
            if ovl["first"] is None:
                ovl["first"] = {"t_s": plant.t, "phase": k + 1, "switch": "SH" if j < N else "SL", "mode_p": st["mode_p"]}
            if cfg.get("stop_on_overlap", 0):
                ovl["stop"] = True
        dbg = self.dbg
        if dbg and dbg[0] * 1e-6 <= plant.t <= dbg[1] * 1e-6:
            self.edges_log.append({"t_s": plant.t, "j": j, "level": int(level), "mode_p": st["mode_p"],
                                   "vds": [round(plant.vds(q), 3) for q in range(2 * N)],
                                   "i": [round(float(x), 2) for x in plant.y[nv:]], "gh": list(plant.gh), "gl": list(plant.gl)})
        if j < N and level:                     # high-side turn-on edge
            v = plant.vds(k)
            rec = {"t_s": plant.t, "phase": k + 1, "how": meta["how"], "vds_v": float(v),
                   "i_a": float(plant.y[nv + k])}
            self.turnons.append(rec)
            if (meta["how"] == 0 or (meta["how"] == 3 and cfg.get("learn_at_restart", 0))) and mon.vmin_set[k]:
                # early: the minimum was lowered by the step that landed on this edge (node still falling),
                # the same test as A75's "Vds at the edge below the minimum of the previous steps"
                tv, vm = float(mon.t_vmin[k]), float(mon.vmin[k])
                early = abs(tv - plant.t) < 1e-15 and tv > self.t_lo_act[k]
                dip = vm < self.v_lo[k] - self.v_hys and tv > self.t_lo_act[k]
                err = 0 if early else max(0, to_lsb(plant.t - tv))      # A92: edge - valley
                self.meas_m[k] = (early, not early and not dip, max(0, to_lsb(tv - self.t_lo_act[k])), err)
                rec["early"] = bool(early); rec["err_s"] = None if early else plant.t - tv
            mon.vmin_set[k] = 0
            if k == 0:
                vo, vin = float(plant.y[self.i_out]), p.vin_at(plant.t)
                ia = [plant.sim.idx[f"a{q}"] for q in range(1, N)]; ix = [plant.sim.idx[f"x{q}"] for q in range(1, N)]
                self.sections.append({"t_s": plant.t, "v": plant.y[:nv].tolist(), "i": plant.y[nv:].tolist(),
                                      "vo": vo, "vin_v": vin, "mode_p": st["mode_p"], "ton_lsb": st["ton"],
                                      "vcs_v": [float(plant.y[a] - plant.y[x]) for a, x in zip(ia, ix)],
                                      "rev_energy_j": list(plant.rev_e), "rev_time_s": list(plant.rev_t)})   # A89
                plant.rev_e = [0.0] * (2 * N); plant.rev_t = [0.0] * (2 * N)
                if na:                                          # A101: Cm voltages, branch int i^2 dt and extremes
                    self.sections[-1].update(vm_v=[float(plant.y[x]) for x in self.im], aux_i2s=[float(x) for x in plant.aux_e2],
                                             aux_imax_a=[float(x) for x in plant.aux_imax],
                                             aux_imin_a=[float(x) for x in plant.aux_imin])
                    plant.aux_e2 = [0.0] * na; plant.aux_imax = [0.0] * na; plant.aux_imin = [0.0] * na
                self.adc.append(min(max(int(round(vo / self.adc_lsb)), 0), self.adc_max))
        if j < N and not level:                 # A89: high-side turn-off edge starts the zero-crossing TDC
            mon.hoff_set[k] = 1; mon.t_hoff[k] = plant.t; mon.cross_set[k] = 0; mon.vprev_valid[k] = 0
            ib = [plant.y[c] for a, c in enumerate(plant.aux_col) if plant.aux_k[a] == k]   # A101: and its branch
            self.highoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": float(plant.y[nv + k]),
                                  "i_aux_a": float(ib[0]) if ib else 0.0})
        if j >= N and level and mon.hoff_set[k]:    # A89: low-side turn-on edge
            crossed = bool(mon.cross_set[k])
            th, tc = float(mon.t_hoff[k]), float(mon.t_cross[k])
            rel = (tc - th) if crossed else None
            self.lowons.append({"t_s": plant.t, "phase": k + 1, "vds_v": float(plant.vds(N + k)), "mode_p": st["mode_p"],
                                "crossed": crossed, "t_cross_rel_s": rel, "t_since_off_s": plant.t - th})
            if cfg.get("low_pred", 0) and st["mode_p"]:
                self.meas_l[k] = (not crossed, 0 if not crossed else max(0, to_lsb(rel)),
                                  0 if not crossed else max(0, to_lsb(plant.t - tc)))      # A92: edge - crossing
            mon.hoff_set[k] = 0; mon.cross_set[k] = 0
        if j == N and level and st.get("lo_timed"):  # A99: phase 1's low side on: measure its crossing
            mlo["armed"] = True; mlo["t"] = None
        if j == N and not level and mlo["armed"]:     # A99: its timed turn-off: report turn-off - crossing
            early = mlo["t"] is None
            mlo["report"] = (early, 0 if early else max(0, to_lsb(plant.t - mlo["t"])))
            self.lo_reports.append({"t_s": plant.t, "early": early, "err_s": None if early else plant.t - mlo["t"],
                                    "i_a": float(plant.y[nv])})
            mlo["armed"] = False
        if j >= N and not level:                # low-side turn-off edge
            i_e = float(plant.y[nv + k])
            self.lowoffs.append({"t_s": plant.t, "phase": k + 1, "i_a": i_e, "bind_cur": meta["bind"]})
            if meta["bind"]:
                self.meas_r[k] = i_e < self.i_tgt
            self.v_lo[k] = plant.vds(k); self.t_lo_act[k] = plant.t
            mon.vmin_set[k] = 1; mon.vmin[k] = self.v_lo[k]; mon.t_vmin[k] = self.t_lo_act[k]
        plant.set_gate(j, level)

    def read_rising(self):
        """After the rising edge (read-only phase): the controller's state and the edge requests of window w."""
        c, st, lat, mlo, cfg, fb, lsb = self.ctl, self.st, self.lat, self.mlo, self.cfg, self.fb, self.lsb
        w = c.get("win_q")
        how = c.get("on_how"); bind = c.get("lo_bind_cur")
        self.trim_now = [signed(field(c.get("trim"), k, CW), CW) for k in range(N)]
        st["ton"] = c.get("ton_now")
        if c.get("mode_p") and not st["mode_p"]:
            st["t_mode_p"] = w * lsb
        st["mode_p"] = c.get("mode_p")
        if cfg.get("lo_pred", 0):                                # A99
            st["lo_timed"] = c.get("lo_timed1")
            if st["lo_timed"] and mlo["t_timed"] is None:
                mlo["t_timed"] = w * lsb
        if c.get("arm1"):
            lat["armed"] = True
        else:
            lat["armed"] = False; lat["fired"] = False
        lat["dt0"] = field(c.get("dt_pred"), 0, TW)
        gh_ev, gh_lvl, gh_fine = c.get("gh_ev"), c.get("gh_lvl"), c.get("gh_fine")
        gl_ev, gl_lvl, gl_fine = c.get("gl_ev"), c.get("gl_lvl"), c.get("gl_fine")
        for k in range(N):
            for gate, ev, lvl, fine in (("H", gh_ev, gh_lvl, gh_fine), ("L", gl_ev, gl_lvl, gl_fine)):
                if field(ev, k, 1):
                    t_cmd = (w + field(fine, k, fb)) * lsb
                    j = k if gate == "H" else N + k
                    meta = {"how": field(how, k, 3), "bind": bool(field(bind, k, 1))}
                    heapq.heappush(self.pend, (self.t_apply(t_cmd, j), self.seq[0], j, field(lvl, k, 1), meta))
                    self.seq[0] += 1
        return w

    def write_falling(self):
        """After the falling edge: one-cycle measurement pulses from the previous window, the ADC sample, the handover
        request, the load and the branch arming."""
        c, cfg, lat, mlo, p, plant = self.ctl, self.cfg, self.lat, self.mlo, self.p, self.plant
        mv = me = mf = rv = rb = 0; mtv = [0] * N; merr = [0] * N
        for k, (early, flat, tv, err) in self.meas_m.items():
            mv |= 1 << k; me |= int(early) << k; mf |= int(flat) << k; mtv[k] = tv; merr[k] = err
        for k, below in self.meas_r.items():
            rv |= 1 << k; rb |= int(below) << k
        ml_v = ml_e = 0; ml_t = [0] * N; ml_r = [0] * N             # A89: zero-crossing reports (A92: + error)
        for k, (early, tv, err) in self.meas_l.items():
            ml_v |= 1 << k; ml_e |= int(early) << k; ml_t[k] = tv; ml_r[k] = err
        self.meas_l.clear()
        c.set("ml_valid", ml_v); c.set("ml_early", ml_e); c.set("ml_tv", pack(ml_t, TW))
        c.set("ml_err", pack(ml_r, TW)); c.set("m_err", pack(merr, TW))
        if cfg.get("lo_pred", 0):                                # A99: one-cycle crossing report
            rep = mlo["report"]; mlo["report"] = None
            c.set("mlo_valid", int(rep is not None))
            c.set("mlo_early", int(rep[0]) if rep else 0)
            c.set("mlo_err", rep[1] if rep else 0)
        self.meas_m.clear(); self.meas_r.clear()
        c.set("m_valid", mv); c.set("m_early", me); c.set("m_flat", mf); c.set("m_tv", pack(mtv, TW))
        c.set("r_valid", rv); c.set("r_below", rb)
        c.set("a_valid", int(lat["report"] is not None))
        c.set("a_tlo", lat["report"] or 0)
        lat["report"] = None
        c.set("adc_valid", int(bool(self.adc)))
        c.set("adc_code", self.adc[-1] if self.adc else 0)
        self.adc.clear()
        c.set("hand_req", int(plant.t >= p.t_hand))
        plant.load_on = plant.t >= p.t_load
        if self.en["t"] is None and plant.t >= self.t_en:        # A102: arm the branches (each starts at its
            plant.aux_armed = [True] * self.na; self.en["t"] = plant.t   # next low-side turn-off)

    def run_window(self, t_win_end):
        """The plant through the window, applying the pending edges at their times. False after a shoot-through stop."""
        pend = self.pend
        while pend and pend[0][0] < t_win_end:
            ta, _, j, lvl, meta = heapq.heappop(pend)
            self.integrate_to(ta)
            self.apply(j, lvl, meta)
            if self.ovl["stop"]:                                # A91: no integration through a shoot-through
                return False
        self.integrate_to(t_win_end)
        return True

    def sample(self):
        """The comparators at the window end."""
        plant, nv, mon, c = self.plant, self.nv, self.mon, self.ctl
        ci = czl = czh = cva = 0
        for k in range(N):
            ci |= int(plant.y[nv + k] <= self.i_tgt + self.trim_now[k] * self.lsb_a) << k
            czl |= int(plant.vds(N + k) <= 0.0) << k
            czh |= int(plant.vds(k) <= 0.0) << k
            if mon.vmin_set[k]:
                cva |= int(plant.vds(k) >= float(mon.vmin[k]) + self.v_hys) << k
        c.set("cmp_i", ci); c.set("cmp_zl", czl); c.set("cmp_zh", czh); c.set("cmp_valley", cva)

    def result(self, wall_s):
        """The run record."""
        c, cfg, plant, lsb, st, lat, mlo, ovl, p, na = self.ctl, self.cfg, self.plant, self.lsb, self.st, self.lat, self.mlo, self.ovl, self.p, self.na
        keep_n = int(cfg.get("records_last", 1000))                      # A100: longer records on request
        out = {"cfg": cfg, "t_end_s": plant.t, "steps": plant.steps, "wall_s": wall_s,
               "late_fires": [field(c.get("late_fires"), k, 16) for k in range(N)],
               "trim_final": [signed(field(c.get("trim"), k, CW), CW) for k in range(N)],
               "dt_pred_final_ns": [field(c.get("dt_pred"), k, TW) * lsb * 1e9 for k in range(N)],
               "t_mode_p_s": st["t_mode_p"], "ton_final_lsb": c.get("ton_now"), "lsb_s": lsb,
               "vds_max_v": plant.vds_max, "ipk_a": plant.ipk, "async_fires": lat["fires"],
               "sections": self.sections, "turnons_last": self.turnons[-keep_n:], "lowoffs_last": self.lowoffs[-keep_n:],
               "dtl_final_ns": [field(c.get("dtl"), k, TW) * lsb * 1e9 for k in range(N)],     # A89
               "edges_log": self.edges_log, "driver": self.drv, "overlaps": ovl["count"], "first_overlap": ovl["first"],
               "status": "OVERLAP_STOP" if ovl["stop"] else "COMPLETED", "lowons_last": self.lowons[-keep_n:],
               "plant_flags": {"nonlinear_coss": p.nonlinear_coss, "rev_drop": p.rev_drop, "rev_vf": p.rev_vf, "rev_r": p.rev_r}}
        if cfg.get("lo_pred", 0):                                    # A99
            out.update(t_lo_timed_s=mlo["t_timed"], dlo1_final_lsb=c.get("dlo1"), lo_reports_last=self.lo_reports[-keep_n:])
        out["highoffs_last"] = self.highoffs[-keep_n:]               # A101
        if na:
            out["aux_params"] = {"phases": list(p.aux_phases), "l_h": p.aux_l, "r_ohm": p.aux_r, "c_f": p.aux_c,
                                 "vm0_v": self.vm0, "valley_zero": int(self.mon.vmin_zero), "t_en_us": self.t_en * 1e6,
                                 "t_armed_s": self.en["t"]}
        return out


def write_out(cfg_path, cfg, out):
    dest = Path(os.environ.get("COSIM_OUT") or (cfg_path.parent / cfg["out"]))
    text = json.dumps(out)
    if dest.suffix == ".gz":
        with gzip.open(dest, "wt") as fh:
            fh.write(text)
    else:
        dest.write_text(text)


async def cosim_multi(dut, cfg_path, cfg, ref):
    """M modules (C3) on one output: each module is a ModuleSim with the single-module plant (its own Co and load);
    after every window the output nodes are joined by charge conservation (equal Co: their mean). The master
    (module 0) runs the voltage loop; the system broadcasts its Ton to the slaves (cfg_ext_ton) and gives slave m's
    phase 1 the slot t_ref + m T / (M N) after each master turn-on, T the master's last period (the mean of its last
    two once three turn-ons are seen; cfg t0 before), the reference id its t_ref. cfg "module_circuit" (list, one dict
    per module) adds per-module circuit values; a load step's i_a is the system's, shared equally."""
    n_mod = int(cfg["modules"])
    cache = {}
    mods = []
    for m in range(n_mod):
        cm = dict(cfg)
        circ = dict(cfg.get("circuit") or {})
        circ.update((cfg.get("module_circuit") or [{}] * n_mod)[m] or {})
        cm["circuit"] = circ
        if cfg.get("load_step"):
            cm["load_step"] = dict(cfg["load_step"], i_a=float(cfg["load_step"]["i_a"]) / n_mod)
        if m > 0:
            cm["vloop"] = 0
            if cm.get("driver"):                                  # each module its own jitter sequence
                cm["driver"] = dict(cm["driver"], seed=int(cm["driver"].get("seed", 1)) + 1000 * m)
        mods.append(ModuleSim(cm, make_params(cm, ref), MultiCtl(dut, m, n_mod, cache), first_high=(m == 0)))
    cocotb.start_soon(Clock(dut.clk, cfg["t_clk_ns"], unit="ns").start())
    for mod in mods:
        mod.configure()
    for mod in mods[1:]:
        mod.ctl.set("cfg_ext_ton", 1)
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    for mod in mods:
        mod.start()
    t_end = float(os.environ.get("COSIM_T_END_US", cfg["t_end_us"])) * 1e-6
    t0w = time.time()
    master = mods[0]
    nn = n_mod * N
    sync = {"t_ref": None, "hist": [], "period": master.to_lsb(cfg["t0_ns"] * 1e-9)}
    eq = {"max_v": 0.0, "sum_v": 0.0, "n": 0}
    while master.plant.t < t_end and not any(md.ovl["stop"] for md in mods):
        await RisingEdge(dut.clk)
        await ReadOnly()
        ws = [md.read_rising() for md in mods]
        w = ws[0]
        ton_m = master.st["ton"]
        t_ref = master.ctl.get("t_ref")
        if t_ref != sync["t_ref"]:                               # a master turn-on: the slaves' new slots
            if sync["t_ref"] is not None:
                sync["hist"].append((t_ref - sync["t_ref"]) % (1 << TW))
                h = sync["hist"]
                sync["period"] = h[-1] if len(h) < 2 else (h[-1] + h[-2]) // 2
            sync["t_ref"] = t_ref
        await FallingEdge(dut.clk)
        for md in mods:
            md.write_falling()
        for m, md in enumerate(mods[1:], start=1):
            md.ctl.set("ext_ton", ton_m)
            if sync["t_ref"] is not None:
                md.ctl.set("ext_ref", sync["t_ref"])
                md.ctl.set("ext_slot", (sync["t_ref"] + (m * sync["period"]) // nn) % (1 << TW))
        t_win_end = (w + (1 << master.fb)) * master.lsb
        stop = False
        for md in mods:
            if not md.run_window(t_win_end):
                stop = True
        if stop:
            break
        vs = [float(md.plant.y[md.i_out]) for md in mods]           # join the output nodes (equal Co)
        v_eq = sum(vs) / n_mod
        dev = max(abs(v - v_eq) for v in vs)
        eq["max_v"] = max(eq["max_v"], dev); eq["sum_v"] += dev; eq["n"] += 1
        for md in mods:
            md.plant.y[md.i_out] = v_eq
        for md in mods:
            md.sample()
    await RisingEdge(dut.clk)
    await ReadOnly()
    wall = time.time() - t0w
    out = master.result(wall)
    out["modules_rest"] = [md.result(wall) for md in mods[1:]]
    out["system"] = {"modules": n_mod, "equalisation_max_v": eq["max_v"], "equalisation_mean_v": eq["sum_v"] / max(eq["n"], 1),
                     "windows": eq["n"], "status": "OVERLAP_STOP" if any(md.ovl["stop"] for md in mods) else "COMPLETED",
                     "overlaps": [md.ovl["count"] for md in mods], "ipk_a": [md.plant.ipk for md in mods]}
    out["provenance"] = dict(json.loads(os.environ.get("COSIM_PROVENANCE", "{}")),
                             plant_impl=cfg.get("plant_impl", "kernel2"), t_end_us_override=os.environ.get("COSIM_T_END_US"))
    write_out(cfg_path, cfg, out)


@cocotb.test()
async def cosim(dut):
    prof = None
    if os.environ.get("COSIM_PROFILE"):                                 # optional: cProfile of the whole run
        import cProfile
        prof = cProfile.Profile(); prof.enable()
    cfg_path, cfg, ref = load_cfg()
    if int(cfg.get("modules", 1)) > 1:                                 # C3: the M-module system
        await cosim_multi(dut, cfg_path, cfg, ref)
        return
    p = make_params(cfg, ref)
    mod = ModuleSim(cfg, p, Ctl(dut))
    cocotb.start_soon(Clock(dut.clk, cfg["t_clk_ns"], unit="ns").start())
    mod.configure()
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    mod.start()
    t_end = float(os.environ.get("COSIM_T_END_US", cfg["t_end_us"])) * 1e-6
    t0w = time.time()
    plant = mod.plant
    while plant.t < t_end and not mod.ovl["stop"]:
        await RisingEdge(dut.clk)
        await ReadOnly()
        w = mod.read_rising()
        await FallingEdge(dut.clk)
        mod.write_falling()
        # plant through window [w, w + 2^fb) LSB
        if not mod.run_window((w + (1 << mod.fb)) * mod.lsb):
            break
        mod.sample()

    await RisingEdge(dut.clk)
    await ReadOnly()
    out = mod.result(time.time() - t0w)
    out["provenance"] = dict(json.loads(os.environ.get("COSIM_PROVENANCE", "{}")),
                             plant_impl=cfg.get("plant_impl", "kernel2"), t_end_us_override=os.environ.get("COSIM_T_END_US"))
    if prof is not None:
        prof.disable(); prof.dump_stats(os.environ["COSIM_PROFILE"])
    trace = mod.trace
    if trace["h"] is not None:
        Path(trace["path"]).write_text(json.dumps({"checkpoints": len(trace["digests"]), "digests": trace["digests"]}))
    write_out(cfg_path, cfg, out)
