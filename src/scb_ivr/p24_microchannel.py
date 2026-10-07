"""D77: a parallel-microchannel cooler under the module's spreader (the team's substrate-embedded channels next to the
GaN layer, Choi et al. 2025), reduced to an effective heat transfer coefficient on the cooled face, a coolant that heats
along the channels, a pressure drop and a pumping power.

Fully developed laminar flow in rectangular channels (Shah and London 1978): Nu for axially uniform heat flux with
peripherally uniform wall temperature (H1, four walls heated) and the Fanning friction factor product f Re, both as
fifth-order polynomials in the aspect ratio a = short / long side. Fins (channel walls) by the straight-fin efficiency
tanh(mH) / (mH) with an adiabatic tip. Effective coefficient on the base (per unit footprint):
h_eff = h_ch (w_c + 2 eta H) / (w_c + w_w). Pressure drop 2 (f Re) mu u L / D_h^2 (no manifold or entrance losses).
"""
from __future__ import annotations

import numpy as np

WATER = {"rho": 992.0, "cp": 4179.0, "k": 0.631, "mu": 6.53e-4}     # ~40 C


def nu_h1(a):
    a = min(a, 1.0 / a) if a > 0 else 0.0
    return 8.235 * (1 - 2.0421 * a + 3.0853 * a ** 2 - 2.4765 * a ** 3 + 1.0578 * a ** 4 - 0.1861 * a ** 5)


def f_re(a):
    a = min(a, 1.0 / a) if a > 0 else 0.0
    return 24.0 * (1 - 1.3553 * a + 1.9467 * a ** 2 - 1.7012 * a ** 3 + 0.9564 * a ** 4 - 0.2537 * a ** 5)


def fin_efficiency(h, k_s, w_w, height):
    m = np.sqrt(2.0 * h / (k_s * w_w))
    return float(np.tanh(m * height) / (m * height))


def cooler(w_c, h_c, w_w, k_s, m_dot, width, length, fluid=WATER):
    """Channels w_c wide, h_c deep, walls w_w (conductivity k_s) across a face width x length, flow m_dot (kg/s) along
    the length. Returns h_ch, h_eff (per footprint), Re, Pr, Graetz x*, dp, pumping power, coolant rise per watt."""
    n = width / (w_c + w_w)
    area = w_c * h_c
    d_h = 2 * area / (w_c + h_c)
    u = m_dot / n / (fluid["rho"] * area)
    re = fluid["rho"] * u * d_h / fluid["mu"]
    pr = fluid["mu"] * fluid["cp"] / fluid["k"]
    h_ch = nu_h1(w_c / h_c) * fluid["k"] / d_h
    eta = fin_efficiency(h_ch, k_s, w_w, h_c)
    h_eff = h_ch * (w_c + 2 * eta * h_c) / (w_c + w_w)
    dp = 2 * f_re(w_c / h_c) * fluid["mu"] * u * length / d_h ** 2
    return {"n_channels": n, "d_h": d_h, "u": u, "re": re, "pr": pr, "x_star": length / (d_h * re * pr),
            "h_ch": h_ch, "fin_eta": eta, "h_eff": h_eff, "dp_pa": dp, "pump_w": dp * m_dot / fluid["rho"],
            "rise_k_per_w": 1.0 / (m_dot * fluid["cp"])}
