"""A184 cosim cfgs: A183's 200 ns mode-S period with mode S's own Ton (RTL cfg_ton_s, cfg "ton_s_ns" = A183's trim)
while ton_ns (the loop's reset value, scb_vff's seed, the 0.5x / 2x clamps) keeps each board's validated t0 = 400 ns
trim. Boards and plant as A183 (V5, t_il 1.0 ns); A183's board_cfg builds the base cfg.
  python3 make_cfgs.py   cosim/cfg_<cond>_p<k>.json and cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a183_make", TA / "A183_p24_startup_period_ladder" / "make_cfgs.py")
A183 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A183)
COS = HERE / "cosim"
T0 = 200
TRIM_S = json.loads((TA / "A183_p24_startup_period_ladder" / "trims.json").read_text())["trims_ns"]
# validated t0 = 400 ns trims: A181 (S75), A164 (S0, N0), A178 (N75), A172 / A173 (N07, N13, F0)
TRIM_P = {"S75": 43.325, "S0": 48.348, "N0": 39.615, "N75": 36.379, "N07": 35.769, "N13": 40.916, "F0": 37.692}
M4_BASE = TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_m4_nom_s_p62.json"
T_STEP0, POST_US, T_LONG, PER0 = 500.0, 400.0, 500.0, 0.5048
# (board, temp C, step offsets in periods, full run with the +4.8 V / 1 us step)
CONDS = {"S75_25": ("S75", 25.0, (0.0, 1 / 3, 2 / 3), True), "S75_hot": ("S75", 125.0, (0.0,), True),
         "N0_25": ("N0", 25.0, (0.0,), True),
         "S0_25": ("S0", 25.0, (0.0,), False), "N75_25": ("N75", 25.0, (0.0,), False), "N07_25": ("N07", 25.0, (0.0,), False),
         "N13_25": ("N13", 25.0, (0.0,), False), "F0_25": ("F0", 25.0, (0.0,), False),
         "N0_hot": ("N0", 125.0, (0.0,), False), "S0_hot": ("S0", 125.0, (0.0,), False), "F0_hot": ("F0", 125.0, (0.0,), False)}


def board(b, temp, t_step, t_end):
    c = A183.board_cfg(b, T0, TRIM_P[b], temp, t_step, t_end)
    return dict(c, ton_s_ns=TRIM_S[b])


def m4():
    """Four nominal modules (A173's m4_nom_s_p62: +62.5 A load step at 800 us, not reached) to 500 us."""
    c = json.loads(M4_BASE.read_text())
    assert c["modules"] == 4 and c["ton_ns"] == TRIM_P["N0"] and c["t0_ns"] == 400.0
    return dict(c, t0_ns=float(T0), ton_s_ns=TRIM_S["N0"], gate=dict(c["gate"], t_il_ns=A183.T_IL), t_end_us=T_LONG)


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for cond, (b, temp, offs, full) in CONDS.items():
        for k, f in enumerate(offs):
            t = round(T_STEP0 + f * PER0 * A183.BOARDS[b][1], 4)
            run = f"{cond}_p{k}"
            c = dict(board(b, temp, t, round(t + POST_US, 4) if full else T_LONG), out=f"run_{run}.json",
                     note=f"A184 {run}: board {b}, mode-S period {T0} ns at its own Ton {TRIM_S[b]} ns, loop seed / clamps from "
                          f"{TRIM_P[b]} ns, both set at 25 C and locked, {temp:g} C, t_il {A183.T_IL} ns"
                          + (f", +4.8 V / 1 us at {t} us" if full else f", to {T_LONG} us"))
            (COS / f"cfg_{run}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(run)
    c = dict(m4(), out="run_M4_25_p0.json",
             note=f"A184 M4_25_p0: four nominal modules, mode-S period {T0} ns at {TRIM_S['N0']} ns, loop from {TRIM_P['N0']} ns, "
                  f"t_il {A183.T_IL} ns, to {T_LONG} us")
    (COS / "cfg_M4_25_p0.json").write_text(json.dumps(c, indent=1) + "\n")
    order.insert(0, "M4_25_p0")                                    # longest first
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
