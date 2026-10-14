"""A217 cosim cfgs: A216's skipping rows with the resume offset (cfg skip "res_ofs_a"): phase 1's front end ends a
resume's low-side interval that much above the target, the latency of its edges (8 ns, read from A216's resumes on
nominal devices) times the current's slope Vo / L of the board.
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a216_cfgs", TA / "A216_p24_skipped_rounds" / "make_cfgs.py")
A16 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A16)
COS = HERE / "cosim"
LAT_NS = 8.0
ROWS = ("z_N0_25_10", "z_N0_25_0", "z_N75_25_10", "z_S75_25_10", "z_S75_hot_10", "u_N0_25_5_s62")


def ofs(c):
    return round(LAT_NS * 1e-9 * c["vref_v"] / c["circuit"]["L"], 3)


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for name in ROWS:
        c = json.loads((TA / "A216_p24_skipped_rounds" / "cosim" / f"cfg_{name}.json").read_text())
        c = dict(c, skip=dict(c["skip"], res_ofs_a=ofs(c)), out=f"run_{name}.json")
        c["note"] = c["note"].replace("A216", "A217", 1) + f"; resume offset {ofs(c)} A ({LAT_NS:g} ns x Vo / L)"
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(ROWS) + "\n")
    print(len(ROWS), "cfgs:", {n: json.loads((COS / f"cfg_{n}.json").read_text())["skip"]["res_ofs_a"] for n in ROWS})
