"""cocotb unit tests of the controller RTL (../rtl/scb_ctrl.v), one design requirement per test.

Time is in LSB units: 1 LSB = T_clk / 32 = 125 ps at the 250 MHz base case (the tests use FB = 5). The fixture
drives every input; option bits default to 0. Groups: phase timing, comparators and slots; predictive correction
and trim; restarts; mode S, handover and voltage loop; the asynchronous phase-1 front end; the timed low side and
blanking; the error-based correctors; the period-following slots, their two-period average and the missed-slot
guard, their reference at phase 1's low-side turn-off (C02) and their valley trim (A109); the timed phase-1 turn-off and its adaptive
step and Ton feedforward. From A93's tests (history: ../CHANGELOG.md).
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

N, TW, FB, CW = 4, 32, 5, 8
WIN = 1 << FB
BASE = dict(ton=133, rs_high=160, rs_low=3200, dt_step=2, dt_max=278,
            slot=(400, 800, 1200), dt_init=(85, 80, 80, 93), trim_init=(0, 0, 0, 0),
            pred=1, zvs_react=0, trim=1, fine=1,
            start_s=0, t0=1600, tdead=17, ton_min=67, ton_max=266, vloop=0, vref=2000, ki=0, async_=0,
            low_pred=0, dtl_init=(8, 8, 8, 8), dtl_step=2, dtl_max=80, blank=0,   # A89
            err_low=0, err_high=0, el_tgt=0, eh_tgt=0, err_shift=0,              # A92
            slot_follow=0, slot_guard=0,                                         # A93
            slot_avg=0,                                                          # A97
            lo_pred=0, lo_learn=0, lo_tgt=0,                                     # A99
            lo_adm=0, lo_smax=0, lo_ff=0, lo_kff=0,                              # A100
            kp=0,                                                                # A104
            ext_ton_en=0, ext_ton=0, ext_slot=0, ext_ref=0,                      # C2
            slot_lo=0,                                                           # C02
            slot_trim=0, st_smax=1)                                              # A109


def pack(values, width):
    out = 0
    for k, v in enumerate(values):
        out |= (v & ((1 << width) - 1)) << (k * width)
    return out


def field(value, k, width):
    return (int(value) >> (k * width)) & ((1 << width) - 1)


def signed(v, width):
    return v - (1 << width) if v & (1 << (width - 1)) else v


class Ctrl:
    """Drives the controller and records every gate edge request as (win, fine, gate, level, phase)."""

    def __init__(self, dut):
        self.dut = dut
        self.edges = []
        self.cycle = 0

    async def start(self, **over):
        cfg = dict(BASE, **over)
        d = self.dut
        cocotb.start_soon(Clock(d.clk, 4, unit="ns").start())
        d.rst.value = 1
        d.cfg_ton.value = cfg["ton"]
        d.cfg_rs_high.value = cfg["rs_high"]
        d.cfg_rs_low.value = cfg["rs_low"]
        d.cfg_dt_step.value = cfg["dt_step"]
        d.cfg_dt_max.value = cfg["dt_max"]
        d.cfg_slot.value = pack(cfg["slot"], TW)
        d.cfg_pred.value = cfg["pred"]
        d.cfg_zvs_react.value = cfg["zvs_react"]
        d.cfg_trim.value = cfg["trim"]
        d.cfg_fine.value = cfg["fine"]
        d.dt_init.value = pack(cfg["dt_init"], TW)
        d.trim_init.value = pack(cfg["trim_init"], CW)
        d.cfg_start_s.value = cfg["start_s"]
        d.hand_req.value = 0
        d.cfg_t0.value = cfg["t0"]
        d.cfg_tdead.value = cfg["tdead"]
        d.cfg_ton_min.value = cfg["ton_min"]
        d.cfg_ton_max.value = cfg["ton_max"]
        d.cfg_vloop.value = cfg["vloop"]
        d.cfg_vref_code.value = cfg["vref"]
        d.cfg_ki.value = cfg["ki"]
        d.cfg_kp.value = cfg["kp"]                               # A104
        d.cfg_ext_ton.value = cfg["ext_ton_en"]; d.ext_ton.value = cfg["ext_ton"]   # C2
        d.ext_slot.value = cfg["ext_slot"]; d.ext_ref.value = cfg["ext_ref"]
        d.adc_valid.value = 0
        d.adc_code.value = 0
        d.cfg_async.value = cfg["async_"]
        d.a_valid.value = 0
        d.a_tlo.value = 0
        d.cfg_low_pred.value = cfg["low_pred"]                  # A89
        d.dtl_init.value = pack(cfg["dtl_init"], TW)
        d.cfg_dtl_step.value = cfg["dtl_step"]
        d.cfg_dtl_max.value = cfg["dtl_max"]
        d.cfg_blank.value = cfg["blank"]
        d.ml_valid.value = 0
        d.ml_early.value = 0
        d.ml_tv.value = 0
        d.cfg_err_low.value = cfg["err_low"]                     # A92
        d.cfg_err_high.value = cfg["err_high"]
        d.cfg_el_tgt.value = cfg["el_tgt"]
        d.cfg_eh_tgt.value = cfg["eh_tgt"]
        d.cfg_err_shift.value = cfg["err_shift"]
        d.ml_err.value = 0
        d.m_err.value = 0
        d.cfg_slot_follow.value = cfg["slot_follow"]             # A93
        d.cfg_slot_guard.value = cfg["slot_guard"]
        d.cfg_slot_avg.value = cfg["slot_avg"]                   # A97
        d.cfg_slot_lo.value = cfg["slot_lo"]                     # C02
        d.cfg_slot_trim.value = cfg["slot_trim"]; d.cfg_st_smax.value = cfg["st_smax"]   # A109
        d.cfg_lo_pred.value = cfg["lo_pred"]                     # A99
        d.cfg_lo_learn.value = cfg["lo_learn"]
        d.cfg_lo_tgt.value = cfg["lo_tgt"]
        d.mlo_valid.value = 0; d.mlo_early.value = 0; d.mlo_err.value = 0
        d.cfg_lo_adm.value = cfg["lo_adm"]; d.cfg_lo_smax.value = cfg["lo_smax"]   # A100
        d.cfg_lo_ff.value = cfg["lo_ff"]; d.cfg_lo_kff.value = cfg["lo_kff"]
        for s in ("cmp_i", "cmp_zl", "cmp_zh", "cmp_valley", "m_valid", "m_early", "m_flat", "r_valid", "r_below"):
            getattr(d, s).value = 0
        d.m_tv.value = 0
        await ClockCycles(d.clk, 3)
        await FallingEdge(d.clk)
        d.rst.value = 0
        cocotb.start_soon(self._monitor())

    async def _monitor(self):
        d = self.dut
        while True:
            await RisingEdge(d.clk)
            await ReadOnly()
            self.cycle += 1
            w = int(d.win_q.value)
            for k in range(N):
                if field(d.gh_ev.value, k, 1):
                    self.edges.append((w, field(d.gh_fine.value, k, FB), "H", field(d.gh_lvl.value, k, 1), k + 1))
                if field(d.gl_ev.value, k, 1):
                    self.edges.append((w, field(d.gl_fine.value, k, FB), "L", field(d.gl_lvl.value, k, 1), k + 1))

    def find(self, gate, level, phase, after=-1):
        for e in self.edges:
            if e[2] == gate and e[3] == level and e[4] == phase and e[0] + e[1] > after:
                return e
        return None

    async def until(self, gate, level, phase, after=-1, limit=400):
        for _ in range(limit):
            e = self.find(gate, level, phase, after)
            if e:
                return e
            await RisingEdge(self.dut.clk)
            await ReadOnly()
        raise AssertionError(f"no {gate}{level} edge on phase {phase} after {after}")

    async def set(self, **sig):
        await FallingEdge(self.dut.clk)
        for name, value in sig.items():
            getattr(self.dut, name).value = value


@cocotb.test()
async def ton_edge_window_and_fine(dut):
    """Reset: phase 1 HIGH from t = 0. Its high-side turn-off lands at Ton = 133 LSB: window 128, fine 5."""
    c = Ctrl(dut)
    await c.start()
    e = await c.until("H", 0, 1)
    assert (e[0], e[1]) == (128, 5), e
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert field(dut.state.value, 0, 2) == 1  # DOWN


@cocotb.test()
async def down_restart(dut):
    """No low-side ZVS signal: the low side turns on by the restart timer at t_off + 160 = 293 LSB."""
    c = Ctrl(dut)
    await c.start()
    e = await c.until("L", 1, 1)
    assert (e[0], e[1]) == (288, 5), e


@cocotb.test()
async def comparator_sync_latency(dut):
    """A comparator change reaches the logic through the 2-FF synchroniser: the edge follows 2-3 clocks later, fine 0."""
    c = Ctrl(dut)
    await c.start()
    await c.until("H", 0, 1)
    await c.set(cmp_zl=0b0001)
    w_set = int(dut.win_q.value)          # window of the clock edge just before the comparator changed
    e = await c.until("L", 1, 1)
    assert e[1] == 0
    lag = (e[0] - w_set) // WIN
    assert 2 <= lag <= 3, (lag, e, w_set)


@cocotb.test()
async def phase1_current_turn_off_and_bind(dut):
    """Phase 1 turns its low side off when its current comparator trips, marked current-decided."""
    c = Ctrl(dut)
    await c.start()
    await c.set(cmp_zl=0b0001)
    on = await c.until("L", 1, 1)
    await c.set(cmp_zl=0, cmp_i=0b0001)
    e = await c.until("L", 0, 1, after=on[0] + on[1])
    assert e[1] == 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert field(dut.lo_bind_cur.value, 0, 1) == 1
    assert field(dut.state.value, 0, 2) == 3  # UP


@cocotb.test()
async def predictive_turn_on_time(dut):
    """The predictive high-side turn-on lands at t_lo + dt_pred (85 LSB for phase 1)."""
    c = Ctrl(dut)
    await c.start()
    await c.set(cmp_zl=0b0001)
    on = await c.until("L", 1, 1)
    await c.set(cmp_zl=0, cmp_i=0b0001)
    lo = await c.until("L", 0, 1, after=on[0] + on[1])
    await c.set(cmp_i=0)
    t_lo = lo[0] + lo[1]
    hi = await c.until("H", 1, 1, after=t_lo)
    assert hi[0] + hi[1] == t_lo + 85, (lo, hi)


@cocotb.test()
async def slots_of_phases_2_to_4(dut):
    """Phases 2-4 turn their low sides off at t_ref + 400 / 800 / 1200 LSB (t_ref = 0 after reset)."""
    c = Ctrl(dut)
    await c.start()
    for k, t in ((2, 400), (3, 800), (4, 1200)):
        e = await c.until("L", 0, k)
        assert e[0] + e[1] == t, (k, e)


@cocotb.test()
async def predictive_correction(dut):
    """Early: dt_pred += step. Late: dt_pred = measured valley time. Flat: unchanged. Early is capped at dt_max."""
    c = Ctrl(dut)
    await c.start(dt_init=(85, 80, 80, 277))
    dtp = lambda k: field(dut.dt_pred.value, k, TW)
    await c.set(m_valid=0b0001, m_early=0b0001)
    await c.set(m_valid=0, m_early=0)
    await ReadOnly()
    assert dtp(0) == 87
    await c.set(m_valid=0b0001, m_tv=pack((77, 0, 0, 0), TW))
    await c.set(m_valid=0)
    await ReadOnly()
    assert dtp(0) == 77
    await c.set(m_valid=0b0001, m_flat=0b0001, m_tv=pack((10, 0, 0, 0), TW))
    await c.set(m_valid=0, m_flat=0)
    await ReadOnly()
    assert dtp(0) == 77
    await c.set(m_valid=0b1000, m_early=0b1000)
    await c.set(m_valid=0, m_early=0)
    await ReadOnly()
    assert dtp(3) == 278


@cocotb.test()
async def comparator_trim(dut):
    """The trim moves one LSB per current-decided turn-off (up when the edge current was below target),
    saturates, and ignores turn-offs the comparator did not decide."""
    c = Ctrl(dut)
    await c.start(trim_init=(126, 0, 0, 0))
    tr = lambda k: signed(field(dut.trim.value, k, CW), CW)
    await c.set(r_valid=0b0001, r_below=0b0001)
    await c.set(r_valid=0, r_below=0)
    await ReadOnly()
    assert tr(0) == 126  # lo_bind_cur is 0 after reset: no trim
    await c.set(cmp_zl=0b0001)
    on = await c.until("L", 1, 1)
    await c.set(cmp_zl=0, cmp_i=0b0001)
    await c.until("L", 0, 1, after=on[0] + on[1])
    await c.set(cmp_i=0)
    for expect in (127, 127):
        await c.set(r_valid=0b0001, r_below=0b0001)
        await c.set(r_valid=0, r_below=0)
        await ReadOnly()
        assert tr(0) == expect
    await c.set(r_valid=0b0001, r_below=0)
    await c.set(r_valid=0)
    await ReadOnly()
    assert tr(0) == 126


@cocotb.test()
async def counter_only_mode(dut):
    """cfg_fine = 0: every edge is placed at its window start (counter-only DPWM)."""
    c = Ctrl(dut)
    await c.start(fine=0)
    e = await c.until("H", 0, 1)
    assert (e[0], e[1]) == (128, 0), e
    e = await c.until("L", 0, 2)
    assert e[1] == 0 and e[0] == 384, e


@cocotb.test()
async def up_restart(dut):
    """A predictive delay longer than the restart time: the restart turns the high side on at t_lo + 160."""
    c = Ctrl(dut)
    await c.start(dt_init=(85, 200, 80, 93))
    lo = await c.until("L", 0, 2)
    hi = await c.until("H", 1, 2, after=lo[0] + lo[1])
    assert hi[0] + hi[1] == lo[0] + lo[1] + 160, (lo, hi)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert field(dut.on_how.value, 1, 3) == 3


# ---------------- A80: mode S, handover, voltage loop ----------------

@cocotb.test()
async def mode_s_period_and_dead_times(dut):
    """Mode S: phase 1 has period T0 = 1600 LSB (200 ns). Low side on at t_off + t_dead; low side off at
    t_on + T0 - t_dead; high side on after one dead time (17 LSB = 2.125 ns)."""
    c = Ctrl(dut)
    await c.start(start_s=1)
    off = await c.until("H", 0, 1)
    lon = await c.until("L", 1, 1)
    assert off[0] + off[1] == 133 and lon[0] + lon[1] == 133 + 17, (off, lon)
    loff = await c.until("L", 0, 1)
    assert loff[0] + loff[1] == 1600 - 17, loff
    hon = await c.until("H", 1, 1, after=loff[0] + loff[1])
    assert hon[0] + hon[1] == 1600, hon
    off2 = await c.until("H", 0, 1, after=hon[0] + hon[1])
    assert off2[0] + off2[1] == 1600 + 133, off2


@cocotb.test()
async def mode_s_chained_edges_in_one_window(dut):
    """A dead time shorter than a clock: the second edge of the pair is emitted in the same window."""
    c = Ctrl(dut)
    await c.start(start_s=1)
    off = await c.until("H", 0, 1)
    lon = await c.until("L", 1, 1)
    assert off[0] == lon[0] == 128 and (off[1], lon[1]) == (5, 22), (off, lon)


@cocotb.test()
async def handover_at_phase1_turn_on(dut):
    """hand_req switches to mode P only at the next phase-1 high-side turn-on."""
    c = Ctrl(dut)
    await c.start(start_s=1)
    await c.set(hand_req=1)
    await ReadOnly()
    assert int(dut.mode_p.value) == 0
    hon = await c.until("H", 1, 1, after=0)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.mode_p.value) == 1 and int(dut.t_ref.value) == hon[0] + hon[1], (hon, int(dut.t_ref.value))


@cocotb.test()
async def voltage_loop_integrates(dut):
    """Mode P with the loop on: each ADC sample adds ki * (vref - code) to the Ton accumulator (FRAC = 16)."""
    c = Ctrl(dut)
    await c.start(vloop=1, ki=65536 // 4)          # 0.25 LSB of Ton per ADC LSB of error
    assert int(dut.ton_now.value) == 133
    await c.set(adc_valid=1, adc_code=2000 - 40)   # 40 LSB below vref: +10 LSB of Ton
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 143, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000 + 2)    # 2 LSB above: -0.5 LSB, rounds 142.5 -> 143
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 143, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000 + 2)    # -0.5 more: 142.0
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 142, int(dut.ton_now.value)


@cocotb.test()
async def voltage_loop_clamps(dut):
    """The Ton command stays within [ton_min, ton_max]; in mode S or with the loop off, Ton is cfg_ton."""
    c = Ctrl(dut)
    await c.start(vloop=1, ki=65535)
    await c.set(adc_valid=1, adc_code=0)            # huge positive error
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 266
    await c.set(adc_valid=1, adc_code=4095)         # huge negative error
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 67


@cocotb.test()
async def voltage_loop_proportional(dut):
    """A104: Ton = round(ton_acc + kp * e), the proportional term held from one ADC sample to the next; with ki = 0
    Ton returns to the accumulator when the error is zero; the sum is clamped."""
    c = Ctrl(dut)
    await c.start(vloop=1, ki=0, kp=65536)          # 1 LSB of Ton per ADC LSB of error
    assert int(dut.ton_now.value) == 133
    await c.set(adc_valid=1, adc_code=2000 - 40)   # 40 LSB below vref: +40 LSB while the sample holds
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 173, int(dut.ton_now.value)
    await ClockCycles(dut.clk, 5)
    await ReadOnly()
    assert int(dut.ton_now.value) == 173, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000)        # zero error: back to the accumulator
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 133, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000 - 1000) # +1000 LSB: clamped at ton_max
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 266, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000 + 1000)
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 67, int(dut.ton_now.value)


@cocotb.test()
async def voltage_loop_pi(dut):
    """A104: with ki and kp together, the integral keeps its sum and the proportional part follows the last sample."""
    c = Ctrl(dut)
    await c.start(vloop=1, ki=65536 // 4, kp=65536 // 2)
    await c.set(adc_valid=1, adc_code=2000 - 40)   # integral +10, proportional +20
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 163, int(dut.ton_now.value)
    await c.set(adc_valid=1, adc_code=2000)        # integral stays +10, proportional 0
    await c.set(adc_valid=0)
    await ReadOnly()
    assert int(dut.ton_now.value) == 143, int(dut.ton_now.value)


@cocotb.test()
async def external_ton(dut):
    """C2: with cfg_ext_ton (loop off), Ton in mode P follows ext_ton at once; in mode S it stays cfg_ton."""
    c = Ctrl(dut)
    await c.start(vloop=0, ext_ton_en=1, ext_ton=150)
    assert int(dut.ton_now.value) == 150, int(dut.ton_now.value)
    await c.set(ext_ton=170)
    await ReadOnly()
    assert int(dut.ton_now.value) == 170, int(dut.ton_now.value)


# ---------------- A81: asynchronous fast path of phase 1 ----------------

async def _phase1_to_low(c):
    """Phase 1: high-side off at 133, low side on by the ZVS comparator; returns the low-on edge."""
    await c.set(cmp_zl=0b0001)
    on = await c.until("L", 1, 1)
    await c.set(cmp_zl=0)
    return on


@cocotb.test()
async def async_report_records_both_edges(dut):
    """Armed in LOW; the TDC report sets t_lo = a_tlo and t_on = a_tlo + dt_pred, enters HIGH, and no gate
    event is emitted for these two edges; t_ref follows t_on."""
    c = Ctrl(dut)
    await c.start(async_=1)
    await _phase1_to_low(c)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.arm1.value) == 1
    n_edges = len([e for e in c.edges if e[4] == 1])
    await c.set(a_valid=1, a_tlo=1000)
    await c.set(a_valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.arm1.value) == 0
    assert field(dut.state.value, 0, 2) == 0            # HIGH
    assert field(dut.lo_bind_cur.value, 0, 1) == 1
    assert int(dut.t_ref.value) == 1000 + 85, int(dut.t_ref.value)
    assert len([e for e in c.edges if e[4] == 1]) == n_edges   # no phase-1 gate event
    off = await c.until("H", 0, 1, after=1000)
    assert off[0] + off[1] == 1000 + 85 + 133, off       # Ton counted from the recorded turn-on


@cocotb.test()
async def async_ignores_synchronised_comparator(dut):
    """While armed, the synchronised current comparator does not turn phase 1's low side off."""
    c = Ctrl(dut)
    await c.start(async_=1)
    on = await _phase1_to_low(c)
    await c.set(cmp_i=0b0001)
    for _ in range(10):
        await RisingEdge(dut.clk)
    await ReadOnly()
    assert c.find("L", 0, 1, after=on[0] + on[1]) is None
    assert int(dut.arm1.value) == 1


@cocotb.test()
async def async_restart_stays_clocked(dut):
    """Without a report, the 400 ns restart still turns phase 1's low side off on the clocked path and disarms."""
    c = Ctrl(dut)
    await c.start(async_=1)
    on = await _phase1_to_low(c)
    t_lon = on[0] + on[1]
    e = await c.until("L", 0, 1, after=t_lon, limit=200)
    assert e[0] + e[1] == t_lon + 3200, (on, e)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.arm1.value) == 0 and field(dut.lo_bind_cur.value, 0, 1) == 0


# ---------------- A89: timed low-side turn-on ----------------

@cocotb.test()
async def low_pred_chained_in_the_turn_off_window(dut):
    """cfg_low_pred: the low side turns on at t_off + dtl. With dtl = 8 LSB (1 ns) that is 133 + 8 = 141, in the
    turn-off's own window (128): both edges come out in the same clock, and the phase enters LOW."""
    c = Ctrl(dut)
    await c.start(low_pred=1)
    off = await c.until("H", 0, 1)
    lon = await c.until("L", 1, 1)
    assert off[0] == lon[0] == 128 and (off[1], lon[1]) == (5, 13), (off, lon)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert field(dut.state.value, 0, 2) == 2  # LOW


@cocotb.test()
async def low_pred_edge_in_a_later_window(dut):
    """dtl = 40 LSB: the edge lands at 133 + 40 = 173, window 160, fine 13, emitted from DOWN."""
    c = Ctrl(dut)
    await c.start(low_pred=1, dtl_init=(40, 8, 8, 8))
    lon = await c.until("L", 1, 1)
    assert (lon[0], lon[1]) == (160, 13), lon
    assert field(dut.late_fires.value, 0, 16) == 0


@cocotb.test()
async def low_pred_ignores_the_zero_voltage_comparator(dut):
    """With cfg_low_pred the synchronised zero-voltage comparator no longer turns the low side on: the edge stays
    at t_off + dtl = 253 (window 224, fine 29), although the comparator is set right after the turn-off."""
    c = Ctrl(dut)
    await c.start(low_pred=1, dtl_init=(120, 8, 8, 8))
    await c.until("H", 0, 1)
    await c.set(cmp_zl=0b0001)
    lon = await c.until("L", 1, 1)
    assert (lon[0], lon[1]) == (224, 29), lon


@cocotb.test()
async def low_pred_correction(dut):
    """Early: dtl += step. Otherwise: dtl = the reported crossing time. Both capped at dtl_max (80)."""
    c = Ctrl(dut)
    await c.start(low_pred=1, dtl_init=(8, 8, 8, 79))
    dl = lambda k: field(dut.dtl.value, k, TW)
    await c.set(ml_valid=0b0001, ml_early=0b0001)
    await c.set(ml_valid=0, ml_early=0)
    await ReadOnly()
    assert dl(0) == 10
    await c.set(ml_valid=0b0001, ml_tv=pack((6, 0, 0, 0), TW))
    await c.set(ml_valid=0)
    await ReadOnly()
    assert dl(0) == 6
    await c.set(ml_valid=0b0001, ml_tv=pack((100, 0, 0, 0), TW))
    await c.set(ml_valid=0)
    await ReadOnly()
    assert dl(0) == 80
    await c.set(ml_valid=0b1000, ml_early=0b1000)
    await c.set(ml_valid=0, ml_early=0)
    await ReadOnly()
    assert dl(3) == 80


@cocotb.test()
async def low_pred_off_ignores_reports(dut):
    """cfg_low_pred = 0: zero-crossing reports do not change dtl (the A81 behaviour is untouched)."""
    c = Ctrl(dut)
    await c.start()
    await c.set(ml_valid=0b1111, ml_early=0b1111)
    await c.set(ml_valid=0, ml_early=0)
    await ReadOnly()
    assert all(field(dut.dtl.value, k, TW) == 8 for k in range(N))


@cocotb.test()
async def mode_s_unaffected_by_low_pred(dut):
    """Mode S keeps its fixed dead time with cfg_low_pred = 1: the edges of mode_s_chained_edges_in_one_window."""
    c = Ctrl(dut)
    await c.start(start_s=1, low_pred=1)
    off = await c.until("H", 0, 1)
    lon = await c.until("L", 1, 1)
    assert off[0] == lon[0] == 128 and (off[1], lon[1]) == (5, 22), (off, lon)


@cocotb.test()
async def blanking_holds_the_async_arm(dut):
    """Leading-edge blanking (BOUNDARY Section 8): with the timed low side (on at 141) and cfg_blank = 160 LSB (20 ns),
    phase 1 is LOW from window 160 but the front end is armed only from the first window with now - 141 >= 160,
    i.e. window 320."""
    c = Ctrl(dut)
    await c.start(low_pred=1, async_=1, blank=160)
    lon = await c.until("L", 1, 1)
    assert lon[0] + lon[1] == 141, lon
    first_low, first_arm = None, None
    for _ in range(40):
        await RisingEdge(dut.clk)
        await ReadOnly()
        now = int(dut.win_q.value) + WIN                 # the window the logic is in after this edge
        if first_low is None and field(dut.state.value, 0, 2) == 2:
            first_low = now
        if int(dut.arm1.value):
            first_arm = now
            break
    assert first_low is not None and first_low < 320, first_low
    assert first_arm == 320, first_arm


@cocotb.test()
async def blanking_holds_the_sync_current_comparator(dut):
    """With cfg_blank = 160 the synchronised current comparator, set right after the timed low-side turn-on at 141,
    turns the low side off only at window 320 (the first window with now - 141 >= 160), fine 0."""
    c = Ctrl(dut)
    await c.start(low_pred=1, blank=160)
    lon = await c.until("L", 1, 1)
    await c.set(cmp_i=0b0001)
    e = await c.until("L", 0, 1, after=lon[0] + lon[1])
    assert (e[0], e[1]) == (320, 0), e


# ---------------- A92: error-based correctors ----------------

async def _report_low(c, dut, k, early=0, err=0, tv=0):
    await c.set(ml_valid=1 << k, ml_early=early << k, ml_err=pack([err if q == k else 0 for q in range(N)], TW),
                ml_tv=pack([tv if q == k else 0 for q in range(N)], TW))
    await c.set(ml_valid=0, ml_early=0)
    await ReadOnly()
    return field(dut.dtl.value, k, TW)


async def _report_high(c, dut, k, early=0, flat=0, err=0, tv=0):
    await c.set(m_valid=1 << k, m_early=early << k, m_flat=flat << k,
                m_err=pack([err if q == k else 0 for q in range(N)], TW),
                m_tv=pack([tv if q == k else 0 for q in range(N)], TW))
    await c.set(m_valid=0, m_early=0, m_flat=0)
    await ReadOnly()
    return field(dut.dt_pred.value, k, TW)


@cocotb.test()
async def err_low_update(dut):
    """cfg_err_low, target 3, gain 1/2: late error 13 -> dtl 40 - (10 >> 1) = 35; error 0 (below target) ->
    35 - (-3 >>> 1) = 37 (arithmetic shift rounds towards minus infinity); error 3 (on target) -> unchanged;
    early -> + step (2), as A89. The crossing time ml_tv is ignored."""
    c = Ctrl(dut)
    await c.start(low_pred=1, dtl_init=(40, 8, 8, 8), err_low=1, el_tgt=3, err_shift=1)
    assert await _report_low(c, dut, 0, err=13, tv=70) == 35
    assert await _report_low(c, dut, 0, err=0, tv=70) == 37
    assert await _report_low(c, dut, 0, err=3, tv=70) == 37
    assert await _report_low(c, dut, 0, early=1) == 39


@cocotb.test()
async def err_low_clamps(dut):
    """Floor 0 and cap dtl_max (80): dtl 4 with error 40 at gain 1 -> 0, not negative; dtl 79 with error 0,
    target 10 -> 89 capped to 80; early at the cap stays 80."""
    c = Ctrl(dut)
    await c.start(low_pred=1, dtl_init=(4, 8, 8, 79), err_low=1, el_tgt=10, err_shift=0)
    assert await _report_low(c, dut, 0, err=40) == 0
    assert await _report_low(c, dut, 3, err=0) == 80
    assert await _report_low(c, dut, 3, early=1) == 80


@cocotb.test()
async def err_high_update(dut):
    """cfg_err_high, target 3, gain 1/2, dt_pred 85: late error 23 -> 85 - 10 = 75; flat -> unchanged; early ->
    + step (2); error 0 -> 77 - (-2) = 79. The valley time m_tv is ignored."""
    c = Ctrl(dut)
    await c.start(err_high=1, eh_tgt=3, err_shift=1)
    assert await _report_high(c, dut, 0, err=23, tv=10) == 75
    assert await _report_high(c, dut, 0, flat=1, err=50, tv=10) == 75
    assert await _report_high(c, dut, 0, early=1) == 77
    assert await _report_high(c, dut, 0, err=0, tv=10) == 79


@cocotb.test()
async def err_high_clamps(dut):
    """Floor 0 and cap dt_max (278): dt_pred 85, error 300 at gain 1 -> 0; dt_pred 277 (phase 4), error 0,
    target 5 -> 282 capped to 278."""
    c = Ctrl(dut)
    await c.start(dt_init=(85, 80, 80, 277), err_high=1, eh_tgt=5, err_shift=0)
    assert await _report_high(c, dut, 0, err=300) == 0
    assert await _report_high(c, dut, 3, err=0) == 278


@cocotb.test()
async def err_high_restart_base(dut):
    """After a restart turn-on (on_how = 3) the base is cfg_rs_high (160), not dt_pred (200): phase 2 restarts
    at t_lo + 160; a report with error 20, target 0, gain 1 then gives 160 - 20 = 140."""
    c = Ctrl(dut)
    await c.start(dt_init=(85, 200, 80, 93), err_high=1, eh_tgt=0, err_shift=0)
    lo = await c.until("L", 0, 2)
    await c.until("H", 1, 2, after=lo[0] + lo[1])
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert field(dut.on_how.value, 1, 3) == 3
    assert await _report_high(c, dut, 1, err=20) == 140


@cocotb.test()
async def err_bits_off_keep_a89_rules(dut):
    """Both bits 0: the error fields are ignored. Low side: dtl = ml_tv (6); high side: dt_pred = m_tv (77)."""
    c = Ctrl(dut)
    await c.start(low_pred=1, el_tgt=3, eh_tgt=3, err_shift=1)
    assert await _report_low(c, dut, 0, err=50, tv=6) == 6
    assert await _report_high(c, dut, 0, err=50, tv=77) == 77


# ---------------- A93: period-following slots and the missed-slot guard ----------------

async def _phase1_cycle(c, after, hold=0):
    """Drive phase 1 through one mode-P cycle from HIGH: wait for its turn-off, then the zero-voltage comparator
    (low side on), the current comparator (low side off, `hold` clocks later than otherwise) and the predictive
    turn-on (dt_pred 85). Returns the turn-on time (LSB)."""
    off = await c.until("H", 0, 1, after=after)
    await c.set(cmp_zl=0b0001)
    lon = await c.until("L", 1, 1, after=off[0] + off[1])
    if hold:
        await ClockCycles(c.dut.clk, hold)
    await c.set(cmp_zl=0, cmp_i=0b0001)
    lo = await c.until("L", 0, 1, after=lon[0] + lon[1])
    await c.set(cmp_i=0)
    hi = await c.until("H", 1, 1, after=lo[0] + lo[1])
    return hi[0] + hi[1]


@cocotb.test()
async def guard_fires_a_missed_slot(dut):
    """cfg_slot_guard, fixed slots 600/1200/1800: phase 1 turns on again at t_on1 (< 600), before phase 2's slot of
    reference 0. The guard turns phase 2's low side off right after the reference changes (fine 0, before 600),
    and phases 3 and 4 likewise; each counts one late fire."""
    c = Ctrl(dut)
    await c.start(slot_guard=1, slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    assert t_on1 < 600, t_on1
    for k in (2, 3, 4):
        e = await c.until("L", 0, k)
        assert e[1] == 0 and t_on1 <= e[0] < t_on1 + 3 * WIN, (k, t_on1, e)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert [field(dut.late_fires.value, k, 16) for k in (1, 2, 3)] == [1, 1, 1]


@cocotb.test()
async def without_guard_the_slot_moves(dut):
    """Bits off (A92 behaviour): with the same drive, phase 2's slot moves to the new reference: t_on1 + 600."""
    c = Ctrl(dut)
    await c.start(slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    e = await c.until("L", 0, 2, limit=800)
    assert e[0] + e[1] == t_on1 + 600, (t_on1, e)


@cocotb.test()
async def follow_slots_at_k_period_over_n(dut):
    """cfg_slot_follow with fixed slots set far away (4000/8000/12000): after the second phase-1 turn-on, phase k
    turns its low side off at t_on2 + (k - 1) * (t_on2 - t_on1) // 4."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot=(4000, 8000, 12000))
    t_on1 = await _phase1_cycle(c, -1)
    t_on2 = await _phase1_cycle(c, t_on1)
    per = t_on2 - t_on1
    for k in (2, 3, 4):
        e = await c.until("L", 0, k, after=t_on2)
        assert e[0] + e[1] == t_on2 + ((k - 1) * per) // 4, (k, t_on1, t_on2, e)


@cocotb.test()
async def follow_needs_two_turn_ons(dut):
    """cfg_slot_follow: after only one phase-1 turn-on the configured slot still applies (phase 2 at t_on1 + 600,
    the reference changed once, so the period is not yet known)."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    e = await c.until("L", 0, 2, limit=800)
    assert e[0] + e[1] == t_on1 + 600, (t_on1, e)


@cocotb.test()
async def avg_slots_from_two_periods(dut):
    """cfg_slot_avg with cfg_slot_follow, fixed slots set far away (4000/8000/12000): after the third phase-1
    turn-on, with two different periods P1 and P2, phase k turns its low side off at
    t_on3 + (k - 1) * (P1 + P2) // 8, not at A93's t_on3 + (k - 1) * P2 // 4."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot_avg=1, slot=(4000, 8000, 12000))
    t_on1 = await _phase1_cycle(c, -1)
    t_on2 = await _phase1_cycle(c, t_on1, hold=10)
    t_on3 = await _phase1_cycle(c, t_on2)
    p1, p2 = t_on2 - t_on1, t_on3 - t_on2
    assert all(((k - 1) * (p1 + p2)) // 8 != ((k - 1) * p2) // 4 for k in (2, 3, 4)), (p1, p2)
    for k in (2, 3, 4):
        e = await c.until("L", 0, k, after=t_on3)
        assert e[0] + e[1] == t_on3 + ((k - 1) * (p1 + p2)) // 8, (k, p1, p2, t_on3, e)


@cocotb.test()
async def avg_needs_three_turn_ons(dut):
    """cfg_slot_avg with cfg_slot_follow: after two phase-1 turn-ons (one period known) the configured slot still
    applies (phase 2 at t_on2 + 600), where A93's rule alone would give t_on2 + (t_on2 - t_on1) // 4."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot_avg=1, slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    t_on2 = await _phase1_cycle(c, t_on1)
    assert t_on1 < 600 and t_on2 - t_on1 < 600, (t_on1, t_on2)
    e = await c.until("L", 0, 2, after=t_on2, limit=800)
    assert e[0] + e[1] == t_on2 + 600, (t_on1, t_on2, e)


@cocotb.test()
async def avg_without_follow_keeps_the_configured_slot(dut):
    """cfg_slot_avg alone (cfg_slot_follow 0): after three phase-1 turn-ons phase 2 still turns its low side off
    at the configured slot, t_on3 + 600."""
    c = Ctrl(dut)
    await c.start(slot_avg=1, slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    t_on2 = await _phase1_cycle(c, t_on1)
    t_on3 = await _phase1_cycle(c, t_on2)
    assert max(t_on1, t_on2 - t_on1, t_on3 - t_on2) < 600, (t_on1, t_on2, t_on3)
    e = await c.until("L", 0, 2, after=t_on3, limit=800)
    assert e[0] + e[1] == t_on3 + 600, (t_on3, e)


@cocotb.test()
async def lo_pred_learns_then_times_phase1_turn_off(dut):
    """cfg_lo_pred, cfg_lo_learn 2: the first two phase-1 turn-offs are comparator-decided and set dlo to their on-low
    interval; then lo_timed1 is set and the third turn-off is a timed edge at t_lon + dlo, without the comparator."""
    c = Ctrl(dut)
    await c.start(lo_pred=1, lo_learn=2)
    t1 = await _phase1_cycle(c, -1)
    t2 = await _phase1_cycle(c, t1, hold=3)
    lon = [e for e in c.edges if e[2] == "L" and e[3] == 1 and e[4] == 1][-1]
    lo = [e for e in c.edges if e[2] == "L" and e[3] == 0 and e[4] == 1][-1]
    learned = (lo[0] + lo[1]) - (lon[0] + lon[1])
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.dlo1.value) == learned and int(dut.lo_timed1.value) == 1, (int(dut.dlo1.value), learned)
    off = await c.until("H", 0, 1, after=t2)
    await c.set(cmp_zl=0b0001)
    lon3 = await c.until("L", 1, 1, after=off[0] + off[1])
    await c.set(cmp_zl=0)
    lo3 = await c.until("L", 0, 1, after=lon3[0] + lon3[1], limit=800)
    assert lo3[0] + lo3[1] == lon3[0] + lon3[1] + learned, (lon3, lo3, learned)


@cocotb.test()
async def lo_pred_sign_update(dut):
    """Once timed, a crossing report that is early or below cfg_lo_tgt (3) raises dlo by 1 LSB; one at or above
    the target lowers it by 1 LSB."""
    c = Ctrl(dut)
    await c.start(lo_pred=1, lo_learn=1, lo_tgt=3)
    await _phase1_cycle(c, -1)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.lo_timed1.value) == 1
    d0 = int(dut.dlo1.value)
    for early, err, delta in ((1, 0, +1), (0, 5, -1), (0, 2, +1), (0, 3, -1)):
        await c.set(mlo_valid=1, mlo_early=early, mlo_err=err)
        await c.set(mlo_valid=0)
        await RisingEdge(dut.clk)
        await ReadOnly()
        d1 = int(dut.dlo1.value)
        assert d1 - d0 == delta, (early, err, d0, d1)
        d0 = d1


@cocotb.test()
async def lo_pred_timed_does_not_arm_the_front_end(dut):
    """cfg_async with cfg_lo_pred and cfg_lo_learn 0 (timed at once, dlo 0): phase 1's front end is never armed in
    LOW, and its low side turns off at the timed edge t_lon + 0, placed in the next window (a late fire)."""
    c = Ctrl(dut)
    await c.start(async_=1, lo_pred=1, lo_learn=0)
    off = await c.until("H", 0, 1)
    await c.set(cmp_zl=0b0001)
    lon = await c.until("L", 1, 1, after=off[0] + off[1])
    await c.set(cmp_zl=0)
    armed = []
    for _ in range(10):
        await RisingEdge(dut.clk)
        await ReadOnly()
        armed.append(int(dut.arm1.value))
    lo = c.find("L", 0, 1, after=lon[0] + lon[1])
    assert not any(armed) and lo is not None and lo[0] + lo[1] == lon[0] + lon[1] + WIN, (armed, lon, lo)


@cocotb.test()
async def lo_adm_doubles_while_decisions_agree(dut):
    """cfg_lo_adm, cfg_lo_smax 4, once timed: three "up" reports step dlo by +1, +2, +4; a fourth by +4 (the cap);
    then a "down" report steps it by -1 (back to the unit step)."""
    c = Ctrl(dut)
    await c.start(lo_pred=1, lo_learn=1, lo_tgt=3, lo_adm=1, lo_smax=4)
    await _phase1_cycle(c, -1)
    await RisingEdge(dut.clk)
    await ReadOnly()
    d0 = int(dut.dlo1.value)
    for early, err, delta in ((1, 0, +1), (0, 1, +2), (1, 0, +4), (0, 0, +4), (0, 9, -1)):
        await c.set(mlo_valid=1, mlo_early=early, mlo_err=err)
        await c.set(mlo_valid=0)
        await RisingEdge(dut.clk)
        await ReadOnly()
        d1 = int(dut.dlo1.value)
        assert d1 - d0 == delta, (early, err, d0, d1)
        d0 = d1


@cocotb.test()
async def lo_ff_moves_dlo_with_ton(dut):
    """cfg_lo_ff with cfg_lo_kff 9, once timed: raising ton by 2 LSB raises dlo by 18 LSB; lowering it by 1 LSB
    lowers dlo by 9 LSB."""
    c = Ctrl(dut)
    await c.start(lo_pred=1, lo_learn=1, lo_ff=1, lo_kff=9)
    await _phase1_cycle(c, -1)
    await RisingEdge(dut.clk)
    await ReadOnly()
    d0 = int(dut.dlo1.value)
    await c.set(cfg_ton=BASE["ton"] + 2)
    await ClockCycles(dut.clk, 2)
    await ReadOnly()
    d1 = int(dut.dlo1.value)
    assert d1 - d0 == 18, (d0, d1)
    await c.set(cfg_ton=BASE["ton"] + 1)
    await ClockCycles(dut.clk, 2)
    await ReadOnly()
    assert int(dut.dlo1.value) - d1 == -9, (d1, int(dut.dlo1.value))


# ---------------- C02: slots referenced to phase 1's low-side turn-off ----------------

@cocotb.test()
async def follow_slots_from_phase1_low_off(dut):
    """cfg_slot_lo with cfg_slot_follow, fixed slots set far away (4000/8000/12000): after the second phase-1
    turn-on, phase k turns its low side off at t_lo + (k - 1) * (t_on2 - t_on1) // 4, t_lo phase 1's low-side
    turn-off before t_on2 (one predictive delay earlier than A93's reference t_on2); t_lo1 reports it. The second
    cycle is held 10 clocks so that phase 2's slot lies two windows after t_on2 (T/N - dt_pred > 2 windows, as in
    the circuit: 58 - 9.4 ns)."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot_lo=1, slot=(4000, 8000, 12000))
    t_on1 = await _phase1_cycle(c, -1)
    t_on2 = await _phase1_cycle(c, t_on1, hold=10)
    lo = [e for e in c.edges if e[2] == "L" and e[3] == 0 and e[4] == 1 and t_on1 < e[0] + e[1] < t_on2][-1]
    t_lo = lo[0] + lo[1]
    per = t_on2 - t_on1
    assert 0 < t_on2 - t_lo and t_lo + per // 4 > t_on2 + 2 * WIN, (t_on1, t_lo, t_on2)
    assert int(dut.t_lo1.value) == t_lo, (int(dut.t_lo1.value), t_lo)
    for k in (2, 3, 4):
        e = await c.until("L", 0, k, after=t_on2)
        assert e[0] + e[1] == t_lo + ((k - 1) * per) // 4, (k, t_lo, per, e)


@cocotb.test()
async def slot_lo_keeps_configured_slots_at_t_ref(dut):
    """cfg_slot_lo without the period known (one phase-1 turn-on, cfg_slot_follow 1): the configured slot stays
    referenced to the turn-on, phase 2 at t_on1 + 600."""
    c = Ctrl(dut)
    await c.start(slot_follow=1, slot_lo=1, slot=(600, 1200, 1800))
    t_on1 = await _phase1_cycle(c, -1)
    e = await c.until("L", 0, 2, limit=800)
    assert e[0] + e[1] == t_on1 + 600, (t_on1, e)


# ---------------- A109: valley trim of the slotted phases ----------------

async def _report_r(c, dut, k, below):
    await c.set(r_valid=1 << k, r_below=below << k)
    await c.set(r_valid=0, r_below=0)
    await ReadOnly()
    return signed(field(dut.slot_ofs.value, k, TW), TW)


@cocotb.test()
async def slot_trim_adaptive_step(dut):
    """cfg_slot_trim, st_smax 8, mode P: phase 2's reports 'above the target' move its slot later by 1, 2, 4, 8, 8
    (sofs 1, 3, 7, 15, 23); a 'below' report then moves it earlier by 1 (22), a second by 2 (20)."""
    c = Ctrl(dut)
    await c.start(slot_trim=1, st_smax=8)
    got = [await _report_r(c, dut, 1, 0) for _ in range(5)]
    got += [await _report_r(c, dut, 1, 1) for _ in range(2)]
    assert got == [1, 3, 7, 15, 23, 22, 20], got


@cocotb.test()
async def slot_trim_moves_the_slot(dut):
    """cfg_slot_trim, fixed slots 400/800/1200: three 'above' reports on phase 2 before its slot (sofs 7) turn its
    low side off at 407 instead of 400; phase 3, without reports, stays at 800."""
    c = Ctrl(dut)
    await c.start(slot_trim=1, st_smax=8)
    for _ in range(3):
        await _report_r(c, dut, 1, 0)
    e = await c.until("L", 0, 2)
    assert e[0] + e[1] == 407, e
    e = await c.until("L", 0, 3)
    assert e[0] + e[1] == 800, e


@cocotb.test()
async def slot_trim_not_phase1(dut):
    """cfg_slot_trim: reports on phase 1 (not a slotted phase in a master) leave its offset at 0."""
    c = Ctrl(dut)
    await c.start(slot_trim=1, st_smax=8)
    assert [await _report_r(c, dut, 0, 0) for _ in range(3)] == [0, 0, 0]


@cocotb.test()
async def slot_trim_not_in_mode_s(dut):
    """cfg_slot_trim: in mode S (start_s) a slotted phase's reports leave its offset at 0."""
    c = Ctrl(dut)
    await c.start(slot_trim=1, st_smax=8, start_s=1)
    assert [await _report_r(c, dut, 1, 0) for _ in range(3)] == [0, 0, 0]

