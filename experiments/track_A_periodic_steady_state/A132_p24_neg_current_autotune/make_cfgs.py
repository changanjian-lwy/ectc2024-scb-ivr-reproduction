"""A132 configurations: the adopted 2.5 MHz design (A129's g125: A124 with the gated Vin feed-forward) at component
corners - circuit L x k_L, coss_scale k_C with c_high / c_low (the chord's linear part) alike - with the depth loop
("dep") off (the fixed 15.625 A) or on. Rows: A124's seven step rows + n0 (A129 stage 1) and the standard matrix
(A129 stage 2: m1n m1p m3n m3p j30 j100 s_m25 s_p25). Runs: nominal - on, 16 rows (off = A129's records; two identity
reruns of A129 rows with this code -> tmp/identity_a132/); c0.7_l1.3 and c1.3_l0.7 - off on the 8 step rows, on on all
16. c0.7_l1.3 starts with the ladder unbalanced (L +30%: mode S's timing; pilot: rails 16.8 / 10.4 V, ~600 us to
relax), so its steps and ends move 800 us later. Writes cosim/cfg_<arm><corner>_<row>.json and cosim/ORDER.txt. `pilot`: n0 at c0.7_l1.3, off and on, to 500 us ->
tmp/pilot_a132/ (looked at before the boundary)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
A129 = PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim"
STEP_ROWS = ("l_p48_5us", "l_p48_1us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62", "n0")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")
CORNERS = {"nom": (1.0, 1.0), "c07l13": (0.7, 1.3), "c13l07": (1.3, 0.7)}     # (k_C, k_L)
DEP = {"von_set_v": 3.9, "wsh": 5, "smax": 4, "dmin": -24, "dmax": 28, "ehold": 4}
C_DEV = 1860e-12                                                             # Params c_high / c_low per device
LATE_US = {"c07l13": 800.0}                                                  # warm-up added (the L +30% start-up)


def cfg(row, corner, on):
    c = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
    k_c, k_l = CORNERS[corner]
    if corner != "nom":
        c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * k_l, coss_scale=k_c, c_high=2 * C_DEV * k_c, c_low=3 * C_DEV * k_c)
    if on:
        c["dep"] = dict(DEP)
    dt = LATE_US.get(corner, 0.0)
    if dt:
        c["t_end_us"] += dt
        for key in ("load_step", "line_step"):
            if key in c:
                c[key] = dict(c[key], t_us=c[key]["t_us"] + dt)
    name = f"{'t' if on else 'f'}{corner}_{row}"
    c["note"] = f"A132 {name}: A129's g125_{row} at k_C {k_c:g}, k_L {k_l:g}, depth loop {'on' if on else 'off'}"
    c["out"] = f"run_{name}.json"
    return name, c


def write(path: Path, c: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c, indent=1) + "\n")


def main():
    if "pilot" in sys.argv:
        for on in (False, True):
            name, c = cfg("n0", "c07l13", on)
            c["t_end_us"] = 500.0
            write(PROJECT / "tmp" / "pilot_a132" / f"cfg_{name}.json", c)
        return
    order = []
    for corner in CORNERS:
        for on in (False, True):
            if corner == "nom" and not on:
                continue
            for row in STEP_ROWS + (MATRIX_ROWS if on else ()):
                name, c = cfg(row, corner, on)
                write(HERE / "cosim" / f"cfg_{name}.json", c)
                order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    for row in ("l_p48_1us", "n0"):
        c = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
        write(PROJECT / "tmp" / "identity_a132" / f"cfg_g125_{row}.json", c)
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
