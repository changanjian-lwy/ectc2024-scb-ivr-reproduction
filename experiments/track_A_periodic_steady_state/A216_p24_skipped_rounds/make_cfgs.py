"""A216 cosim cfgs: skipped rounds (cfg "skip", scb_ctrl cfg_skip) on the final configuration, plant V6, lower Ton
limit 4.0 ns, the Ton path's registers at TON_LAT clocks (A215). Board cfgs from A210's row() (A206's board_v6).
  z_<board>_<temp>_<p>     the load released to p % of 250 A at 300 us, end 450 us;
  u_N0_25_5_s62            released to 5 % at 300 us, +62.5 A back at 380 us (cfg "load_step2"), end 460 us;
  w_N0_25_5_up             information: released to 5 %, the whole 237.5 A back at 380 us, with skipping;
  w_N0_25_20_up_ns         information: released to 20 %, 200 A back at 380 us, without skipping;
  f_S75_25_30              information: the slow board at 30 % with the lower limit at 20.78 ns (its 60 % load register);
  i_n_s_p62                identity: A215's m16_n_s_p62 with "skip" configured (the limit is never reached).
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a210_cfgs", TA / "A210_p24_load_range_boards" / "make_cfgs.py")
A10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A10)
COS = HERE / "cosim"
TON_MIN_NS, TON_LAT = 4.0, 16
SKIP = {"hi_mv": 5.0, "lo_mv": 1.0}
T_UP, T_END_UP = 380.0, 460.0
Z = (("N0", "25", 20), ("N0", "25", 10), ("N0", "25", 0), ("N75", "25", 10), ("S75", "25", 10), ("S75", "hot", 10))
FLOOR_S75_NS = 20.78                      # A211: S75's Ton register at 60 % of the load


def base(a194, trims, b, tk, p, ton_min=TON_MIN_NS):
    name, c = A10.row(a194, trims, b, tk, p, ton_min)
    return dict(c, ton_lat=TON_LAT, skip=dict(SKIP))


def up(c, i_a):
    return dict(c, load_step2={"t_us": T_UP, "i_a": i_a}, t_end_us=T_END_UP, snap_us=[[T_END_UP - 2.0, T_END_UP - 0.5]],
                debug_edges_us=[T_END_UP - 13.0, T_END_UP - 0.1])


if __name__ == "__main__":
    a194 = A10.A6._a194()
    trims = json.loads(A10.A6.TRIMS.read_text())["dton_s_ns"]
    COS.mkdir(exist_ok=True)
    rows = {}
    for b, tk, p in Z:
        rows[f"z_{b}_{tk}_{p}"] = (base(a194, trims, b, tk, p), f"board {b} {tk}, released to {p} %")
    rows["u_N0_25_5_s62"] = (up(base(a194, trims, "N0", "25", 5), 62.5), "N0, released to 5 %, +62.5 A at 380 us")
    rows["w_N0_25_5_up"] = (up(base(a194, trims, "N0", "25", 5), 237.5), "N0, released to 5 %, +237.5 A at 380 us (information)")
    c = up(base(a194, trims, "N0", "25", 20), 200.0)
    c.pop("skip")
    rows["w_N0_25_20_up_ns"] = (c, "N0, released to 20 %, +200 A at 380 us, no skipping (information)")
    rows["f_S75_25_30"] = (base(a194, trims, "S75", "25", 30, FLOOR_S75_NS), f"S75, 30 %, lower limit {FLOOR_S75_NS} ns (information)")
    c = json.loads((TA / "A215_p24_buildable_ton_path" / "cosim" / "cfg_m16_n_s_p62.json").read_text())
    rows["i_n_s_p62"] = (dict(c, ton_lat=TON_LAT, skip=dict(SKIP)), "A215's m16_n_s_p62 with skip configured (identity)")
    for name, (c, what) in rows.items():
        c = dict(c, out=f"run_{name}.json",
                 note=f"A216 {name}: {what}; final configuration on plant V6, lower Ton limit {c['ton_min_ns']:g} ns, ton_lat {c['ton_lat']}, "
                      f"skip {c.get('skip')}")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(rows) + "\n")
    print(len(rows), "cfgs; run-equivalents of 900 us:", round(sum(c["t_end_us"] for c, _ in rows.values()) / 900.0, 2))
