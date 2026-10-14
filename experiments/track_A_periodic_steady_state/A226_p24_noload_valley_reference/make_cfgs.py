"""A226 cosim cfgs: A224's N0 no-load skipping row (z_N0_0: A221's z_N0_25_0 with A222's N0 trim, plant V7, released
to no load at 300 us, to 750 us) without the derivative term - d0: the final configuration as it is (no gate, no kd);
g25: with A223's gate only. A224's run_z_N0_0_d355.json is the third arm.
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

if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    c, what = M24.z_row("z_N0_25_0", "N0")
    rows = []
    for arm in ("d0", "g25"):
        x = copy.deepcopy(c)
        if arm == "g25":
            x["vff"] = dict(x["vff"], rel_gate=M24.GATE)
        x["out"] = f"run_z_N0_0_{arm}.json"
        x["note"] = (f"A226 z_N0_0_{arm}: {what}; final configuration on plant V7 (r_core {x['circuit']['r_core']} ohm, "
                     f"ton_s_ns {x['ton_s_ns']}), skip {x.get('skip')}" + (f", vff rel_gate {M24.GATE}" if arm == "g25" else ""))
        (COS / f"cfg_z_N0_0_{arm}.json").write_text(json.dumps(x, indent=1) + "\n")
        rows.append(f"z_N0_0_{arm}")
    (COS / "ORDER.txt").write_text("\n".join(rows) + "\n")
    print(rows)
