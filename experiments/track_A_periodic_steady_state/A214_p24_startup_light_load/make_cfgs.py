"""A214 cosim cfgs: start-up into less than the full load. A206's board cfgs (final configuration on plant V6, low
sides 0.3 ohm x the board's factor, A206's trims) with A208's ton_min_ns 4.0 and the resistive load set to
4 mOhm / share (cfg circuit r_load): the load is there from the start, so mode S, the handover and mode P all see it.
End 300 us. Row u_<board>_<temp>_<p>: p % of 250 A at 1 V.
  python3 make_cfgs.py -> cosim/cfg_u_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a206_cfgs", HERE.parent / "A206_p24_low_side_zvs_turn_on" / "make_cfgs.py")
A6 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A6)
COS = HERE / "cosim"
R_FULL, T_END, TON_MIN_NS = 4e-3, 300.0, 4.0
ROWS = (("N0", "25", (75, 50, 30)), ("S75", "25", (50,)), ("S75", "hot", (50,)))

if __name__ == "__main__":
    a194 = A6._a194()
    trims = json.loads(A6.TRIMS.read_text())["dton_s_ns"]
    COS.mkdir(exist_ok=True)
    order = []
    for b, tk, ps in ROWS:
        for p in ps:
            c, r_b, d = A6.board_v6(a194, b, tk, 0.3, trims)
            name = f"u_{b}_{tk}_{p}"
            c = dict(c, circuit=dict(c["circuit"], r_load=R_FULL * 100.0 / p), ton_min_ns=TON_MIN_NS, t_end_us=T_END, out=f"run_{name}.json",
                     note=f"A214 {name}: board {b}, {a194.TEMPS[tk]:g} C, final configuration on plant V6 (ton_s {c['ton_s_ns']} ns, lower Ton "
                          f"limit {TON_MIN_NS:g} ns), start-up into a {1e3 * R_FULL * 100.0 / p:.3f} mOhm load ({p} % of 250 A at 1 V)")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(order)
