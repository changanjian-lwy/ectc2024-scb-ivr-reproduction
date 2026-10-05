"""A144 cosim cfgs: the frozen single-module design (A143's K 4 cfgs: A141 F + lo_learn 4) at L x 1.0 on n0, l_p48_1us
and s_p62, with cfg "loop" (A144: l_ph pH in series with every high-side switch) and "vds_win" 1 (windowed V_DS peaks).
b_<row>: loop off (identity with A143's records + the V_DS baseline); q7_l<L>_<row>: L 50 / 100 / 150 / 300 pH with
the parallel damping of quality factor 7 (a144_edge.q_rp: R = 7 sqrt(L / (2 Coss(12 V)))); u_l<L>_l_p48_1us: L 150 /
300 pH undamped. Writes cosim/cfg_*.json and cosim/ORDER.txt (longest first)."""
from __future__ import annotations

import json
from pathlib import Path

from a144_edge import q_rp

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A143C = HERE.parent / "A143_p24_short_comparator_phase" / "cosim"
ROWS = {"n0": "cfg_g3_s100_n0_k4.json", "l_p48_1us": "cfg_g4_s100_l_p48_1us_k4.json", "s_p62": "cfg_g4_s100_s_p62_k4.json"}
LS = (50, 100, 150, 300)
Q = 7.0


def main():
    COS.mkdir(exist_ok=True)
    order = []
    def put(name, base, note, loop=None):
        c = dict(base, vds_win=1, out=f"run_{name}.json", note=f"A144 {name}: {note}")
        if loop:
            c["loop"] = loop
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    base = {r: json.loads((A143C / f).read_text()) for r, f in ROWS.items()}
    for l in (300, 150):
        put(f"u_l{l}_l_p48_1us", base["l_p48_1us"], f"frozen design, loop {l} pH undamped", {"l_ph": float(l), "rp_ohm": 0.0})
    for l in sorted(LS, reverse=True):
        rp = round(q_rp(l * 1e-12, Q), 4)
        for r in ROWS:
            put(f"q7_l{l}_{r}", base[r], f"frozen design, loop {l} pH, Q 7 ({rp} Ohm across)", {"l_ph": float(l), "rp_ohm": rp})
    for r in ROWS:
        put(f"b_{r}", base[r], "frozen design, loop off (A143 record + windowed V_DS)")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
