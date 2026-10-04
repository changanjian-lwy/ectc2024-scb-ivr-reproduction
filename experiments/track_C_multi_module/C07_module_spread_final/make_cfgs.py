"""C07 configurations: module-to-module component spread (C04's four rows) on the final four-module design (C06's
cfg_n0 / cfg_s_p62: A129 g125 + modules 4 + slave_floor 1), plus two controls with the slave floor off. Module 1 takes
the + spread, module 3 the - spread, modules 0 and 2 nominal. Nominals are the final design's: L 2.9333 nH, Cs 6 uF,
R 0.54 mOhm (A79 init run; A124 scales only controller values). Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "C06_slave_floor" / "cosim"
NOM = {"cs": 6e-6, "R": 0.00054, "L": 2.9333333199999997e-9}
SPREAD = {
    "cs20": {"cs": 0.20},
    "r30": {"R": 0.30},
    "all": {"L": 0.05, "cs": -0.20, "R": 0.30},
}


def module_circuit(spread):
    m1 = {k: NOM[k] * (1 + v) for k, v in spread.items()}
    m3 = {k: NOM[k] * (1 - v) for k, v in spread.items()}
    return [{}, m1, {}, m3]


if __name__ == "__main__":
    runs = {f"{n}_n0": ("n0", s, 1) for n, s in SPREAD.items()}
    runs["all_s_p62"] = ("s_p62", SPREAD["all"], 1)
    runs["r30_n0_nf"] = ("n0", SPREAD["r30"], 0)
    runs["all_n0_nf"] = ("n0", SPREAD["all"], 0)
    for name, (row, spread, floor) in runs.items():
        c = json.loads((BASE / f"cfg_{row}.json").read_text())
        c["module_circuit"] = module_circuit(spread)
        c["slave_floor"] = floor
        c["note"] = (f"C07 {name}: final four-module design, C06 row {row}, slave_floor {floor}; module 1 "
                     + ", ".join(f"{k} {v:+.0%}" for k, v in spread.items()) + ", module 3 the opposite.")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(runs) + "\n")
    print(len(runs), "configurations:", ", ".join(runs))
