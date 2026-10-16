"""A236 cfgs (BOUNDARY Section 1): each row is its reference record's cfg with "early_hold_a" 0.0 (arm h, out
run_h_<row>.json); o_f_N75_k4 is A232's cfg unchanged (option off, out run_o_f_N75_k4.json) for the identity check.
  python3 make_cfgs.py"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
SRC = {"A232": "A232_p24_fast_falling_step_v7", "A235": "A235_p24_v7_corner_boards", "A228": "A228_p24_damped_loop_adoption",
       "A225": "A225_p24_startup_items_recheck", "A229": "A229_p24_kd_band", "A234": "A234_p24_four_modules_v7"}
ROWS = {                                            # row -> (experiment, reference cfg stem)
    "f_N0_k0": ("A232", "f_N0_k0_b"), "f_N0_k4": ("A232", "f_N0_k4_b"),
    "f_N75_k0": ("A232", "f_N75_k0_b"), "f_N75_k2": ("A232", "f_N75_k2_b"), "f_N75_k4": ("A232", "f_N75_k4_b"),
    "f_S75_k0": ("A232", "f_S75_k0_b"),
    "r_N13_lm48": ("A235", "r_N13_lm48"), "r_F0_lm48": ("A235", "r_F0_lm48"), "r_F0_lm80": ("A235", "r_F0_lm80"),
    "l_N0_m80": ("A228", "l_N0_m80_h"), "l_N0_p48": ("A228", "l_N0_p48_h"),
    "a_S75h_d2": ("A225", "a_S75h_d2"), "a_S75h_d20": ("A225", "a_S75h_d20"), "a_S75_d20": ("A225", "a_S75_d20"),
    "k_N0": ("A229", "k_N0_b"), "k_S75h": ("A229", "k_S75h_b"), "u_N0": ("A229", "u_N0_b"),
    "w5_N0": ("A229", "w5_N0_b"), "w20_N0": ("A229", "w20_N0_b"), "w5_N75": ("A229", "w5_N75_b"),
    "w30_S75h": ("A229", "w30_S75h_b"),
    "z_N0_10_t0": ("A229", "z_N0_10_t0_b"), "z_N75_10_t0": ("A229", "z_N75_10_t0_b"),
    "m4_l_m80_10us": ("A234", "m4_l_m80_10us_b"), "m4_s_p250": ("A234", "m4_s_p250_b"),
}
IDENT = ("f_N75_k4",)


def src(row):
    e, stem = ROWS[row]
    return TA / SRC[e] / "cosim" / f"cfg_{stem}.json"


def ref(row):
    e, stem = ROWS[row]
    return TA / SRC[e] / "cosim" / json.loads(src(row).read_text())["out"]


def main():
    for row in ROWS:
        c = json.loads(src(row).read_text())
        h = dict(c, out=f"run_h_{row}.json", early_hold_a=0.0, note=f"A236 arm h: {ROWS[row][0]} {ROWS[row][1]} + early_hold_a 0")
        (COS / f"cfg_h_{row}.json").write_text(json.dumps(h, indent=1) + "\n")
        if row in IDENT:
            o = dict(c, out=f"run_o_{row}.json", note=f"A236 identity: {ROWS[row][0]} {ROWS[row][1]} unchanged")
            (COS / f"cfg_o_{row}.json").write_text(json.dumps(o, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
