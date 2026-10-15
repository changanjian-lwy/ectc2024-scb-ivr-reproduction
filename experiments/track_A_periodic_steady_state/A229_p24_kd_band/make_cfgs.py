"""A229 cosim cfgs: arm b = A228's arm h (vff rel_gate 25, kd 355 ns/V, dead band 2, kd_hold 1) + kd_band_ns 4.0 (no
derivative term while the PI output is at most 4 ns above the lower Ton limit; A229), plant V7, A222's trims, one
module, 25 C unless named.
- part S: A228's skipping rows (N0 10 %, N75 10 %, N0 no load) at its four release instants t0-t3 (d0: A228's records);
- part W: the re-applications from light load (w0_N0, w5_N0, w20_N0, w5_N75, u_N0, w30_S75h);
- part I: k_N0 and k_S75h, where the band never acts (Ton register >= 28.0 ns in A228's arm h): bit for bit arm h.
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a228_make_cfgs", TA / "A228_p24_damped_loop_adoption" / "make_cfgs.py")
M28 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M28)
M27, M24, M23 = M28.M27, M28.M24, M28.M23
BAND_NS = 4.0
T_REL = {"t0": 300.0, **M28.T_REL}
W_ROWS = ("w0_N0", "w5_N0", "w20_N0", "w5_N75", "u_N0", "w30_S75h")
I_ROWS = ("k_N0", "k_S75h")


def banded(c, what, name):
    n, x = M27.held(c, what, name)
    x["kd_band_ns"] = BAND_NS
    x["note"] = (x["note"].replace("A227", "A229", 1).replace("A224", "A229", 1)
                 + f", within {BAND_NS} ns above it (kd_band_ns)")
    return n, x


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [banded(*M28.released(z, t), f"{z}_{k}_b") for k, t in T_REL.items() for z in M24.Z_ROWS]
    rows += [banded(*M23.ROWS[r], f"{r}_b") for r in W_ROWS + I_ROWS]
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs")
