"""A212 cosim cfgs: the nominal board's stimulus rows of the final-plant coverage table (V5: A173, A175) on plant V6
with the present configuration: A206's board cfg for N0 at 25 C (low sides 0.3 ohm, A206's trim) and A208's lower
Ton limit (ton_min_ns 4.0). Stimulus at 500 us, end 620 us.
  python3 make_cfgs.py -> cosim/cfg_n_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a206_cfgs", HERE.parent / "A206_p24_low_side_zvs_turn_on" / "make_cfgs.py")
A6 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A6)
COS = HERE / "cosim"
T_STEP, T_END, TON_MIN_NS = 500.0, 620.0, 4.0
ROWS = {"l_p48_2us": {"line_step": {"dv": 4.8, "slew_us": 2.0}}, "l_p48_3us": {"line_step": {"dv": 4.8, "slew_us": 3.0}},
        "l_p48_4us": {"line_step": {"dv": 4.8, "slew_us": 4.0}}, "l_p48_5us": {"line_step": {"dv": 4.8, "slew_us": 5.0}},
        "l_p48_10us": {"line_step": {"dv": 4.8, "slew_us": 10.0}}, "l_m48_1us": {"line_step": {"dv": -4.8, "slew_us": 1.0}},
        "l_m80_10us": {"line_step": {"dv": -8.0, "slew_us": 10.0}}, "s_p62": {"load_step": {"i_a": 62.5}}}

if __name__ == "__main__":
    a194 = A6._a194()
    trims = json.loads(A6.TRIMS.read_text())["dton_s_ns"]
    COS.mkdir(exist_ok=True)
    order = []
    for name, stim in ROWS.items():
        c, r_b, d = A6.board_v6(a194, "N0", "25", 0.3, trims)
        k, v = next(iter(stim.items()))
        c = dict(c, **{k: dict(v, t_us=T_STEP)}, ton_min_ns=TON_MIN_NS, t_end_us=T_END, out=f"run_n_{name}.json",
                 note=f"A212 n_{name}: board N0, 25 C, final configuration on plant V6 (low sides {r_b:g} ohm, ton_s {c['ton_s_ns']} ns, "
                      f"lower Ton limit {TON_MIN_NS:g} ns), {k} {v} at {T_STEP:g} us")
        (COS / f"cfg_n_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(f"n_{name}")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs; run-equivalents of 900 us:", round(len(order) * T_END / 900.0, 2))
