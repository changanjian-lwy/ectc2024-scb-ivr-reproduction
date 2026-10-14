"""A221 cosim cfgs. Plant V7 = V6 + a core-loss resistor across each inductor (cfg circuit "r_core"), calibrated on
D76's HBS1 data at its highest measured frequency: R_acx(8 MHz) = 2.557 mOhm/nH, and the parallel model's
R_ac(f) = (2 pi f L)^2 / r_core, so r_core = (2 pi 8 MHz)^2 L / R_acx (2.90 ohm at L0, 2.17 ohm at 0.75 L0).
- z / u rows: A220's skipping rows (zero-current pause, A217's offset) with A221's period fix and V7; the N0 rows run
  to 750 us (N0's ladder, unbalanced by the release, settles with about 100 us), the edge log covers the last 20 us;
- rc2 rows: the same with twice r_core (half the damping; about D76's f^1.5 extrapolation at the ring's 20-25 MHz);
- k rows: A215's ton_lat 16 rows +62.5 A on N0 and the binding row S75 125 C k 5 on V7 (references: A215's records).
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
R_ACX_8MHZ = 2.557e6                                  # ohm / H (2.557 mOhm/nH), D76 Section 2
T_END_N0 = 750.0


def r_core(c, k=1.0):
    return round(k * (2 * math.pi * 8e6) ** 2 * c["circuit"]["L"] / R_ACX_8MHZ, 4)


def skip_row(name, k=1.0, tag=""):
    c = json.loads((TA / "A220_p24_zero_current_pause" / "cosim" / f"cfg_{name}.json").read_text())
    c["circuit"] = dict(c["circuit"], r_core=r_core(c, k))
    if "_N0_" in name and not name.startswith("u_"):
        c["t_end_us"] = T_END_N0
        c["debug_edges_us"] = [T_END_N0 - 20.0, T_END_N0 - 0.1]
    c["out"] = f"run_{name}{tag}.json"
    c["note"] = c["note"].replace("A220", "A221", 1) + f"; plant V7, r_core {c['circuit']['r_core']} ohm; the pause keeps the slots' period"
    return f"{name}{tag}", c


def check_row(src, name):
    c = json.loads((TA / "A215_p24_buildable_ton_path" / "cosim" / f"cfg_{src}.json").read_text())
    c["circuit"] = dict(c["circuit"], r_core=r_core(c))
    c["out"] = f"run_{name}.json"
    c["note"] = "A221 " + name + ": " + c.get("note", "").split(": ", 1)[-1] + f"; plant V7, r_core {c['circuit']['r_core']} ohm"
    return name, c


ROWS = [skip_row("z_N0_25_10"), skip_row("z_N75_25_10"), skip_row("z_N0_25_0"), skip_row("u_N0_25_5_s62"),
        skip_row("z_N0_25_10", 2.0, "_rc2"), skip_row("z_N75_25_10", 2.0, "_rc2"),
        check_row("m16_n_s_p62", "k_n_s_p62"), check_row("m16_B_S75_hot_p5_ls0p3", "k_B_S75_hot_p5_ls0p3")]

if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    order = ["k_B_S75_hot_p5_ls0p3", "z_N0_25_10", "z_N0_25_0", "z_N0_25_10_rc2", "k_n_s_p62", "z_N75_25_10",
             "z_N75_25_10_rc2", "u_N0_25_5_s62"]                     # longest first
    for name, c in ROWS:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    assert sorted(order) == sorted(n for n, _ in ROWS)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(ROWS), "cfgs:", {n: (c["circuit"]["r_core"], c["t_end_us"]) for n, c in ROWS})
