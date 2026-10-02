"""C03 configurations: the standard matrix (scb_ivr.cosim.matrix.ROWS, 16 rows) on four modules with the uniform
interleave (C02's m4_n0: A105's I2 and slot_lo), plus two rows with one slave's inductors larger. A load step's i_a
is the system's, so the matrix's per-module steps are multiplied by the module count. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from scb_ivr.cosim.matrix import configs  # noqa: E402

BASE = HERE.parent / "C02_uniform_interleave" / "cosim" / "cfg_m4_n0.json"
L_NOM = 1.4666667e-09
SLAVE_L = {"ls_p5": 1.05, "ls_p10": 1.10}       # slave 1's inductors x this, the others nominal

if __name__ == "__main__":
    base = json.loads(BASE.read_text())
    m = int(base["modules"])
    rows = configs(base)
    for name, ratio in SLAVE_L.items():
        c = dict(rows["n0"])
        c["module_circuit"] = [{}, {"L": L_NOM * ratio}, {}, {}]
        rows[name] = c
    for name, c in rows.items():
        if "load_step" in c:
            c["load_step"] = dict(c["load_step"], i_a=c["load_step"]["i_a"] * m)
        c["note"] = (f"C03 {name}: four modules (A105's I2 with slot_lo, C02), standard-matrix row {name}"
                     + (f" (system load step {c['load_step']['i_a']:+.1f} A)" if "load_step" in c else "")
                     + (f" (slave 1's L x {SLAVE_L[name]})" if name in SLAVE_L else "") + ".")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(rows), "configurations:", ", ".join(rows))
