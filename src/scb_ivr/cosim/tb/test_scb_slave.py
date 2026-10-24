"""cocotb unit tests of a slave module's controller (scb_ctrl with SLAVE = 1): phase 1 slotted at ext_slot once per
ext_ref, C06's slot floor (cfg_slave_floor) with A141's late report, and A215's registers after a change of the
broadcast Ton. The fixture and LSB units are test_scb_ctrl's (start_s 0: mode P
from reset; a slave's phase 1 resets LOW; dt_init of phase 1 85, Ton 133)."""
import cocotb
from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge

from test_scb_ctrl import Ctrl, _report_high, field


async def _now(dut):
    await RisingEdge(dut.clk)
    await ReadOnly()
    return int(dut.win_q.value)


async def _floor_report(c, t):
    await c.set(a_valid=1, a_tlo=t)
    await c.set(a_valid=0)
    await RisingEdge(c.dut.clk)
    await ReadOnly()


async def _back_to_low(c, t_on):
    """High side off at t_on + Ton, then the low side on by the ZVS comparator; returns the low-on time."""
    off = await c.until("H", 0, 1, after=t_on)
    await c.set(cmp_zl=0b0001)
    lon = await c.until("L", 1, 1, after=off[0] + off[1])
    await c.set(cmp_zl=0)
    return lon[0] + lon[1]


@cocotb.test()
async def slave_slot_floor_off_never_arms(dut):
    """Without cfg_slave_floor a slave's phase 1 is not armed in LOW (C2 behaviour)."""
    c = Ctrl(dut)
    await c.start(ext_ref=7, ext_slot=4000)
    await ClockCycles(dut.clk, 5)
    await ReadOnly()
    assert field(dut.state.value, 0, 2) == 2 and int(dut.arm1.value) == 0


@cocotb.test()
async def slave_slot_floor_arms_in_low(dut):
    """cfg_slave_floor: a slave's phase 1 in LOW (mode P) is armed until its slot."""
    c = Ctrl(dut)
    await c.start(slave_floor=1, ext_ref=7, ext_slot=4000)
    await ClockCycles(dut.clk, 5)
    await ReadOnly()
    assert field(dut.state.value, 0, 2) == 2 and int(dut.arm1.value) == 1


@cocotb.test()
async def slave_floor_after_reference_is_its_slot(dut):
    """Reference 7 is known (slot at 4000): a floor report at t sets t_on = t + dt_pred, enters HIGH without a gate
    event and without binding the trim; slot 4000 never fires; the next reference's slot fires as usual."""
    c = Ctrl(dut)
    await c.start(slave_floor=1, ext_ref=7, ext_slot=4000)
    t = await _now(dut)
    await _floor_report(c, t)
    assert field(dut.state.value, 0, 2) == 0 and int(dut.arm1.value) == 0
    assert field(dut.lo_bind_cur.value, 0, 1) == 0 and int(dut.t_ref.value) == t + 85
    await _back_to_low(c, t)
    while await _now(dut) < 4200:
        pass
    assert c.find("L", 0, 1) is None
    t2 = await _now(dut)
    await c.set(ext_ref=9, ext_slot=t2 + 300)
    e = await c.until("L", 0, 1, after=t2)
    assert e[0] + e[1] == t2 + 300 and int(dut.late_fires.value) == 0


@cocotb.test()
async def slave_floor_before_reference_consumes_the_next(dut):
    """Reference 7's slot fires at 300; back in LOW the floor fires before reference 9 arrives: reference 9's slot
    (while HIGH) is consumed, reference 11's fires at its slot."""
    c = Ctrl(dut)
    await c.start(slave_floor=1, ext_ref=7, ext_slot=300)
    e = await c.until("L", 0, 1)
    assert e[0] + e[1] == 300
    await _back_to_low(c, 300)
    t = await _now(dut)
    await _floor_report(c, t)
    assert field(dut.state.value, 0, 2) == 0
    await c.set(ext_ref=9, ext_slot=t + 200)
    await _back_to_low(c, t)
    while await _now(dut) < t + 1200:
        pass
    assert c.find("L", 0, 1, after=300) is None
    t2 = await _now(dut)
    await c.set(ext_ref=11, ext_slot=t2 + 300)
    e = await c.until("L", 0, 1, after=t2)
    assert e[0] + e[1] == t2 + 300


@cocotb.test()
async def slave_floor_late_report_after_the_slot_moves_t_on(dut):
    """cfg_floor_late: reference 7's slot fires at 300 (UP); a floor report at 290 arriving after it is the turn-off:
    t_on = 290 + dt_pred = 375, HIGH without a gate event, t_lo1 still the slot (300), the turn-off at 375 + Ton = 508."""
    c = Ctrl(dut)
    await c.start(slave_floor=1, floor_late=1, ext_ref=7, ext_slot=300)
    e = await c.until("L", 0, 1)
    assert e[0] + e[1] == 300 and field(dut.state.value, 0, 2) == 3
    await _floor_report(c, 290)
    assert field(dut.state.value, 0, 2) == 0 and int(dut.t_ref.value) == 375 and int(dut.t_lo1.value) == 300
    off = await c.until("H", 0, 1, after=300)
    assert off[0] + off[1] == 508 and c.find("H", 1, 1) is None


@cocotb.test()
async def slave_ton_lat_follows_the_broadcast(dut):
    """A215, cfg_ton_lat 3 on a slave: a change of ext_ton (150 -> 170 LSB) is seen in its first clock and reaches
    the phases 3 edges after that clock's end."""
    c = Ctrl(dut)
    await c.start(ext_ton_en=1, ext_ton=150, ext_ref=7, ext_slot=40000, ton_lat=3)
    await ClockCycles(dut.clk, 3)
    await ReadOnly()
    assert field(dut.ton_ph.value, 0, 32) == 150
    await c.set(ext_ton=170)
    await ReadOnly()
    assert int(dut.ton_now.value) == 170 and int(dut.lat_ev.value) == 1
    seen = []
    for _ in range(5):
        await RisingEdge(dut.clk)
        await ReadOnly()
        seen.append(field(dut.ton_ph.value, 0, 32))
    assert seen == [150, 150, 150, 170, 170], seen


@cocotb.test()
async def slave_rev_skips_phase1(dut):
    """A245 on a slave: rev_n 2 leaves phase 1's dt_pred (85) after three m_rev reports, as on a master; phase 2's
    second one lowers it (80 -> 78)."""
    c = Ctrl(dut)
    await c.start(ext_ref=7, ext_slot=40000, err_high=1, eh_tgt=3, err_shift=1, rev_n=2)
    assert [await _report_high(c, dut, 0, err=3, tv=10, rev=1) for _ in range(3)] == [85, 85, 85]
    assert [await _report_high(c, dut, 1, err=3, tv=10, rev=1) for _ in range(2)] == [80, 78]
