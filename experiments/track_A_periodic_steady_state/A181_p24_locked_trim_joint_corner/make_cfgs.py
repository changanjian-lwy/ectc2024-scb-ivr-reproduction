"""A181 cosim cfgs: a start-up trim set once at 25 C, then locked, under joint adverse conditions.
Boards (each trimmed once at 25 C at its own device corner, the factory calibration):
- N0  nominal devices, L0:        A164's trim 39.615 ns;
- S0  slow corner (ss), L0:       A164's trim 48.348 ns;
- S75 slow corner, L x 0.75:      trimmed here (stage 1).
Conditions (trim locked): N0 at 125 C (one step position); S0 at 125 C; S75 at 25 C; S75 at 125 C (three positions
each). All at t_il 1.0 ns (the interlock target from A179). Row +4.8 V / 1 us, step at 500 us + k T / 3 (T = 0.5048 us
x L scale, A178's proportional period), end = step + 400 us (A179's window).
Bases: A171's S50 nominal l_p48_1us cfg (A178's base) and A173's il1p4 ss l_p48_1us cfg; they differ only in gate and
ton (checked). A '125 C' condition adds gate temp 125 to the board's own corner.
  python3 make_cfgs.py cal   stage 1: cosim_cal/cfg_S75_t<ton>.json, start-ups to 150 us at three trims around the
                             guess 48.348 x 36.379 / 39.615 (A178's L x 0.75 / L0 trim ratio)
  python3 make_cfgs.py       stage 2: trims.json (S75 interpolated between the start-ups bracketing Vo 1.035 V) and
                             cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
TA = HERE.parent
BASE = {"nom": TA / "A171_p24_gate_interlock_threshold" / "cosim" / "cfg_S50_nom_l_p48_1us.json",
        "ss": TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_il1p4_ss_l_p48_1us.json"}
L0, T0 = 2.9333333199999997e-09, 0.5048
T_IL, T_STEP0, POST_US = 1.0, 500.0, 400.0
VO_TGT, VO_CLIFF = 1.035, 0.99
TRIM = {"N0": 39.615, "S0": 48.348}
BOARDS = {"N0": ("nom", 1.0), "S0": ("ss", 1.0), "S75": ("ss", 0.75)}
GUESS_S75 = round(48.348 * 36.379 / 39.615, 3)
CAL_TONS = (round(GUESS_S75 - 1.0, 3), GUESS_S75, round(GUESS_S75 + 1.0, 3))
# condition: (board, temp C, step offsets in periods)
CONDS = {"N0_hot": ("N0", 125.0, (0.0,)), "S0_hot": ("S0", 125.0, (0.0, 1 / 3, 2 / 3)),
         "S75_25": ("S75", 25.0, (0.0, 1 / 3, 2 / 3)), "S75_hot": ("S75", 125.0, (0.0, 1 / 3, 2 / 3))}


def cfg(board, ton, temp, t_step, t_end):
    corner, s = BOARDS[board]
    c = json.loads(BASE[corner].read_text())
    g = dict(c["gate"], t_il_ns=T_IL)
    if temp != 25.0:
        g["temp"] = temp
    return dict(c, circuit=dict(c["circuit"], L=L0 * s), gate=g, ton_ns=ton,
                line_step=dict(c["line_step"], t_us=t_step), t_end_us=t_end)


def check_bases():
    a, b = (json.loads(BASE[k].read_text()) for k in ("ss", "nom"))
    assert {k for k in set(a) | set(b) if a.get(k) != b.get(k)} <= {"gate", "ton_ns", "note", "out"}


def cal():
    check_bases()
    CAL.mkdir(exist_ok=True)
    for ton in CAL_TONS:
        name = f"S75_t{ton:.3f}".replace(".", "p")
        c = dict(cfg("S75", ton, 25.0, T_STEP0, 150.0), out=f"run_{name}.json",
                 note=f"A181 stage 1: slow-corner L x 0.75 board start-up at 25 C, ton {ton} ns, t_il {T_IL} ns")
        (CAL / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(CAL_TONS), "cal cfgs", CAL_TONS)


def s75_trim():
    pts = []
    for ton in CAL_TONS:
        r = json.loads((CAL / f"run_S75_t{ton:.3f}.json".replace(".", "p", 1)).read_text())
        vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
        pts.append((ton, vo))
    ok = [p for p in pts if p[1] >= VO_CLIFF]                      # below the cliff the slope does not hold (A168)
    lo = max((p for p in ok if p[1] <= VO_TGT), default=None, key=lambda p: p[1])
    hi = min((p for p in ok if p[1] >= VO_TGT), default=None, key=lambda p: p[1])
    if lo and hi and lo != hi:
        ton = lo[0] + (VO_TGT - lo[1]) * (hi[0] - lo[0]) / (hi[1] - lo[1])
    else:                                                          # all on one side: A164's slope from the nearest
        n = min(ok, key=lambda p: abs(p[1] - VO_TGT))
        ton = n[0] + (VO_TGT - n[1]) / 0.026
    return round(ton, 3), pts


def main():
    COS.mkdir(exist_ok=True)
    ton75, pts = s75_trim()
    trims = dict(TRIM, S75=ton75)
    order = []
    for name, (b, temp, offs) in CONDS.items():
        s = BOARDS[b][1]
        for k, f in enumerate(offs):
            t = round(T_STEP0 + f * T0 * s, 4)
            run = f"{name}_p{k}"
            c = dict(cfg(b, trims[b], temp, t, round(t + POST_US, 4)), out=f"run_{run}.json",
                     note=f"A181 {run}: board {b} (trim {trims[b]} ns set at 25 C, locked) at {temp:g} C, t_il {T_IL} ns, "
                          f"+4.8 V / 1 us at {t} us")
            (COS / f"cfg_{run}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(run)
    (HERE / "trims.json").write_text(json.dumps({"trims_ns": trims, "s75_cal": pts}, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", trims)


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
