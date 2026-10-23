"""A242 cfgs (BOUNDARY Section 1): each row is its reference record's cfg with "late_hold_a" 0.0 (arm l: a late
valley report whose low-side turn-off current had not reversed leaves dt_pred). Rows as A241: stage 1 = A240's 18
accelerator-load rows, stage 2 = A236's 25 rows and A237's three single re-applications (out run_l_<row>.json).
o_cw5_N75 is A237's cfg unchanged (option absent, out run_o_cw5_N75.json) for the identity check.
  python3 make_cfgs.py"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a241_make_cfgs", TA / "A241_p24_dt_pred_fall_limit" / "make_cfgs.py")
M41 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M41)
STAGE1, STAGE2, A37_ROWS, IDENT, src, ref = M41.STAGE1, M41.STAGE2, M41.A37_ROWS, M41.IDENT, M41.src, M41.ref
HOLD_A = 0.0


def main():
    for row in STAGE1 + STAGE2:
        c = json.loads(src(row).read_text())
        l = dict(c, out=f"run_l_{row}.json", late_hold_a=HOLD_A,
                 note=f"A242 arm l: {src(row).parent.parent.name} {src(row).stem[4:]} + late_hold_a {HOLD_A}")
        (COS / f"cfg_l_{row}.json").write_text(json.dumps(l, indent=1) + "\n")
    c = json.loads(src(IDENT).read_text())
    o = dict(c, out=f"run_o_{IDENT}.json", note=f"A242 identity: A237 {IDENT} unchanged (option absent)")
    (COS / f"cfg_o_{IDENT}.json").write_text(json.dumps(o, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
