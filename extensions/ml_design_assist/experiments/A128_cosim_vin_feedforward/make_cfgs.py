"""A128 configurations: A124's 2.5 MHz rows (12.5%, the floor, Cs 6 uF, 100 kHz) with the Vin feed-forward (cfg "vff",
scb_vff.v): A127's hybrid - phase 1's cap from Vin (cap_vin: I_CAP 180 A, K = L I_CAP = 844 800 LSB x 20 mV code, a
2^-6 low-pass and a one-step prediction) and the learned falling-step rule (A127 s1's distilled weights, Q16 per code
(+64, -47, -47, -139) on the rectified Vin minus its 2^-2 low-pass). Rows: the seven step rows and n0. Writes
cosim/cfg_*.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A124 = HERE.parents[3] / "experiments" / "track_A_periodic_steady_state" / "A124_p24_two_point_five_mhz" / "cosim"
VFF = {"c": [64, -47, -47, -139], "k": 844800, "sh2": 2, "sh20": 6, "vin_lsb_v": 0.02}
ROWS = ("p125_l_p48_5us", "p125_l_p48_1us", "p125_l_m48_1us", "p125_l_m48_5us", "p125_l_m80_10us", "p125_s_p62",
        "p125_s_m62", "p125_n0")


def main():
    for name in ROWS:
        c = json.loads((A124 / f"cfg_{name}.json").read_text())
        c["vff"] = dict(VFF)
        c["note"] = f"A128 v{name[1:]}: A124's {name} with the Vin feed-forward (A127 hybrid)"
        c["out"] = f"run_v{name[1:]}.json"
        (HERE / "cosim" / f"cfg_v{name[1:]}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(f"v{n[1:]}" for n in ROWS) + "\n")


if __name__ == "__main__":
    main()
