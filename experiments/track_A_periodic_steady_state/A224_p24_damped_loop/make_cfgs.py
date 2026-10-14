"""A224 cosim cfgs: A223's final-configuration rows (plant V7, A222's trims) with phase 1's cap gated to rising Vin
(vff rel_gate 25, A223) and the voltage loop's derivative term (cfg kd_ns_per_v, kd_db 2 codes; A224).
- stage 1: A223's three w rows that missed c1 (w5_N0, w20_N0, w5_N75), the k row (+62.5 A on N0) and two rising line
  rows (l_N0_p48, k_S75h) at kd 355 and 530 ns/V (cfg_<row>_d355 / _d530); i_u_N0_g25: A223's u_N0_g25 again on
  A224's code (kd absent; identity);
- stage 2 (kd chosen by BOUNDARY Section 4): the remaining A223 rows (w0_N0, w30_S75h, u_N0, l_N0_m80) and A221's
  skipping rows (N0 10 %, N75 10 %, N0 no load; A222's trims) at that kd (cfg_<row>_d<kd>).
    python3 make_cfgs.py 1          -> cosim/cfg_*.json, cosim/ORDER_S1.txt
    python3 make_cfgs.py 2 <kd>     -> cosim/cfg_*.json, cosim/ORDER_S2.txt"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a223_make_cfgs", TA / "A223_p24_cap_on_rising_vin" / "make_cfgs.py")
M23 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M23)
GATE, DB = M23.GATE, 2
S1_ROWS, S1_KD = ("w5_N0", "w20_N0", "w5_N75", "k_N0", "k_S75h", "l_N0_p48"), (355, 530)
S2_ROWS = ("w0_N0", "w30_S75h", "u_N0", "l_N0_m80")
Z_ROWS = {"z_N0_10": ("z_N0_25_10", "N0"), "z_N75_10": ("z_N75_25_10", "N75"), "z_N0_0": ("z_N0_25_0", "N0")}


def arm(c, what, name, kd):
    x = copy.deepcopy(c)
    x["vff"] = dict(x["vff"], rel_gate=GATE)
    if kd:
        x["kd_ns_per_v"], x["kd_db"] = float(kd), DB
    x["out"] = f"run_{name}.json"
    x["note"] = (f"A224 {name}: {what}; final configuration on plant V7 (r_core {x['circuit']['r_core']} ohm, ton_s_ns "
                 f"{x['ton_s_ns']}), skip {x.get('skip')}, vff rel_gate {GATE}"
                 + (f", derivative term kd {kd} ns/V, dead band {DB} codes" if kd else ", no derivative term"))
    return name, x


def z_row(src, board):
    c = M23.final(M23.load(f"A221_p24_core_loss_and_pause/cosim/cfg_{src}.json"), board)
    return c, f"A221's {src} (released at 300 us)"


def write(rows, order_name):
    COS.mkdir(exist_ok=True)
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / order_name).write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs ->", order_name)


if __name__ == "__main__":
    if sys.argv[1] == "1":
        rows = [arm(*M23.ROWS[r], f"{r}_d{kd}", kd) for kd in S1_KD for r in S1_ROWS]
        rows.append(arm(*M23.ROWS["u_N0"], "i_u_N0_g25", 0))
        write(rows, "ORDER_S1.txt")
    else:
        kd = int(sys.argv[2])
        rows = [arm(*M23.ROWS[r], f"{r}_d{kd}", kd) for r in S2_ROWS]
        rows += [arm(*z_row(*v), f"{k}_d{kd}", kd) for k, v in Z_ROWS.items()]
        write(rows, "ORDER_S2.txt")
