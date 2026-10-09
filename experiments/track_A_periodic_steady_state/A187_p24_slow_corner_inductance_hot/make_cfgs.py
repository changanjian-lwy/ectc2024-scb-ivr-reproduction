"""A187 cosim cfgs: the slow corner's inductance at 125 C after +4.8 V / 1 us, over six step positions, with the
start-up of A186 (200 ns mode S at its own trim, bumpless loop seed, handover requested at Vo 1.03 V).
Boards: S75 (slow, L x 0.75; A183 trim 35.451 ns, A185 seed 45.355 ns) and S80 (slow, L x 0.8; trim from three 25 C
start-ups here, seed = T_ss + (kp + ki)(1.032 V - vref) with T_ss interpolated in L between S75 (32.306 ns) and S0
(40.984 ns), A185 seeds.json). Base: A186's S75 125 C cfg. Steps at 500 us + k T / 6, T = 0.5048 us x L scale,
end + 400 us.
  python3 make_cfgs.py cal    cosim_cal/cfg_S80_n<ton>.json: 150 us start-ups at 25 C, 35.0 / 35.5 / 36.0 ns
  python3 make_cfgs.py        trims.json, cosim/cfg_<board>_hot_p<k>.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
BASE = TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_S75_hot_p0.json"
SEEDS = json.loads((TA / "A185_p24_bumpless_loop_seed" / "seeds.json").read_text())
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
L0, PER0, T_STEP0, POST_US, NPOS = 2.9333333199999997e-09, 0.5048, 500.0, 400.0, 6
KPI, VO_SEED, VO_TGT = 377.9084, 1.032, 1.035
CAL_TONS = (35.0, 35.5, 36.0)


def base(scale, ton_s, seed, temp, t_step, t_end):
    c = json.loads(BASE.read_text())
    assert c["gate"]["temp"] == 125.0 and c["hand_vo_v"] == 1.03 and c["circuit"]["L"] == L0 * 0.75
    g = dict(c["gate"])
    if temp == 25.0:
        g.pop("temp")
    else:
        g["temp"] = temp
    return dict(c, circuit=dict(c["circuit"], L=L0 * scale), gate=g, ton_s_ns=ton_s, ton_ns=seed,
                line_step=dict(c["line_step"], t_us=t_step), t_end_us=t_end)


def cal():
    CAL.mkdir(exist_ok=True)
    for ton in CAL_TONS:
        n = f"S80_n{ton:.3f}".replace(".", "p")
        c = dict(base(0.8, ton, 46.0, 25.0, T_STEP0, 150.0), hand_vo_v=None, out=f"run_{n}.json",
                 note=f"A187 trim start-up: slow corner, L x 0.8, 25 C, mode-S period 200 ns, ton_s {ton} ns, to 150 us")
        c.pop("hand_vo_v")                                        # trim start-ups hand over at 144 us, as A183's
        (CAL / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(CAL_TONS), "cal cfgs")


def s80_trim():
    pts = []
    for f in sorted(CAL.glob("run_S80_n*.json")):
        r = json.loads(f.read_text())
        pts.append((r["cfg"]["ton_s_ns"], float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))))
    lo = max((p for p in pts if p[1] <= VO_TGT), key=lambda p: p[1])
    hi = min((p for p in pts if p[1] >= VO_TGT), key=lambda p: p[1])
    return round(lo[0] + (VO_TGT - lo[1]) * (hi[0] - lo[0]) / (hi[1] - lo[1]), 3), pts


def main():
    t80, pts = s80_trim()
    tss80 = SEEDS["S75"]["t_ss_ns"] + (SEEDS["S0"]["t_ss_ns"] - SEEDS["S75"]["t_ss_ns"]) * (0.80 - 0.75) / (1.0 - 0.75)
    boards = {"S75": (0.75, 35.451, SEEDS["S75"]["seed_ns"]), "S80": (0.80, t80, round(tss80 + KPI * (VO_SEED - 1.0), 3))}
    COS.mkdir(exist_ok=True)
    order = []
    for b, (sc, ton_s, seed) in boards.items():
        for k in range(NPOS):
            t = round(T_STEP0 + k / NPOS * PER0 * sc, 4)
            run = f"{b}_hot_p{k}"
            c = dict(base(sc, ton_s, seed, 125.0, t, round(t + POST_US, 4)), out=f"run_{run}.json",
                     note=f"A187 {run}: slow corner, L x {sc}, 125 C, mode-S period 200 ns at {ton_s} ns, seed {seed} ns (set at "
                          f"25 C, locked), handover at Vo 1.03 V, +4.8 V / 1 us at {t} us")
            (COS / f"cfg_{run}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(run)
    (HERE / "trims.json").write_text(json.dumps({"boards": boards, "s80_cal": pts, "s80_t_ss_interp_ns": tss80}, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs", boards)


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
