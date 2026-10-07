"""D76: core loss of an HBS1-class metal-polymer composite (MPC) inductor array from the R_acx metric.

R_acx = R_AC / L (mOhm/nH) at frequency f and duty cycle D (triangular ripple, rise over D T) is a material property
below ~5 MHz (Murali et al., ECTC 2022, Fig. 8; Alvarez Barros et al., TCPMT 2021, P24's ref. [10] for HBS1). The AC
loss of an inductance L carrying a ripple of rms I_ac is kappa R_acx L I_ac^2, where kappa >= 1 converts the small-signal
metric to large signal ("over four times" in the MHz range, Alvarez Barros et al. 2021). For an array of N parallel
units of N L each carrying I / N the loss is the same, so the core loss of a phase does not depend on the unit count.

RACX_HBS1: the HBS1 (black) curves of Murali et al. Fig. 8(e) (discrete toroid, small signal), digitised from the page
rendered at 500 dpi with the axes calibrated on the gridlines (0-6 mOhm/nH, 119.7 px per unit; D 0-1, 1300 px per unit);
reading error ~0.02 mOhm/nH. Between 2 and 8 MHz the metric follows f^1.53-1.56 at D 0.03-0.1.
"""
from __future__ import annotations

import numpy as np

RACX_D = np.array([0.03, 0.05, 0.06, 0.077, 0.09, 0.10])
RACX_HBS1 = {                                  # mOhm / nH, small signal, at RACX_D
    2e6: np.array([0.497, 0.389, 0.347, 0.301, 0.272, 0.259]),
    4e6: np.array([1.429, 1.116, 1.015, 0.886, 0.819, 0.773]),
    8e6: np.array([3.518, 3.113, 2.891, 2.557, 2.352, 2.231]),
}


def racx(f, d):
    """Small-signal R_acx (Ohm / H) of HBS1 at frequency f (Hz) and duty d: linear in d inside the digitised range
    (clipped to it), power law in f through the neighbouring curves (below 2 MHz the 2-4 MHz exponent: extrapolated)."""
    d = float(np.clip(d, RACX_D[0], RACX_D[-1]))
    fs = sorted(RACX_HBS1)
    v = {fk: float(np.interp(d, RACX_D, RACX_HBS1[fk])) for fk in fs}
    lo, hi = (fs[0], fs[1]) if f <= fs[1] else (fs[1], fs[2])
    alpha = np.log(v[hi] / v[lo]) / np.log(hi / lo)
    return v[lo] * (f / lo) ** alpha * 1e6          # mOhm / nH = 1e6 Ohm / H


def exponent(d, f_lo=2e6, f_hi=8e6):
    return float(np.log(racx(f_hi, d) / racx(f_lo, d)) / np.log(f_hi / f_lo))


def phase_core_loss(valley, peak, ton, period, l_phase, kappa=1.0):
    """Core loss (W) of one phase: triangular ripple valley -> peak over ton, back over the rest of the period."""
    i_ac2 = (peak - valley) ** 2 / 12.0
    return kappa * racx(1.0 / period, ton / period) * l_phase * i_ac2


def module_core_loss(m, l_phase, kappa=1.0):
    """Sum over the phases of a p24_loss_budget.measure() record."""
    return sum(phase_core_loss(p["valley"], p["peak"], m["ton_s"], m["period_s"], l_phase, kappa) for p in m["phases"])
