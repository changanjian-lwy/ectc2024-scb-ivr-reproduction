"""A183 cosim cfgs: the mode-S (open-loop start-up) period t0 against the Cs-ladder split found in A181's records.
Only t0_ns and the board's start-up trim ton_ns change; plant V5 (all switches gate-driven, threshold interlock
1.0 ns), RTL and every other cfg value as A181.
  python3 make_cfgs.py screen   stage 1: cosim_screen/cfg_t<t0>_n<ton>.json - the slow-corner L x 0.75 board (A181's
                                S75) at 25 C, start-ups to 170 us (mode P from 144 us, the 20 us lead ramp included),
                                t0 200 / 250 / 300 / 500 ns x three trims each around the volt-second guess
  python3 make_cfgs.py extra T0 stage 1's extra pair (BOUNDARY Section 2) for a t0 whose runs do not bracket Vo 1.035 V:
                                ton* from the slope of the two runs nearest the target, pair at ton* -+ 0.3 ns
  python3 make_cfgs.py cal      stage 2 trims: cosim_cal/cfg_<board>_n<ton>.json, 150 us start-ups at t0* (a183_pick.json)
                                for the six boards other than S75, at the guess and -+ 2 ns; guess = 1.035 V t0* / 12 V
                                + k x S75's on-time loss at t0* (trim - 1.035 t0* / 12), k = 1 slow, 0.42 nominal, 0.30 ff
                                (L13 at t0 400, all hard: 6.4 ns lost vs S75's ~16)
  python3 make_cfgs.py calx B   stage 2 extra pair for board B (stage 1's rule) when its three start-ups miss Vo 1.035 V
  python3 make_cfgs.py main     stage 2 runs: cosim/cfg_<board>_<cond>.json, trims.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
SCREEN = HERE / "cosim_screen"
A181 = TA / "A181_p24_locked_trim_joint_corner"
L0 = 2.9333333199999997e-09
T_IL = 1.0
T_END_SCREEN = 170.0
VO_TGT = 1.035
# volt-second guess (BOUNDARY Section 3): ton = 1.035 V x t0 / 12 V + on-time change at turn-on (all hard: +16 ns
# lost, A181 S75 phase 1 at t0 400; all ZVS: -4 ns, phases 3-4); three trims 2 ns apart (3 ns at the mixed 300 / 500)
SCREEN_TONS = {200: (31.3, 33.3, 35.3), 250: (35.6, 37.6, 39.6), 300: (37.0, 40.0, 43.0), 500: (38.0, 41.0, 44.0)}


COS, CAL = HERE / "cosim", HERE / "cosim_cal"
BASE = {"nom": TA / "A171_p24_gate_interlock_threshold" / "cosim" / "cfg_S50_nom_l_p48_1us.json",
        "ss": TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_il1p4_ss_l_p48_1us.json"}
FF_GATE = json.loads((TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_ff_s_p62.json").read_text())["gate"]
BOARDS = {"S75": ("ss", 0.75), "S0": ("ss", 1.0), "N0": ("nom", 1.0), "N75": ("nom", 0.75), "N07": ("nom", 0.7),
          "N13": ("nom", 1.3), "F0": ("ff", 1.0)}
K_LOSS = {"ss": 1.0, "nom": 0.42, "ff": 0.30}
T_STEP0, POST_US, T_SHORT, T_CAL, PER0 = 500.0, 400.0, 300.0, 150.0, 0.5048
# (board, temp C, step offsets in periods, full run)
CONDS = {"S75_25": ("S75", 25.0, (0.0, 1 / 3, 2 / 3), True), "S75_hot": ("S75", 125.0, (0.0,), True),
         "N0_25": ("N0", 25.0, (0.0,), True), "S0_25": ("S0", 25.0, (0.0,), False), "N75_25": ("N75", 25.0, (0.0,), False),
         "N07_25": ("N07", 25.0, (0.0,), False), "N13_25": ("N13", 25.0, (0.0,), False), "F0_25": ("F0", 25.0, (0.0,), False)}


def board_cfg(board, t0, ton, temp, t_step, t_end):
    corner, sc = BOARDS[board]
    c = json.loads(BASE["ss" if corner == "ss" else "nom"].read_text())
    g = dict(FF_GATE if corner == "ff" else c["gate"], t_il_ns=T_IL)
    if temp != 25.0:
        g["temp"] = temp
    return dict(c, circuit=dict(c["circuit"], L=L0 * sc), gate=g, t0_ns=float(t0), ton_ns=float(ton),
                line_step=dict(c["line_step"], t_us=t_step), t_end_us=t_end)


def star():
    pk = json.loads((HERE / "a183_pick.json").read_text())
    t0 = pk["t0_star"]
    assert t0 is not None, "stage 1 picked no t0: stages 2-3 are not run (BOUNDARY Section 4)"
    return int(t0), pk["per_t0"][str(t0)]["trim_ns"]


def cal_guess(board):
    t0, trim75 = star()
    base = VO_TGT * t0 / 12.0
    return round(base + K_LOSS[BOARDS[board][0]] * (trim75 - base), 3)


def cal():
    t0, _ = star()
    CAL.mkdir(exist_ok=True)
    order = []
    for b in BOARDS:
        if b == "S75":
            continue
        g = cal_guess(b)
        for ton in (round(g - 2.0, 3), g, round(g + 2.0, 3)):
            order.append(write_cal(b, t0, ton))
    (CAL / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cal cfgs, t0*", t0)


def write_cal(b, t0, ton):
    n = f"{b}_n{ton:.3f}".replace(".", "p")
    c = dict(board_cfg(b, t0, ton, 25.0, T_STEP0, T_CAL), out=f"run_{n}.json",
             note=f"A183 stage 2 trim: board {b} at 25 C, mode-S period {t0} ns, ton {ton} ns, start-up to {T_CAL} us")
    (CAL / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
    return n


def cal_points(b):
    pts = []
    for f in sorted(CAL.glob(f"run_{b}_n*.json")):
        r = json.loads(f.read_text())
        pts.append((r["cfg"]["ton_ns"], sum(q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6) /
                    sum(1 for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6)))
    return pts


def board_trim(b):
    pts = cal_points(b)
    lo = max((p for p in pts if p[1] <= VO_TGT), default=None, key=lambda p: p[1])
    hi = min((p for p in pts if p[1] >= VO_TGT), default=None, key=lambda p: p[1])
    if not (lo and hi):
        return None, pts
    return round(lo[0] + (VO_TGT - lo[1]) * (hi[0] - lo[0]) / (hi[1] - lo[1]), 3), pts


def calx(b):
    t0, _ = star()
    pts = sorted(cal_points(b), key=lambda p: abs(p[1] - VO_TGT))
    (a, va), (c, vc) = pts[:2]
    ton = a + (VO_TGT - va) * (c - a) / (vc - va)
    order = (CAL / "ORDER.txt").read_text().split()
    order += [write_cal(b, t0, round(ton - 0.3, 3)), write_cal(b, t0, round(ton + 0.3, 3))]
    (CAL / "ORDER.txt").write_text("\n".join(order) + "\n")
    print("calx", b, round(ton, 3))


def main():
    t0, trim75 = star()
    trims, cal_pts = {"S75": trim75}, {}
    for b in BOARDS:
        if b != "S75":
            trims[b], cal_pts[b] = board_trim(b)
            assert trims[b] is not None, f"{b} not bracketed: run calx {b}"
    COS.mkdir(exist_ok=True)
    order = []
    for cond, (b, temp, offs, full) in CONDS.items():
        for k, f in enumerate(offs):
            t = round(T_STEP0 + f * PER0 * BOARDS[b][1], 4)
            run = f"{cond}_p{k}"
            c = dict(board_cfg(b, t0, trims[b], temp, t, round(t + POST_US, 4) if full else T_SHORT), out=f"run_{run}.json",
                     note=f"A183 {run}: board {b} (mode-S period {t0} ns, trim {trims[b]} ns set at 25 C, locked) at {temp:g} C, "
                          f"t_il {T_IL} ns" + (f", +4.8 V / 1 us at {t} us" if full else f", to {T_SHORT} us"))
            (COS / f"cfg_{run}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(run)
    (HERE / "trims.json").write_text(json.dumps({"t0_star_ns": t0, "trims_ns": trims, "cal": cal_pts}, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", trims)


def s75(t0, ton, t_end):
    """A181's S75 board at 25 C (its cfg_S75_25_p0, slow corner, L x 0.75, t_il 1.0 ns) with mode-S period t0."""
    c = json.loads((A181 / "cosim" / "cfg_S75_25_p0.json").read_text())
    assert c["circuit"]["L"] == L0 * 0.75 and c["gate"]["t_il_ns"] == T_IL and c["t0_ns"] == 400.0
    return dict(c, t0_ns=float(t0), ton_ns=float(ton), t_end_us=t_end)


def name(t0, ton):
    return f"t{t0}_n{ton:.3f}".replace(".", "p")


def screen():
    SCREEN.mkdir(exist_ok=True)
    order = []
    for t0, tons in SCREEN_TONS.items():
        for ton in tons:
            n = name(t0, ton)
            c = dict(s75(t0, ton, T_END_SCREEN), out=f"run_{n}.json",
                     note=f"A183 stage 1: S75 board (slow corner, L x 0.75) at 25 C, mode-S period {t0} ns, ton {ton} ns, "
                          f"start-up to {T_END_SCREEN} us")
            (SCREEN / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(n)
    (SCREEN / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "screen cfgs")


def extra(t0):
    st = json.loads((HERE / "a183_screen.json").read_text())
    pts = sorted(((s["ton_ns"], s["vo_143_5"]) for s in st.values() if s["t0_ns"] == t0), key=lambda p: abs(p[1] - VO_TGT))
    (a, va), (b, vb) = pts[:2]
    assert not (min(va, vb) <= VO_TGT <= max(va, vb)) or len(pts) < 2, "already bracketed"
    ton = a + (VO_TGT - va) * (b - a) / (vb - va)
    order = (SCREEN / "ORDER.txt").read_text().split()
    for t in (round(ton - 0.3, 3), round(ton + 0.3, 3)):
        n = name(t0, t)
        c = dict(s75(t0, t, T_END_SCREEN), out=f"run_{n}.json",
                 note=f"A183 stage 1 extra pair: S75 board at 25 C, mode-S period {t0} ns, ton {t} ns (slope estimate {ton:.3f})")
        (SCREEN / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(n)
        print("extra", n)
    (SCREEN / "ORDER.txt").write_text("\n".join(order) + "\n")


if __name__ == "__main__":
    {"screen": screen, "extra": lambda: extra(int(sys.argv[2])), "cal": cal, "calx": lambda: calx(sys.argv[2]),
     "main": main}[sys.argv[1]]()
