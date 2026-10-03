"""C06 configurations: C05's 18 rows (four modules of A124 2.5 MHz + A129's gated vff) with the slave slot floor
("slave_floor": 1; lo_floor_a 2 A as A118). Writes cosim/cfg_<row>.json and ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C05 = HERE.parent / "C05_four_module_final_design" / "cosim"


def main():
    rows = (C05 / "ORDER.txt").read_text().split()
    for row in rows:
        c = json.loads((C05 / f"cfg_{row}.json").read_text())
        c["slave_floor"] = 1
        c["note"] = f"C06 {row}: C05's {row} with the slave slot floor (slave_floor 1)."
        c["out"] = f"run_{row}.json"
        (HERE / "cosim" / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(rows) + "\n")
    print(len(rows), "configurations")


if __name__ == "__main__":
    main()
