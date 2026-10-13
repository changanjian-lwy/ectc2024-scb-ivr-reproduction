"""A210 cosim cfgs: the load release of A207 / A208 on the other boards of A206's stage 2, with the lower Ton limit
proposed by A208 (cfg "ton_min_ns"). Board cfgs from A206's make_cfgs.board_v6 (final configuration on plant V6, low
sides 0.3 ohm x the board's drive factor, A206's start-up trims). Row r_<board>_<temp>_<p>: p % of 250 A left from
300 us on, end 450 us; every gate edge of the last 13 us logged for the loss books.
  python3 make_cfgs.py [ton_min_ns] -> cosim/cfg_r_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a206_cfgs", HERE.parent / "A206_p24_low_side_zvs_turn_on" / "make_cfgs.py")
A6 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A6)
COS = HERE / "cosim"
I_FULL, T_STEP, T_END, R_LS = 250.0, 300.0, 450.0, 0.3
ROWS = (("N75", "25", (40, 30, 20)), ("S75", "25", (30, 20)), ("S75", "c0", (30, 20)), ("S75", "hot", (30, 20)))


def row(a194, trims, b, tk, p, ton_min_ns):
    c, r_b, d = A6.board_v6(a194, b, tk, R_LS, trims)
    i_a = -I_FULL * (100 - p) / 100.0
    name = f"r_{b}_{tk}_{p}"
    return name, dict(c, ton_min_ns=ton_min_ns, load_step={"t_us": T_STEP, "i_a": i_a}, t_end_us=T_END,
                      snap_us=[[T_END - 2.0, T_END - 0.5]], debug_edges_us=[T_END - 13.0, T_END - 0.1], out=f"run_{name}.json",
                      note=f"A210 {name}: board {b}, {a194.TEMPS[tk]:g} C, final configuration on plant V6 (low-side turn-on {r_b:g} ohm, "
                           f"ton_s {c['ton_s_ns']} ns), lower Ton limit {ton_min_ns:g} ns, {i_a:g} A drawn from {T_STEP:g} us on: "
                           f"{p} % of {I_FULL:g} A remain")


if __name__ == "__main__":
    ton_min = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    a194 = A6._a194()
    trims = json.loads(A6.TRIMS.read_text())["dton_s_ns"]
    COS.mkdir(exist_ok=True)
    order = []
    for b, tk, ps in ROWS:
        for p in ps:
            name, c = row(a194, trims, b, tk, p, ton_min)
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs with ton_min_ns", ton_min, "; run-equivalents of 900 us:", round(len(order) * T_END / 900.0, 2))
