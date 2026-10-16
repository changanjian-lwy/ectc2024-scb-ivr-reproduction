"""A235: the final configuration (A229 + A231) on plant V7 for any board and temperature: A194's board (V5 final),
A206's v6 (low sides 0.3 ohm x the board's drive corner, switches at the datasheet maximum x the temperature factor,
zvs_edge, miller, circuit R 0), then V7 and the controller since: r_core = (2 pi 8 MHz)^2 L / 2.557e6 (A221), ton_lat 16
(A215), ton_min_ns 4.0 (A208), skipping on non-slow boards (A221), vff rel_gate 25 + kd 355 / db 2 / hold / band 4 ns
(A229), hand_lead_us 0.7 on non-slow boards (A231). ton_s_ns = A194's (V5) + dton ns."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

TA = Path(__file__).resolve().parent.parent


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A194 = _load("a194_cfgs", "A194_p24_final_plant_random_stimuli/make_cfgs.py")
A206 = _load("a206_cfgs", "A206_p24_low_side_zvs_turn_on/make_cfgs.py")
LSB_NS = 0.03125


def r_core(l_h):
    return round((2 * math.pi * 8e6) ** 2 * l_h / 2.557e6, 4)


def final(b, tk, dton):
    c = A194.board(b, tk)
    r_b = round(0.3 * c["gate"]["r_on"] / 3.0, 4)
    c = A206.v6(c, r_b, A206.R_MAX * A206.R_TEMP[A194.TEMPS[tk]])
    slow = A194.BOARDS[b] == "slow"
    c["circuit"] = dict(c["circuit"], r_core=r_core(c["circuit"]["L"]))
    c["ton_s_ns"] = round(c["ton_s_ns"] + dton, 5)
    c.update(ton_lat=16, ton_min_ns=4.0, kd_ns_per_v=355.0, kd_db=2, kd_hold=1, kd_band_ns=4.0)
    c["vff"] = dict(c["vff"], rel_gate=25)
    vo_l = 1.0 / c["circuit"]["L"] * 8e-9                          # A217 / A221: 8 ns x Vo / L
    if not slow:
        c["skip"] = {"hi_mv": 5.0, "lo_mv": 1.0, "res_ofs_a": round(vo_l, 3), "zcd_a": round(vo_l, 3)}
        c["hand_lead_us"] = 0.7
    return c
