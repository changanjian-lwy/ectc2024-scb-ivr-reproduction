"""A253 cfgs (BOUNDARY Section 1): the final configuration (A246 cfg_h_<row>) + "ocp" {"i_a": THR[L], "t_ns": T_NS} on
every reference row whose whole-run high-side turn-off current reached 175 A (6 of A246's 46 and A245's 20 start-ups,
all on L 2.2 nH) and on two identity rows where the comparator crosses its level in every full-load period.
  python3 make_cfgs.py -> cosim/cfg_o_<row>.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A46 = TA / "A246_p24_held_report_floor" / "cosim"
ACT = ("p_N75_1000k", "p_S75h_1000k", "a_S75h_d2", "a_S75h_d20", "a_S75_d20", "k_S75h")
IDENT = ("p_N75_100k", "p_N0_100k")
THR = {2.2: 130.0, 2.933: 145.0}          # 200 A minus the edge's ~12 A minus slope x (t_drv + t_ns + ~1 ns)
T_NS = 1.0


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    for row in ACT + IDENT:
        c = json.loads((A46 / f"cfg_h_{row}.json").read_text())
        ocp = {"i_a": THR[round(c["circuit"]["L"] * 1e9, 3)], "t_ns": T_NS}
        c.update(ocp=ocp, out=f"run_o_{row}.json", note=f"A253: A246 cfg_h_{row} + ocp {ocp}")
        (HERE / "cosim" / f"cfg_o_{row}.json").write_text(json.dumps(c, indent=1) + "\n")


if __name__ == "__main__":
    main()
