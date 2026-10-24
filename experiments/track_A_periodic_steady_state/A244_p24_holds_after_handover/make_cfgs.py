"""A244 cfgs (BOUNDARY Section 1): each row is its reference record's cfg with "early_hold_a" and "late_hold_a" 0.0
and "hold_wait" 32 (arm w: A243's holds, acting only from phase 1's 32nd turn-on in mode P). Rows as A241-A243 (out
run_w_<row>.json); stage 2's rows that are most at risk run first. Identity: o_cw5_N75 is A243's cfg_b_cw5_N75
unchanged (hold_wait absent), to equal A243's run_b_cw5_N75 bit for bit.
  python3 make_cfgs.py"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A43 = TA / "A243_p24_hold_without_reversal"
_s = importlib.util.spec_from_file_location("a241_make_cfgs", TA / "A241_p24_dt_pred_fall_limit" / "make_cfgs.py")
M41 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M41)
STAGE1, STAGE2, A37_ROWS, src, ref = M41.STAGE1, M41.STAGE2, M41.A37_ROWS, M41.src, M41.ref
HOLD_A, WAIT, IDENT = 0.0, 32, "cw5_N75"
FIRST = ("a_S75h_d20", "a_S75h_d2", "a_S75_d20", "u_N0", "w5_N0", "w20_N0", "f_N75_k0", "f_N75_k2", "f_N75_k4",
         "r_N13_lm48", "m4_l_m80_10us", "m4_s_p250")     # A243's misses, item 3 and four modules: queue order only


def main():
    for row in STAGE1 + STAGE2:
        c = json.loads(src(row).read_text())
        w = dict(c, out=f"run_w_{row}.json", early_hold_a=HOLD_A, late_hold_a=HOLD_A, hold_wait=WAIT,
                 note=f"A244 arm w: {src(row).parent.parent.name} {src(row).stem[4:]} + early_hold_a and late_hold_a "
                      f"{HOLD_A}, hold_wait {WAIT}")
        (COS / f"cfg_w_{row}.json").write_text(json.dumps(w, indent=1) + "\n")
    o = json.loads((A43 / "cosim" / f"cfg_b_{IDENT}.json").read_text())
    o = dict(o, out=f"run_o_{IDENT}.json", note=f"A244 identity: A243 b_{IDENT} unchanged (hold_wait absent)")
    (COS / f"cfg_o_{IDENT}.json").write_text(json.dumps(o, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
