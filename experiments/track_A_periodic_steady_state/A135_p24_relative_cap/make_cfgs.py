"""A135 configurations: the adopted 2.5 MHz design (A129's g125) with the relative phase-1 cap (cfg vff.rel_q8 333,
scb_vff A135; k stays and is unused) at L x m, m 0.7 / 0.85 / 1.0 / 1.15 / 1.3, on A124's seven step rows + n0 and
A129's matrix (8), plus x_l_p80_10us (+8 V / 10 us, A130's slope limit; from g125_l_p48_5us) at m 0.7 / 1.0 / 1.3 for
r; and f (the adopted cap) at m 1.0 on the seven step rows + x_l_p80_10us, the reference at this timing. Every step
moves to 1000 us (end 1400 us; m / j rows end 1200 us): phase 1 learns for lo_learn 1024 periods after the handover
and goes timed at 812-818 us at L x 1.3 (A134), so A129's 800 us step would land in its comparator phase. Writes
cosim/cfg_<arm><mmm>_<row>.json, ORDER.txt; two rel-off reruns of A129 rows -> tmp/identity_a135/."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
A129 = PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim"
STEP_ROWS = ("l_p48_5us", "l_p48_1us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62", "n0")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")
MS = (0.7, 0.85, 1.0, 1.15, 1.3)
REL = 333
T_STEP_US = 1000.0


def cfg(arm, m, row):
    src = "l_p48_5us" if row == "x_l_p80_10us" else row
    c = json.loads((A129 / f"cfg_g125_{src}.json").read_text())
    if row == "x_l_p80_10us":
        c["line_step"] = {"t_us": 800.0, "dv": 8.0, "slew_us": 10.0}
    for key in ("line_step", "load_step"):
        if c.get(key):
            c[key] = dict(c[key], t_us=T_STEP_US)
    c["t_end_us"] = T_STEP_US + 400.0 if (c.get("line_step") or c.get("load_step") or row == "n0") else 1200.0
    if m != 1.0:
        c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * m)
    if arm == "r":
        c["vff"] = dict(c["vff"], rel_q8=REL)
    name = f"{arm}{round(m * 100):03d}_{row}"
    c["note"] = f"A135 {name}: A129's g125_{src} at k_L {m:g}" + (", +8 V / 10 us" if row.startswith("x_") else "") + \
        (f", relative cap rel_q8 {REL}" if arm == "r" else ", the adopted cap")
    c["out"] = f"run_{name}.json"
    return name, c


def main():
    order = []
    plan = [("r", m, row) for m in MS for row in STEP_ROWS + MATRIX_ROWS] + \
           [("r", m, "x_l_p80_10us") for m in (0.7, 1.0, 1.3)] + [("f", 1.0, row) for row in STEP_ROWS[:-1] + ("x_l_p80_10us",)]
    for arm, m, row in plan:
        name, c = cfg(arm, m, row)
        (HERE / "cosim").mkdir(exist_ok=True)
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    ident = PROJECT / "tmp" / "identity_a135"
    ident.mkdir(parents=True, exist_ok=True)
    for row in ("l_p48_1us", "n0"):
        (ident / f"cfg_g125_{row}.json").write_text((A129 / f"cfg_g125_{row}.json").read_text())
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
