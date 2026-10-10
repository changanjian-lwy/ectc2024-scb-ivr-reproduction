"""A190 cosim cfgs: A188's start-up below 25 C with a temperature-compensated mode-S trim,
ton_s(T) = ton_s(25 C) + DT[corner][T]. DT = -(Vo(T) - Vo(25 C)) / slope, taken from the fitting boards only: slow
from S75 (A185 / A189), nominal from N0. Slopes at 25 C, t0 200: slow 0.0545 V/ns (A183 S75 pair), nominal 0.0535
(A183 N0 trim start-ups). The corner is read from the 25 C trim (slow ~35.5, nominal ~23.7 ns). Hold-out boards: S0,
S80 (slow), N13, N75 (nominal); S75 and N0 are the in-sample checks. Seeds stay at their 25 C values. Start-ups to
200 us at 0 and -40 C.
  python3 make_cfgs.py   table.json, cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A185, A189, A186 = TA / "A185_p24_bumpless_loop_seed", TA / "A189_p24_cold_startup", TA / "A186_p24_vo_triggered_handover"
COS = HERE / "cosim"
L0 = 2.9333333199999997e-09
TEMPS = {"c0": 0.0, "m40": -40.0}
SLOPE = {"slow": 0.0545, "nominal": 0.0535}


def vo(path):
    r = json.loads(Path(path).read_text())
    return float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))


def table():
    out = {}
    for corner, b in (("slow", "S75"), ("nominal", "N0")):
        v25 = vo(A185 / "cosim" / f"run_{b}_25_p0.json")
        out[corner] = {k: round(-(vo(A189 / "cosim" / f"run_{b}_{k}.json") - v25) / SLOPE[corner], 3) for k in TEMPS}
    return out


def base(b):
    if b == "S80":                                               # A187's S80 board on A189's S75 cold cfg
        c = json.loads((A189 / "cosim" / "cfg_S75_c0.json").read_text())
        t = json.loads((TA / "A187_p24_slow_corner_inductance_hot" / "trims.json").read_text())["boards"]["S80"]
        return dict(c, circuit=dict(c["circuit"], L=L0 * 0.8), ton_s_ns=t[1], ton_ns=t[2]), "slow"
    src = A189 / "cosim" / f"cfg_{b}_c0.json"
    c = json.loads((src if src.exists() else A186 / "cosim" / f"cfg_{b}_25_p0.json").read_text())
    return dict(c, hand_vo_v=1.045, t_end_us=200.0), ("slow" if b in ("S75", "S0") else "nominal")


def main():
    dt = table()
    (HERE / "table.json").write_text(json.dumps({"dton_ns": dt, "slope_v_per_ns": SLOPE}, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []
    for b in ("S0", "S80", "N13", "N75", "S75", "N0"):
        c, corner = base(b)
        for k, temp in TEMPS.items():
            if b == "N13" and k == "c0":
                continue                                          # N13 passed uncompensated at 0 C with margin
            ton_s = round(c["ton_s_ns"] + dt[corner][k], 3)
            run = f"{b}_{k}"
            cc = dict(c, gate=dict(c["gate"], temp=temp), ton_s_ns=ton_s, t_end_us=200.0, out=f"run_{run}.json",
                      note=f"A190 {run}: A188 start-up at {temp:g} C, mode-S trim {c['ton_s_ns']} + {dt[corner][k]} ns ({corner} table), "
                           f"seed {c['ton_ns']} ns, request 1.045 V, to 200 us")
            (COS / f"cfg_{run}.json").write_text(json.dumps(cc, indent=1) + "\n")
            order.append(run)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs", dt)


if __name__ == "__main__":
    main()
