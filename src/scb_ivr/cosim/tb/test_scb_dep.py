"""A132: unit tests of scb_dep (the depth loop) on its own build (toplevel scb_dep, AW 12, DW 8)."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge


def sval(v, width=8):
    v = int(v) & ((1 << width) - 1)
    return v - (1 << width) if v >> (width - 1) else v


async def setup(dut, en=1, wsh=2, smax=4, dmin=-3, dmax=12, ehold=8):
    cocotb.start_soon(Clock(dut.clk, 4, unit="ns").start())
    for name, v in (("en", 0), ("v_valid", 0), ("v_high", 0), ("adc_valid", 0), ("err", 0), ("wsh", wsh), ("smax", smax),
                    ("dmin", dmin & 0xFF), ("dmax", dmax & 0xFF), ("ehold", ehold)):
        getattr(dut, name).value = v
    dut.rst.value = 1
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.en.value = en


async def report(dut, high, err=0):
    await FallingEdge(dut.clk)
    dut.v_valid.value, dut.v_high.value, dut.adc_valid.value, dut.err.value = 1, int(high), 1, err & 0x1FFF
    await FallingEdge(dut.clk)
    dut.v_valid.value, dut.v_high.value, dut.adc_valid.value, dut.err.value = 0, 0, 0, 0
    await ClockCycles(dut.clk, 2)


async def window(dut, highs, n=4, err_at=None, err=0):
    for j in range(n):
        await report(dut, j < highs, err if j == err_at else 0)
    await FallingEdge(dut.clk)
    return sval(dut.dep.value)


@cocotb.test()
async def off_holds_zero(dut):
    await setup(dut, en=0)
    for _ in range(3):
        assert await window(dut, 4) == 0


@cocotb.test()
async def majority_and_variable_step(dut):
    await setup(dut)
    seq = [(3, 1), (4, 3), (4, 7), (4, 11), (0, 10), (2, 8), (1, 4)]   # (highs of 4, dep after): +1 +2 +4 +4(smax) -1 -2(tie) -4
    for highs, want in seq:
        assert await window(dut, highs) == want, (highs, want)


@cocotb.test()
async def spoiled_window(dut):
    await setup(dut)
    assert await window(dut, 4) == 1
    assert await window(dut, 4) == 3
    assert await window(dut, 4, err_at=1, err=-9) == 3          # |err| 9 > 8: no decision
    assert await window(dut, 4) == 4                            # step back to 1
    assert await window(dut, 4, err_at=3, err=8) == 6           # |err| 8 is not above ehold: decision, step 2


@cocotb.test()
async def clamped_high(dut):
    await setup(dut, smax=8, dmax=5)
    for want in (1, 3, 5, 5):
        assert await window(dut, 4) == want


@cocotb.test()
async def clamped_low(dut):
    await setup(dut, smax=8)
    for want in (-1, -3, -3):
        assert await window(dut, 0) == want


@cocotb.test()
async def en_low_holds(dut):
    await setup(dut)
    assert await window(dut, 4) == 1
    assert await window(dut, 4) == 3
    dut.en.value = 0
    assert await window(dut, 0) == 3
    dut.en.value = 1
    assert await window(dut, 4) == 4                            # the window and the step restart
