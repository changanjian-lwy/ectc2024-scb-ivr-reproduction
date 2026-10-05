"""A145 cosim cfgs: A144's Q 7 cfgs (the frozen single-module design, A143's K 4 cfgs, + loop + vds_win 1) with
cfg "edge" (A145 finite switching edges, the same di/dt at turn-off and hard turn-on).
e<didt>_l<L>_<row>: didt 144 / 72 A/ns (143 A in 1 / 2 ns), loop 50 / 100 / 150 pH, rows n0, l_p48_1us, s_p62;
e<didt>_l0_n0: no loop (A144's b_n0 + edges), the edges' intrinsic loss;
id_<name>: A144's cfg unchanged (edges off), the bit-identity check against A144's record.
Writes cosim/cfg_*.json and cosim/ORDER.txt (longest first)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A144C = HERE.parent / "A144_p24_commutation_loop_inductance" / "cosim"
ROWS = ("n0", "l_p48_1us", "s_p62")
LS = (50, 100, 150)
DIDT = (72, 144)
IDENT = ("q7_l100_l_p48_1us", "q7_l50_n0")


def main():
    COS.mkdir(exist_ok=True)
    order = []
    def put(name, base, note):
        c = dict(base, out=f"run_{name}.json", note=f"A145 {name}: {note}")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    for d in DIDT:                                    # slower edges first: more Python edge steps
        for l in sorted(LS, reverse=True):
            for r in ROWS:
                base = json.loads((A144C / f"cfg_q7_l{l}_{r}.json").read_text())
                put(f"e{d}_l{l}_{r}", dict(base, edge={"didt_a_ns": float(d)}),
                    f"frozen design, loop {l} pH Q 7, edges {d} A/ns (143 A in {143 / d:.2f} ns)")
    for d in DIDT:
        put(f"e{d}_l0_n0", dict(json.loads((A144C / "cfg_b_n0.json").read_text()), edge={"didt_a_ns": float(d)}),
            f"frozen design, no loop, edges {d} A/ns")
    for nm in IDENT:
        put(f"id_{nm}", json.loads((A144C / f"cfg_{nm}.json").read_text()), f"A144 {nm} unchanged (edges off): identity")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
