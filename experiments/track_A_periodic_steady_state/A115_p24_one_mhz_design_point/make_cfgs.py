"""A115 configurations: the adopted single module (C02 cosim/cfg_s1_n0.json: A105's I2 with slot_lo) moved from P24's
5 MHz column to its 1 MHz column (Table I, 4 phases x 4 modules), with Eq. (4)'s inductance there, 7.333 nH.

The design point is the one factor; what follows from it (BOUNDARY Section 2):
- circuit: L x5 (Eq. (4) is proportional to 1 / f); Cs x5 (3 -> 15 uF: the same capacitor ripple, Q / Cs, as at 5 MHz);
- times set by the period, x5: mode S's Ton and T0, phase 1's low-side restart (rs_low), the input ramp (D60's
  margin over Roberts' first resonance, proportional to the ramp / sqrt(L Cs)), the handover, the run, the load
  step's time, and the timed turn-off's largest step lo_smax (its interval is x5);
- times set by the node's resonance sqrt(L C_node), x sqrt(5): the predictive delay's start, step and cap, and the
  high-side restart (rs_high);
- the voltage loop: D59 at the 1 MHz point, fc 60 kHz (a115_predictions.json);
- unchanged: the devices, R, Co, the load, the low-side (current-driven) transition timing dtl, the dead time, the
  driver, the comparators, the error targets, lo_learn (a count).
Rows: the negative-current target at 5, 7.5, 10 and 12.5% of the 125 A peak; at 5% and 10% also the +-62.5 A load steps;
at 10% 30 ps jitter. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
C02 = HERE.parents[1] / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
PEAK = 125.0
K_T, K_R = 5.0, math.sqrt(5.0)                  # period and node-resonance scale factors, 5 MHz -> 1 MHz
L1, CS1 = 7.3333333e-9, 15e-6
T_RAMP_5MHZ_US = 68.61                          # the init run's input ramp (A79 r1 params)
ROWS = {f"n{p:g}".replace(".", "p"): (p, "s1_n0") for p in (5.0, 7.5, 10.0, 12.5)}
ROWS.update({"n5_s_p62": (5.0, "s1_s_p62"), "n5_s_m62": (5.0, "s1_s_m62"),
             "n10_s_p62": (10.0, "s1_s_p62"), "n10_s_m62": (10.0, "s1_s_m62"), "n10_j30": (10.0, "s1_j30")})


def one_mhz(c, pct, loop):
    c = dict(c)
    c["circuit"] = {"L": L1, "cs": CS1}
    for k in ("ton_ns", "t0_ns", "rs_low_ns", "t_hand_us", "t_end_us"):
        c[k] = round(c[k] * K_T, 6)
    c["t_ramp_us"] = round(T_RAMP_5MHZ_US * K_T, 6)
    for k in ("dt_init_ns", "dt_step_ns", "dt_max_ns", "rs_high_ns"):
        c[k] = round(c[k] * K_R, 6)
    c["lo_smax"] = int(c["lo_smax"] * K_T)
    if c.get("load_step"):
        c["load_step"] = dict(c["load_step"], t_us=round(c["load_step"]["t_us"] * K_T, 6))
    c["kp_ns_per_v"] = round(loop["kp_ns_per_v"], 3)
    c["ki_ns_per_v"] = round(loop["ki_ns_per_v"], 4)
    c["i_target"] = -pct / 100 * PEAK
    return c


if __name__ == "__main__":
    loop = json.loads((HERE / "a115_predictions.json").read_text())["loop_1MHz_n5"]
    for name, (pct, src) in ROWS.items():
        c = one_mhz(json.loads((C02 / f"cfg_{src}.json").read_text()), pct, loop)
        c["note"] = (f"A115 {name}: C02's {src} at P24's 1 MHz point (L {L1 * 1e9:.3f} nH, Cs {CS1 * 1e6:.0f} uF, period times x5, "
                     f"node times x sqrt 5, D59 fc 60 kHz), negative-current target {pct:g}% ({c['i_target']:.3f} A).")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(ROWS), "configurations:", ", ".join(ROWS))
