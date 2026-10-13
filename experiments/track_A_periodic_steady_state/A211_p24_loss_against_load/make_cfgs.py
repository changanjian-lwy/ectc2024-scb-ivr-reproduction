"""A211 cosim cfgs: the binding boards at 100 to 40 % of the load, for the loss books against the load. Rows as A210's
(make_cfgs.row: A206's board cfg on plant V6, ton_min_ns 4.0, a release at 300 us, end 450 us), named e_<board>_<temp>_<p>;
p = 100 is the same cfg with a 0 A step.
  python3 make_cfgs.py -> cosim/cfg_e_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a210_cfgs", HERE.parent / "A210_p24_load_range_boards" / "make_cfgs.py")
A10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A10)
COS = HERE / "cosim"
TON_MIN_NS = 4.0
ROWS = (("S75", "25", (100, 75, 60, 50, 40)), ("N75", "25", (100, 75, 60, 50)))

if __name__ == "__main__":
    a194 = A10.A6._a194()
    trims = json.loads(A10.A6.TRIMS.read_text())["dton_s_ns"]
    COS.mkdir(exist_ok=True)
    order = []
    for b, tk, ps in ROWS:
        for p in ps:
            name, c = A10.row(a194, trims, b, tk, p, TON_MIN_NS)
            name = "e" + name[1:]
            c = dict(c, out=f"run_{name}.json", note=c["note"].replace("A210 r_", "A211 e_"))
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs; run-equivalents of 900 us:", round(len(order) * A10.T_END / 900.0, 2))
