"""A175 cosim cfgs: the final gate-level plant (A172 / A173) at nominal devices on the six rows of A152's 13-row
matrix it has not run: -4.8 V / 1 us, L x 1.3 load step, +4.8 V over 2 / 3 / 5 / 10 us. Built as A173 (A164's
gate_cfg on A152's row, then A173's final()); trims: nominal A164's, L x 1.3 A173's re-trim (40.916 ns).
Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a173_make_cfgs", TA / "A173_p24_final_plant_coverage" / "make_cfgs.py")
M3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M3)
COS = HERE / "cosim"
ROWS = ("slew10", "slew5", "slew3", "slew2", "l_m48_1us", "L13_s_p62")


def build(row, ton):
    return M3.final(M3.MC4.gate_cfg(M3.MC4.MC.row_cfg(row), "nom", ton, M3.LEAD))


def main():
    tr = json.loads((M3.A4 / "trims.json").read_text())
    t13 = json.loads((M3.HERE / "trims.json").read_text())["nom_L13"]["ton_ns"]
    a3 = M3.COS
    for row, ton in (("slew4", tr["nom_L0"]["ton_ns"]), ("L13_l_p48_1us", t13)):     # construction = A173's cfgs
        name = "nom_slew4" if row == "slew4" else "nom_L13_l_p48_1us"
        assert M3.strip(build(row, ton)) == M3.strip(json.loads((a3 / f"cfg_{name}.json").read_text())), row
    COS.mkdir(exist_ok=True)
    order = []
    for row in ROWS:
        ton = t13 if row.startswith("L13") else tr["nom_L0"]["ton_ns"]
        name = f"nom_{row}"
        c = dict(build(row, ton), out=f"run_{name}.json",
                 note=f"A175 {name}: A152's row on the final plant, nominal devices, ton {ton} ns")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
