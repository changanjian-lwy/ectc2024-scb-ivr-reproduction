"""C05 configurations: the final single-module design (A124 2.5 MHz with A129's gated Vin feed-forward) on four modules.
Each row is A129's single-module g125_<row> configuration with "modules": 4 (a load step's i_a is the system's, so the
per-module step x 4) plus two rows with slave 1's inductor larger. Rows: n0, driver m1n m1p m3n m3p j30 j100, load
s_m25 s_p25 s_m62 s_p62, line l_*. Writes cosim/cfg_<row>.json and ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A129 = HERE.parents[2] / "extensions" / "ml_design_assist" / "experiments" / "A129_cosim_vff_slope_gate" / "cosim"
ROWS = ("n0", "m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25", "s_m62", "s_p62",
        "l_p48_1us", "l_p48_5us", "l_m48_1us", "l_m48_5us", "l_m80_10us")
L_NOM = 2.9333333199999997e-09
SLAVE_L = {"ls_p5": 1.05, "ls_p10": 1.10}
M = 4


def main():
    out = {}
    for row in ROWS:
        out[row] = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
    for name, ratio in SLAVE_L.items():
        c = json.loads(json.dumps(out["n0"]))
        c["module_circuit"] = [{}, {"L": L_NOM * ratio}, {}, {}]
        out[name] = c
    for name, c in out.items():
        c["modules"] = M
        if "load_step" in c:
            c["load_step"]["i_a"] *= M
        c["note"] = (f"C05 {name}: four modules of A129's g125_{name if name in ROWS else 'n0'} (A124 2.5 MHz + gated vff)"
                     + (f", system load step {c['load_step']['i_a']:+.1f} A" if "load_step" in c else "")
                     + (f", slave 1's L x {SLAVE_L[name]}" if name in SLAVE_L else "") + ".")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(out) + "\n")
    print(len(out), "configurations")


if __name__ == "__main__":
    main()
