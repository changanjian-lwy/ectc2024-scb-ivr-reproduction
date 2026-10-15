"""A231 cosim cfgs: A230's lead (hand_lead_us 0.7) on nominal boards only, checked on rows A230 did not run: N0 and N75
at 125 C into 30 % (to 300 us) and into full load (to 200 us; the request fires hot, A188), and N0 / N75 at 25 C into
20 % (information, to 300 us). Arms base / lead. Hot = gate temp 125 C and r_sw_mohm x 1.5809 (A222's S75 hot cfg
against its 25 C cfg). Adopted configuration of A229, plant V7, one module (a230 make_cfgs.adopted).
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a230_make_cfgs", TA / "A230_p24_handover_slope_lead" / "make_cfgs.py")
M30 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M30)
R_HOT = 1.225197 / 0.775                                   # A222: S75 hot / 25 C r_sw_mohm
ROWS = (("N0", "h", 30), ("N75", "h", 30), ("N0", "h", 100), ("N75", "h", 100), ("N0", "", 20), ("N75", "", 20))


def row(board, hot, share, arm):
    name, c = M30.row(board, share, arm)
    tag = f"{board}{hot}_{share}_{arm}"
    if hot:
        c["gate"] = dict(c["gate"], temp=125.0)
        c["r_sw_mohm"] = [round(x * R_HOT, 6) for x in c["r_sw_mohm"]]
    c["out"] = f"run_u_{tag}.json"
    c["note"] = c["note"].replace(f"A230 {name}", f"A231 u_{tag}", 1).replace(" at 25 C,", " at 125 C," if hot else " at 25 C,", 1)
    return f"u_{tag}", c


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [row(b, h, s, a) for b, h, s in ROWS for a in ("base", "lead")]
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs")
