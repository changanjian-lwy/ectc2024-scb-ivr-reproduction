"""A133 configurations: the adopted 2.5 MHz design (A129's g125: A124 with the gated Vin feed-forward) with the phase
inductance L x k_L, and phases 2-4's floors (cfg "ph_floor" 1, arm p) or not (arm f). Corners (k_C, k_L): nom, l07, l12,
l13 (C nominal) and c07l13 (A132's corner: coss_scale 0.7 with c_high / c_low). Rows: A124's seven step rows + n0 and
A129's standard matrix. Runs: p at nom / l07 / l12 / l13 on all 16 rows, f at l07 / l12 / l13 on the 8 step rows (nom f =
A129's g125 records), p at c07l13 on the 8 step rows. Writes cosim/cfg_<arm><corner>_<row>.json and cosim/ORDER.txt;
two off reruns of A129 rows -> tmp/identity_a133/. `pilot` (looked at before the boundary) -> tmp/pilot_a133/: n0 at
k_L 1.1 / 1.2 / 1.3 (1.3 to 2000 us), and k_L 1.3 with ton_ns x 1.3 (Ton at the handover near its L x 1.3 value; ton_ns
also sets mode S's Ton and the loop clamp 0.5-2 x ton_ns)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
A129 = PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim"
STEP_ROWS = ("l_p48_5us", "l_p48_1us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62", "n0")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")
CORNERS = {"nom": (1.0, 1.0), "l07": (1.0, 0.7), "l12": (1.0, 1.2), "l13": (1.0, 1.3), "c07l13": (0.7, 1.3)}
C_DEV = 1860e-12                                                             # Params c_high / c_low per device
PLAN = [("p", c, STEP_ROWS + MATRIX_ROWS) for c in ("nom", "l07", "l12", "l13")] + \
       [("f", c, STEP_ROWS) for c in ("l07", "l12", "l13")] + [("p", "c07l13", STEP_ROWS)]


def corner_cfg(row, corner, arm):
    c = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
    k_c, k_l = CORNERS[corner]
    if corner != "nom":
        c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * k_l)
    if k_c != 1.0:
        c["circuit"].update(coss_scale=k_c, c_high=2 * C_DEV * k_c, c_low=3 * C_DEV * k_c)
    if arm == "p":
        c["ph_floor"] = 1
    name = f"{arm}{corner}_{row}"
    c["note"] = f"A133 {name}: A129's g125_{row} at k_C {k_c:g}, k_L {k_l:g}, phase floors {'on' if arm == 'p' else 'off'}"
    c["out"] = f"run_{name}.json"
    return name, c


def cfg(row, k_l, tag="f", ton_scale=1.0, t_end_us=None):
    c = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
    c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * k_l)
    c["ton_ns"] = c["ton_ns"] * ton_scale
    if t_end_us:
        c["t_end_us"] = t_end_us
    name = f"{tag}l{round(k_l * 100):03d}_{row}"
    c["note"] = f"A133 {name}: A129's g125_{row} at k_L {k_l:g}" + (f", ton_ns x {ton_scale:g}" if ton_scale != 1.0 else "")
    c["out"] = f"run_{name}.json"
    return name, c


def write(path: Path, c: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c, indent=1) + "\n")


def main():
    if "pilot" in sys.argv:
        runs = [cfg("n0", 1.1), cfg("n0", 1.2), cfg("n0", 1.3, t_end_us=2000.0), cfg("n0", 1.3, "s", ton_scale=1.3)]
        for name, c in runs:
            write(PROJECT / "tmp" / "pilot_a133" / f"cfg_{name}.json", c)
        print(len(runs), "pilot cfgs")
        return
    order = []
    for arm, corner, rows in PLAN:
        for row in rows:
            name, c = corner_cfg(row, corner, arm)
            write(HERE / "cosim" / f"cfg_{name}.json", c)
            order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    for row in ("l_p48_1us", "n0"):
        write(PROJECT / "tmp" / "identity_a133" / f"cfg_g125_{row}.json", json.loads((A129 / f"cfg_g125_{row}.json").read_text()))
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
