"""A249 cfgs (BOUNDARY Section 1): the final configuration's cfg of each row plus "dt_fix_ns", phases 2..4 held at one
delay per board (a249_values.json): arm s = the learner's own settled dt_pred, arm o = A248's window choice mapped to a
command. Rows and their final-configuration references:
- stage 1 (A240's load train): p_N0_100k at k 0 / 2 / 4 of T / 6 (A246 cfg_h_ / cfg_ch_), p_N0_60k, p_N75_100k,
  p_S75h_100k (A246 cfg_h_);
- stage 2: a_S75h_d20 (item 2's re-application), f_N75_k4 (item 3's falling line) (A246 cfg_h_);
- start-up: u_S75h_30 (item 6c; A245 cfg_r_ + hold_floor_ns 3.0, the final configuration since A246).
FIRST: queue order.
  python3 make_cfgs.py -> cosim/cfg_[so]_<row>.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A46 = TA / "A246_p24_held_report_floor" / "cosim"
A45 = TA / "A245_p24_reverse_conduction_delay" / "cosim"
ROWS = {"p_N0_100k": A46 / "cfg_h_p_N0_100k.json", "p_N0_100k_k2": A46 / "cfg_ch_p_N0_100k_k2.json",
        "p_N0_100k_k4": A46 / "cfg_ch_p_N0_100k_k4.json", "p_N0_60k": A46 / "cfg_h_p_N0_60k.json",
        "p_N75_100k": A46 / "cfg_h_p_N75_100k.json", "p_S75h_100k": A46 / "cfg_h_p_S75h_100k.json",
        "a_S75h_d20": A46 / "cfg_h_a_S75h_d20.json", "f_N75_k4": A46 / "cfg_h_f_N75_k4.json",
        "u_S75h_30": A45 / "cfg_r_u_S75h_30.json"}
REFS = {"p_N0_100k": A46 / "run_h_p_N0_100k.json", "p_N0_100k_k2": A46 / "run_ch_p_N0_100k_k2.json",
        "p_N0_100k_k4": A46 / "run_ch_p_N0_100k_k4.json", "p_N0_60k": A46 / "run_h_p_N0_60k.json",
        "p_N75_100k": A46 / "run_h_p_N75_100k.json", "p_S75h_100k": A46 / "run_h_p_S75h_100k.json",
        "a_S75h_d20": A46 / "run_h_a_S75h_d20.json", "f_N75_k4": A46 / "run_h_f_N75_k4.json",
        "u_S75h_30": A45 / "run_r_u_S75h_30.json"}
FIRST = ("p_N0_100k", "p_N0_100k_k2", "p_N0_100k_k4", "p_S75h_100k", "u_S75h_30")


def board(cfg):
    lf, temp = cfg["circuit"]["L"] * 1e9, cfg.get("gate", {}).get("temp", 25.0)
    return {(2.933, 25.0): "N0", (2.2, 25.0): "N75", (2.2, 125.0): "S75h"}[(round(lf, 3), float(temp))]


def main():
    v = json.loads((HERE / "a249_values.json").read_text())["boards"]
    COS.mkdir(exist_ok=True)
    for row, f in ROWS.items():
        base = json.loads(f.read_text())
        if row.startswith("u_"):
            base["hold_floor_ns"] = 3.0
        b = board(base)
        for arm, key in (("s", "settled_dt_pred_ns"), ("o", "opt_dt_pred_ns")):
            c = dict(base, dt_fix_ns=v[b][key], out=f"run_{arm}_{row}.json",
                     note=f"A249 arm {arm}: {f.relative_to(TA)} (final configuration) + dt_fix_ns {v[b][key]} ({b})")
            (COS / f"cfg_{arm}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
