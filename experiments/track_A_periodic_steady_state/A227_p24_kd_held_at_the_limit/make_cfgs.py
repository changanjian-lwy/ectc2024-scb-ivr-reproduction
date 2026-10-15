"""A227 cosim cfgs: A224's candidate (vff rel_gate 25, kd 355 ns/V, dead band 2) with cfg kd_hold 1 (no derivative
term while the PI output is at the lower Ton limit; A227), plant V7, A222's trims, one module.
- h arm (kd_hold): A224's three skipping rows (N0 10 %, N75 10 %, N0 no load) and the three re-applications that
  start from skipping (w0_N0, w5_N0, w5_N75);
- z_N0_10_d0: N0 10 % on the final configuration as it is (no gate, no kd) - the reference A224's e5 lacked.
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a224_make_cfgs", TA / "A224_p24_damped_loop" / "make_cfgs.py")
M24 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M24)
KD = 355


def held(c, what, name):
    n, x = M24.arm(c, what, name, KD)
    x["kd_hold"] = 1
    x["note"] = x["note"].replace("A224", "A227", 1) + ", held at the lower Ton limit (kd_hold 1)"
    return n, x


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [held(*M24.z_row(*v), f"{k}_h") for k, v in M24.Z_ROWS.items()]
    rows += [held(*M24.M23.ROWS[r], f"{r}_h") for r in ("w0_N0", "w5_N0", "w5_N75")]
    c, what = M24.z_row(*M24.Z_ROWS["z_N0_10"])
    x = copy.deepcopy(c)
    x["out"] = "run_z_N0_10_d0.json"
    x["note"] = (f"A227 z_N0_10_d0: {what}; final configuration on plant V7 (r_core {x['circuit']['r_core']} ohm, ton_s_ns "
                 f"{x['ton_s_ns']}), skip {x.get('skip')}, no gate, no derivative term")
    rows.append(("z_N0_10_d0", x))
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print([n for n, _ in rows])
