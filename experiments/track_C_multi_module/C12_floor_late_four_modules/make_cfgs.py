"""C12 configurations: the four-module final design (C10) with cfg floor_late 1 (A141): C10's 18 rows and C11's four
L x 1.2 / 1.3 rows, everything else verbatim. Writes cosim/cfg_<row>.json (C10 rows) and cosim/cfg_l<kkk>_<row>.json
(C11 rows), ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent
SRC = (TC / "C10_seed_before_entry" / "cosim", TC / "C11_seed2_inductance" / "cosim")


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    order = (SRC[0] / "ORDER_gate.txt").read_text().split() + (SRC[0] / "ORDER_rest.txt").read_text().split() \
        + (SRC[1] / "ORDER.txt").read_text().split()
    for n in order:
        c = json.loads(((SRC[1] if n.startswith("l1") and n[:4] in ("l120", "l130") else SRC[0]) / f"cfg_{n}.json").read_text())
        c["floor_late"] = 1
        c["note"] = f"C12 {n}: " + c["note"].split(": ", 1)[-1] + " + floor_late 1."
        c["out"] = f"run_{n}.json"
        (HERE / "cosim" / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
