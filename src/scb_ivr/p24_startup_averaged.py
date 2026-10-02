"""D58: an averaged model of the P24 module's start-up and output-voltage loop (A103).

State: Vo on the output capacitance Co, and the voltage loop's Ton accumulator.
- Mode S (fixed timing, open loop, Ton = ton_s): the module is a voltage source a_s * Ton * Vin(t) / 48 behind
  r_s. a_s is the reference co-simulation's no-load mode-S output (1.2761 V at 533 LSB, 48 V); r_s is from A73
  run 6 (0.933 V under the 4 mOhm load, an older plant), so it is an approximation.
- Mode P (boundary conduction with a fixed negative-current target): each phase's average current is
  (V_rail - Vo) Ton / (2 L) - i_neg, whatever the period (a triangle from -i_neg to the peak and back); the module
  delivers k times four of it. k is set by the reference co-simulation's full-load steady state (Ton 568 LSB at
  1.000 V and 250 A). The period is Ton + (V_rail - Vo) Ton / Vo + t_x, t_x from the same steady state (232.2 ns).
- The loop (A79, mode P only): once per phase-1 period, Ton_acc += ki (Vref - Vo), clamped to [ton_min, ton_max].
- The input ramps linearly to 48 V over t_ramp; V_rail = Vin / 4. The load is resistive from t_load.
validate() runs the reference sequence and compares it with the co-simulation's sections.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

LSB = 4e-9 / 128                     # the controller's time LSB (4 ns clock, 7 fine bits)


@dataclass(frozen=True)
class Module:
    lf: float = 1.4666667e-9
    co: float = 4.672e-3
    r_load: float = 4e-3
    vin: float = 48.0
    n: int = 4
    i_neg: float = 6.25
    ki_lsb_per_v: float = 8.0         # A79: 0.25 ns per V per sample
    a_s: float = 1.2761 / 533         # V per LSB at 48 V, no load (reference co-simulation, mode S)
    r_s: float = 1.47e-3              # mode S output resistance (A73 run 6)
    ton_full: float = 568.0           # reference full-load steady state: Ton (LSB) at 1.000 V, 250 A
    period_full: float = 232.2e-9

    @property
    def k(self):
        return 250.0 / self.i_p_raw(self.ton_full, 1.0, self.vin / self.n)

    @property
    def t_x(self):
        return self.period_full - self.period_raw(self.ton_full, 1.0, self.vin / self.n)

    def i_p_raw(self, ton, vo, vr):
        return self.n * ((vr - vo) * ton * LSB / (2 * self.lf) - self.i_neg)

    def period_raw(self, ton, vo, vr):
        return ton * LSB * (1.0 + (vr - vo) / max(vo, 0.05))


@dataclass(frozen=True)
class Sequence:
    t_load: float = 88.61e-6
    t_hand: float = 88.61e-6
    t_ramp: float = 68.61e-6
    ton_s: float = 533.0
    vref: float = 1.0
    ton_min_frac: float = 0.5         # the bridge's clamps: 0.5 and 2 x the configured Ton
    ton_max_frac: float = 2.0


def run(m: Module = Module(), sq: Sequence = Sequence(), t_end: float = 300e-6, dt: float = 10e-9):
    """Integrate the averaged model; returns arrays t, vo, ton, mode (0 = S, 1 = P)."""
    k, t_x = m.k, m.t_x
    lo, hi = sq.ton_min_frac * sq.ton_s, sq.ton_max_frac * sq.ton_s
    t, vo, acc, mode, nxt = 0.0, 0.0, float(sq.ton_s), 0, 0.0
    out_t, out_v, out_n, out_m = [], [], [], []
    while t < t_end:
        vin = m.vin * min(t / sq.t_ramp, 1.0)
        vr = vin / m.n
        i_load = vo / m.r_load if t >= sq.t_load else 0.0
        if mode == 0 and t >= sq.t_hand:
            mode, nxt = 1, t
        if mode == 0:
            ton = sq.ton_s
            i = (m.a_s * ton * vin / m.vin - vo) / m.r_s
        else:
            if t >= nxt:
                acc = min(max(acc + m.ki_lsb_per_v * (sq.vref - vo), lo), hi)
                nxt += m.period_raw(round(acc), vo, vr) + t_x
            ton = round(acc)
            i = k * m.i_p_raw(ton, vo, vr)
        vo += dt * (i - i_load) / m.co
        t += dt
        out_t.append(t); out_v.append(vo); out_n.append(ton); out_m.append(mode)
    return np.array(out_t), np.array(out_v), np.array(out_n), np.array(out_m)


def metrics(t, vo, sq: Sequence, vid: float = 1.0, band: float = 0.01):
    """Peak and its time, the minimum after the handover, time above VID in the peak's excursion, the last exit
    from VID +/- band, the final value (last 20 us)."""
    i = int(np.argmax(vo))
    above = vo > vid
    a = i
    while a > 0 and above[a - 1]:
        a -= 1
    b = i
    while b < len(vo) - 1 and above[b + 1]:
        b += 1
    out_band = np.nonzero(np.abs(vo - vid) > band * vid)[0]
    after = t >= sq.t_hand
    return {"vo_max_v": float(vo[i]), "t_vo_max_us": float(t[i] * 1e6),
            "t_above_vid_us": float((t[b] - t[a]) * 1e6) if vo[i] > vid else 0.0,
            "vo_min_after_handover_v": float(vo[after].min()),
            "settle_1pct_us": float(t[out_band[-1]] * 1e6) if len(out_band) else 0.0,
            "vo_final_v": float(vo[t >= t[-1] - 20e-6].mean())}


def validate(sections, m: Module = Module(), sq: Sequence = Sequence(), at_us=(40, 60, 88, 95, 100, 105, 110, 115, 120,
                                                                                125, 130, 140, 150, 160, 170, 180, 190, 200)):
    """The reference sequence against a co-simulation's sections (t_s, vo, ton_lsb)."""
    t, vo, ton, _ = run(m, sq, t_end=max(at_us) * 1e-6 + 1e-6)
    ts = np.array([s["t_s"] for s in sections])
    rows = []
    for a in at_us:
        i = int(np.argmin(np.abs(t - a * 1e-6))); j = int(np.argmin(np.abs(ts - a * 1e-6)))
        rows.append({"t_us": a, "model_vo_v": float(vo[i]), "model_ton_lsb": float(ton[i]),
                     "cosim_vo_v": sections[j]["vo"], "cosim_ton_lsb": sections[j]["ton_lsb"]})
    return rows
