"""A243 cfgs (BOUNDARY Section 1): each row is its reference record's cfg with "early_hold_a" 0.0 and "late_hold_a"
0.0 (arm b: any valley report whose low-side turn-off current had not reversed leaves dt_pred). Rows as A241 / A242
(out run_b_<row>.json). No code change since A242, so no identity row.
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
STAGE1, STAGE2, A37_ROWS, src, ref = M41.STAGE1, M41.STAGE2, M41.A37_ROWS, M41.src, M41.ref
HOLD_A = 0.0


def main():
    for row in STAGE1 + STAGE2:
        c = json.loads(src(row).read_text())
        b = dict(c, out=f"run_b_{row}.json", early_hold_a=HOLD_A, late_hold_a=HOLD_A,
                 note=f"A243 arm b: {src(row).parent.parent.name} {src(row).stem[4:]} + early_hold_a and late_hold_a {HOLD_A}")
        (COS / f"cfg_b_{row}.json").write_text(json.dumps(b, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
