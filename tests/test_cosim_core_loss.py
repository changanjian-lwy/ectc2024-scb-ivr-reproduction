"""A221: the core-loss resistor r_core across each phase's inductor (circuit.py) - its stamp, and the damping of an
idle phase's ring that V6 (R = 0, switches off) does not have."""
import numpy as np

from scb_ivr.cosim.circuit import CircuitParams, Sim

N = 4
OFF = (False,) * (2 * N)


def test_r_core_stamps_a_conductance_from_each_switch_node_to_the_output():
    a0 = Sim(CircuitParams(R=0.0)).system(OFF, False)[0]
    s1 = Sim(CircuitParams(R=0.0, r_core=2.0))
    a1 = s1.system(OFF, False)[0]
    d = a1 - a0
    io = s1.idx["out"]
    want = np.zeros_like(d)
    for k in range(1, N + 1):
        ix = s1.idx[f"x{k}"]
        want[ix, ix] -= 0.5; want[io, io] -= 0.5; want[ix, io] += 0.5; want[io, ix] += 0.5
    assert np.array_equal(d, want)


def test_r_core_zero_changes_nothing():
    for cond in (OFF, (True,) + (False,) * (2 * N - 1)):
        assert np.array_equal(Sim(CircuitParams()).system(cond, True)[0], Sim(CircuitParams(r_core=0.0)).system(cond, True)[0])


def _ring(r_core, t_end=1e-6):
    p = CircuitParams(R=0.0, r_core=r_core, t_ramp=0.0, vin=48.0)
    s = Sim(p)
    y = np.zeros(s.ns)
    for k in range(1, N):                                    # the ladder at its nominal voltages, the output at 1 V
        y[s.idx[f"a{k}"]] = 48.0 * (N - k) / N
    y[s.idx["out"]] = 1.0
    for k in range(1, N + 1):
        y[s.idx[f"x{k}"]] = 1.0
    y[s.nv] = 5.0                                            # phase 1 idle with 5 A in its inductor
    h, t, last = p.h, 0.0, []
    while t < t_end:
        y = s.step(y, OFF, h, False, t, False)
        t += h
        if t > t_end - 100e-9:
            last.append(abs(y[s.nv]))
    return max(last)


def test_an_idle_ring_decays_with_r_core_and_not_without():
    assert _ring(0.0) > 2.0
    assert _ring(2.9) < 0.5
