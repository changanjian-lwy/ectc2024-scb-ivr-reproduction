"""A123 configurations: the 1 MHz candidate's last misses (A118/A119: +-4.8 V over 1 us at 206 / 201 A, -8 V over
10 us at 205 A), screened against three single changes from A118's f6 (floor 2 A, Cs 6 uF, 60 kHz):
- c45: Cs 4.5 uF (a faster ladder; between A117's 3 uF handover failure and 6 uF);
- f3: the floor at 3 A;
- k66: the loop at 66 kHz (D59 gains x1.1 / x1.21; ki register 60 800 < 65 535).
Rows: n0 (the handover) and the three failing steps. Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A118 = HERE.parent / "A118_p24_floor_turn_off" / "cosim"
VARIANTS = {"c45": {"cs": 4.5e-6}, "f3": {"lo_floor_a": 3.0}, "k66": {"fc": 66.0}}
ROWS = {"l_p48_1us": "f6_l_p48_1us", "l_m48_1us": "f6_l_m48_1us", "l_m80_10us": None, "n0": "f6_n0"}

if __name__ == "__main__":
    names = []
    for row, src in ROWS.items():
        for v, ch in VARIANTS.items():
            c = json.loads((A118 / f"cfg_{src or 'f6_n0'}.json").read_text())
            if src is None:
                c["line_step"] = {"t_us": 2000.0, "dv": -8.0, "slew_us": 10.0}; c["t_end_us"] = 3000.0
            if "cs" in ch:
                c["circuit"] = dict(c["circuit"], cs=ch["cs"])
            if "lo_floor_a" in ch:
                c["lo_floor_a"] = ch["lo_floor_a"]
            if "fc" in ch:
                k = ch["fc"] / 60.0
                c["kp_ns_per_v"] = round(574.46 * k, 3); c["ki_ns_per_v"] = round(47.9264 * k * k, 4)
            c["note"] = f"A123 {v}_{row}: A118's f6 with {ch}, {row}."
            c["out"] = f"run_{v}_{row}.json"
            (HERE / "cosim" / f"cfg_{v}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
            names.append(f"{v}_{row}")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(names) + "\n")
    print(len(names), "configurations")
