"""D65: package parasitics of P24's Fig. 5 layout from first principles - copper and via resistance with the
converter's own current waveforms, and the commutation-loop energy bound on the switch voltage.

Geometry follows paper_locked/02_ectc2024_main/P24_FIG5_FIG6_PACKAGE_TRANSCRIPTION.md (10 mm module, four 2.5 mm
phase columns L1 inner .. L4 outer, central Vo / GND / Vin strip, switch-node vias through glass 1); every dimension
P24 does not print is a scenario argument. Copper resistivity 17 nOhm m (the VPD framework's Table III).

SCB currents (N phases, phase k's high side SHk joins a(k-1) to a(k)): during phase k's Ton its current flows through
Cs(k-1) and Cs(k), returns through QL(k-1) (Cin for k = 1); QLk carries its own phase off its Ton plus phase k+1's
current during Ton(k+1). The resonant interval (low-off to turn-on) is carried by the Coss and assigned to no channel.
"""
from __future__ import annotations

import numpy as np

RHO_CU = 17e-9           # Ohm m
VIA_FIELD = 16 / np.pi   # R x area / (rho h) of a via array at pitch 2 d (fill pi / 16), independent of d


def phase_waveforms(T, ton, ipk, ilo, i_on, t_res, n=4, pts=4096):
    """Piecewise-linear periodic phase currents: i_on -> ipk over ton (high side), ipk -> ilo until T - t_res (low
    side), ilo -> i_on over t_res (resonant). Phase k delayed by k T / n. Returns t, i[n], hs[n], ls_own[n] (masks)."""
    t = np.arange(pts) * T / pts
    i, hs, lo = [], [], []
    for k in range(n):
        u = (t - k * T / n) % T
        x = np.interp(u, [0.0, ton, T - t_res, T], [i_on, ipk, ilo, i_on])
        i.append(x); hs.append(u < ton); lo.append((u >= ton) & (u < T - t_res))
    return t, np.array(i), np.array(hs), np.array(lo)


def branch_currents(i, hs, lo):
    """SCB branch currents from the phase waveforms: high sides, low sides (own phase + next phase's Ton), series
    capacitors Cs_k (phases k and k+1 during their Ton), input (phase 1's Ton)."""
    n = len(i)
    i_hs = i * hs
    i_ls = i * lo
    i_ls[:-1] += i_hs[1:]                       # QLk returns phase k+1's current through Cs_k's bottom node
    i_cs = np.array([i_hs[k] + i_hs[k + 1] for k in range(n - 1)])
    return {"hs": i_hs, "ls": i_ls, "cs": i_cs, "in": i_hs[0]}


def rms(x, axis=-1):
    return np.sqrt(np.mean(np.square(x), axis=axis))


def lateral_segments(i_phase):
    """Currents in the lateral segments between phase columns and the central strip: segment j (0 = inner, next to the
    strip) carries the sum of phases j..N-1 (the outer ones flow inward)."""
    return np.array([i_phase[j:].sum(axis=0) for j in range(len(i_phase))])


def lateral_loss(i_phase, t_cu, col_w=2.5e-3, depth=10e-3):
    """Copper loss of one lateral layer stack (total thickness t_cu, m) from the columns to the strip: each segment is
    col_w long and depth wide (Fig. 5: 2.5 mm columns, 10 mm module). DC resistance (thickness below a few skin depths at
    the switching harmonics is not credited separately; the ripple share is reported with it)."""
    seg = lateral_segments(i_phase)
    r_seg = RHO_CU * col_w / (t_cu * depth)
    return float(np.sum(rms(seg) ** 2) * r_seg), seg


def via_field_r(h, area):
    """Resistance of a copper via array of height h (m) over a footprint area (m^2) at pitch 2 d."""
    return VIA_FIELD * RHO_CU * h / area


def overshoot(l_loop, i_off, v_rail, coss, n_dev, dv=1e-3, v_top=80.0):
    """Energy bound on the switch voltage at an instantaneous turn-off of i_off through a loop inductance l_loop: the
    loop energy 0.5 L I^2 goes into the turning-off switch's n_dev Coss above the rail. Returns the peak V_DS."""
    v = np.arange(v_rail, v_top, dv)
    e = n_dev * np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] * coss.c(v[1:]) + v[:-1] * coss.c(v[:-1])) * dv)])
    need = 0.5 * l_loop * i_off ** 2
    return float(np.interp(need, e, v)) if need <= e[-1] else float("inf")
