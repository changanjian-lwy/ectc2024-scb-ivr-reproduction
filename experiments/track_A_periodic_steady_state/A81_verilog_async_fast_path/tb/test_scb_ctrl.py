"""cocotb unit tests of the A81 Verilog controller (rtl/scb_ctrl.v), one design requirement per test.

Copied from A80's tests (which include A77's): all run with cfg_async = 0 (backward compatibility);
the A81 tests at the end cover the asynchronous fast path of phase 1.

A80 docstring follows.

Copied from A77's tests: the ten A77 tests run unchanged in mode P from reset (backward compatibility);
the new tests cover mode S, the handover and the voltage loop.

Time is in LSB units: 1 LSB = T_clk / 32 = 125 ps at the 250 MHz base case.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

N, TW, FB, CW = 4, 32, 5, 8
WIN = 1 << FB
BASE = dict(ton=133, rs_high=160, rs_low=3200, dt_step=2, dt_max=278,
            slot=(400, 800, 1200), dt_init=(85, 80, 80, 93), trim_init=(0, 0, 0, 0),
            pred=1, zvs_react=0, trim=1, fine=1,
            start_s=0, t0=1600, tdead=17, ton_min=67, ton_max=266, vloop=0, vref=2000, ki=0, async_=0)


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
        d.adc_valid.value = 0
        d.adc_code.value = 0
        d.cfg_async.value = cfg["async_"]
        d.a_valid.value = 0
        d.a_tlo.value = 0
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
