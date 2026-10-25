"""A246 cfgs (BOUNDARY Section 1). Arm h on A244's 46 rows: A244's cfg_w_<row> (the final configuration; rev_n 16 added,
A245) + "hold_floor_ns" BAND (out run_h_<row>.json). Control (g10): CTRL_ROW with the load train and the end moved by
k T / 6 (k 2, 4; T the switching period, from phase 1's turn-ons in A244's record before the train) in arm h and in
arm w (A244's cfg + rev_n 16, no floor): run_ch_ / run_cw_<row>_k<k>.json. FIRST: queue order.
  python3 make_cfgs.py"""
from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A44 = TA / "A244_p24_holds_after_handover"
_s = importlib.util.spec_from_file_location("a244_make_cfgs", A44 / "make_cfgs.py")
M44 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M44)
STAGE1, STAGE2 = M44.STAGE1, M44.STAGE2
REV_N, BAND, CTRL_ROW, KS = 16, 3.0, "p_N0_100k", (2, 4)
FIRST = ("m4_l_m80_10us", "m4_s_p250", "p_N0_100k", "p_S75h_100k", "p_S75h_60k", "p_S75h_10k", "p_S75h_30k")


def w_cfg(row):
    return dict(json.loads((A44 / "cosim" / f"cfg_w_{row}.json").read_text()), rev_n=REV_N)


def period_us(row):
    r = json.loads((A44 / "cosim" / f"run_w_{row}.json").read_text())
    t0 = r["cfg"]["load_pulse"]["t_us"] * 1e-6
    on = [x["t_s"] for x in r["turnons_last"] if x["phase"] == 1 and t0 - 20e-6 <= x["t_s"] < t0]
    return statistics.median(b - a for a, b in zip(on, on[1:])) * 1e6


def moved(c, dt_us):
    lp = c["load_pulse"]
    return dict(c, load_pulse=dict(lp, t_us=round(lp["t_us"] + dt_us, 4), t_stop_us=round(lp["t_stop_us"] + dt_us, 4)),
                t_end_us=round(c["t_end_us"] + dt_us, 4))


def main():
    for row in STAGE1 + STAGE2:
        h = dict(w_cfg(row), hold_floor_ns=BAND, out=f"run_h_{row}.json",
                 note=f"A246 arm h: A244 w_{row} + rev_n {REV_N} + hold_floor_ns {BAND}")
        (COS / f"cfg_h_{row}.json").write_text(json.dumps(h, indent=1) + "\n")
    t = period_us(CTRL_ROW)
    for k in KS:
        m = moved(w_cfg(CTRL_ROW), k * t / 6)
        w = dict(m, out=f"run_cw_{CTRL_ROW}_k{k}.json",
                 note=f"A246 control arm w: A244 w_{CTRL_ROW} + rev_n {REV_N}, train moved by {k} T / 6 (T {t:.4f} us)")
        h = dict(m, hold_floor_ns=BAND, out=f"run_ch_{CTRL_ROW}_k{k}.json", note=w["note"].replace("arm w", "arm h")
                 + f" + hold_floor_ns {BAND}")
        (COS / f"cfg_cw_{CTRL_ROW}_k{k}.json").write_text(json.dumps(w, indent=1) + "\n")
        (COS / f"cfg_ch_{CTRL_ROW}_k{k}.json").write_text(json.dumps(h, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs, T", round(t, 4), "us")


if __name__ == "__main__":
    main()
