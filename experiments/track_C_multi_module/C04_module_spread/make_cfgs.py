"""C04 configurations: module-to-module component spread on four modules (C03's design: A105's I2 with slot_lo), one
spread per run, then all together. Module 0 is the master; modules 1 and 3 take the spread in opposite directions
(module 2 nominal, as module 0). Nominal values are A79's init run (cs 3 uF, R 0.54 mOhm, L 1.4667 nH). Coss is not
spread: with nonlinear_coss the plant replaces the linear c_high / c_low by the datasheet curve, so they have no
effect (BOUNDARY Section 2). Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "C03_four_module_standard_matrix" / "cosim"
NOM = {"cs": 3e-6, "R": 0.00054, "L": 1.4666667e-9}
SPREAD = {   # name: {key: relative change of module 1; module 3 gets the opposite}
    "cs20": {"cs": 0.20},
    "r30": {"R": 0.30},
    "all": {"L": 0.05, "cs": -0.20, "R": 0.30},
}


def module_circuit(spread):
    m1 = {k: NOM[k] * (1 + v) for k, v in spread.items()}
    m3 = {k: NOM[k] * (1 - v) for k, v in spread.items()}
    return [{}, m1, {}, m3]


if __name__ == "__main__":
    runs = {f"{n}_n0": ("n0", s) for n, s in SPREAD.items()}
    runs["all_s_p62"] = ("s_p62", SPREAD["all"])
    for name, (row, spread) in runs.items():
        c = json.loads((BASE / f"cfg_{row}.json").read_text())
        c["module_circuit"] = module_circuit(spread)
        c["note"] = (f"C04 {name}: four modules (A105's I2 with slot_lo), C03 row {row}; module 1 "
                     + ", ".join(f"{k} {v:+.0%}" for k, v in spread.items()) + ", module 3 the opposite.")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(runs), "configurations:", ", ".join(runs))
