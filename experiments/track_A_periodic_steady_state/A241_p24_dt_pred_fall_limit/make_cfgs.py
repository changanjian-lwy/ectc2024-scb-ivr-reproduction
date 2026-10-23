"""A241 cfgs (BOUNDARY Section 1): each row is its reference record's cfg with "dt_fall_ns" = its own dt_step_ns
(arm f: dt_pred falls at most one step per report). Stage 1: A240's 18 accelerator-load rows (out run_f_<row>.json).
Stage 2: A236's 25 rows and A237's three single re-applications. o_cw5_N75 is A237's cfg unchanged (option absent,
out run_o_cw5_N75.json) for the identity check.
  python3 make_cfgs.py"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A40 = TA / "A240_p24_accelerator_load" / "cosim"
A37 = TA / "A237_p24_true_light_load" / "cosim"
_s = importlib.util.spec_from_file_location("a236_make_cfgs", TA / "A236_p24_early_hold" / "make_cfgs.py")
M36 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M36)
STAGE1 = [f"p_{b}_{f}k" for b in ("N0", "N75", "S75h") for f in (10, 30, 60, 100, 200, 1000)]
A37_ROWS = ("cw5_N0", "cw5_N75", "c30_S75h")
STAGE2 = list(M36.ROWS) + list(A37_ROWS)
IDENT = "cw5_N75"


def src(row):
    if row in STAGE1:
        return A40 / f"cfg_{row}.json"
    return A37 / f"cfg_{row}.json" if row in A37_ROWS else M36.src(row)


def ref(row):
    if row in STAGE1:
        return A40 / f"run_{row}.json"
    return A37 / f"run_{row}.json" if row in A37_ROWS else M36.ref(row)


def main():
    for row in STAGE1 + STAGE2:
        c = json.loads(src(row).read_text())
        f = dict(c, out=f"run_f_{row}.json", dt_fall_ns=c["dt_step_ns"],
                 note=f"A241 arm f: {src(row).parent.parent.name} {src(row).stem[4:]} + dt_fall_ns = dt_step_ns")
        (COS / f"cfg_f_{row}.json").write_text(json.dumps(f, indent=1) + "\n")
    c = json.loads(src(IDENT).read_text())
    o = dict(c, out=f"run_o_{IDENT}.json", note=f"A241 identity: A237 {IDENT} unchanged (option absent)")
    (COS / f"cfg_o_{IDENT}.json").write_text(json.dumps(o, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
