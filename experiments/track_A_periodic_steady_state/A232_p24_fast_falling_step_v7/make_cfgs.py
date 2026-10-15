"""A232 cosim cfgs: -4.8 V / 1 us at 500 us + k T / 6 (A206's step positions; T the board's settled period, N0 0.511 us,
N75 / S75 0.391 us) on plant V7, one module, 25 C, to 620 us, in two arms: d0 = the final configuration before A229
(V7, A222's trims, skipping) and b = the adopted one (A229: + vff rel_gate 25, kd 355 ns/V / dead band 2 / kd_hold /
kd_band_ns 4.0). Rows: N0 and N75 at k 0 / 2 / 4, S75 at k 0.
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
PER_US = {"N0": 0.511, "N75": 0.391, "S75": 0.391}
ROWS = (("N0", 0), ("N0", 2), ("N0", 4), ("N75", 0), ("N75", 2), ("N75", 4), ("S75", 0))


def row(board, k, arm):
    c = M30.adopted(board)
    if arm == "d0":
        c["vff"] = {x: v for x, v in c["vff"].items() if x != "rel_gate"}
        for x in ("kd_ns_per_v", "kd_db", "kd_hold", "kd_band_ns"):
            c.pop(x)
    t = round(500.0 + k * PER_US[board] / 6.0, 4)
    c["line_step"] = {"dv": -4.8, "slew_us": 1.0, "t_us": t}
    c["t_end_us"] = 620.0
    name = f"f_{board}_k{k}_{arm}"
    c["out"] = f"run_{name}.json"
    c["note"] = (f"A232 {name}: {M30.WHAT[board]}, -4.8 V / 1 us at {t} us (k {k} of T/6); plant V7 (r_core {c['circuit']['r_core']} "
                 f"ohm, ton_s_ns {c['ton_s_ns']}), skip; " + ("final configuration before A229" if arm == "d0" else
                 "adopted configuration (rel_gate 25, kd 355 / db 2 / hold / band 4 ns)"))
    return name, c


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [row(b, k, a) for b, k in ROWS for a in ("d0", "b")]
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs")
