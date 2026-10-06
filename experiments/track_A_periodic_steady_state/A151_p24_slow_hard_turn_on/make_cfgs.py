"""A151 cosim cfgs from A145's 72 A/ns loop + edge cfgs (frozen controller, loop Q 7), turn-off kept at 72 A/ns:
on<d>_l<L>_<row>: edge didt_on_a_ns d (36 / 18 at 50 pH, 36 / 18 / 9 at 100 pH, 18 / 9 at 150 pH);
rows l_p48_1us, n0, s_p62 (150 pH: l_p48_1us, n0);
s5_l<L>_l_p48: the unchanged 72 / 72 A/ns design on +4.8 V / 5 us at 50 / 100 pH (the bus-slew lever).
Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A145C = HERE.parent / "A145_p24_finite_switching_edges" / "cosim"
PLAN = {50: ((36, 18), ("l_p48_1us", "n0", "s_p62")), 100: ((36, 18, 9), ("l_p48_1us", "n0", "s_p62")),
        150: ((18, 9), ("l_p48_1us", "n0"))}


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A151 {name}: {note}"),
                                                         indent=1) + "\n")
        order.append(name)
    for l, (ds, rows) in PLAN.items():
        for row in rows:
            base = json.loads((A145C / f"cfg_e72_l{l}_{row}.json").read_text())
            for d in ds:
                put(f"on{d}_l{l}_{row}", dict(base, edge=dict(base["edge"], didt_on_a_ns=float(d))),
                    f"A145 e72_l{l}_{row}, turn-on {d} A/ns (turn-off 72)")
    for l in (50, 100):
        base = json.loads((A145C / f"cfg_e72_l{l}_l_p48_1us.json").read_text())
        put(f"s5_l{l}_l_p48", dict(base, line_step=dict(base["line_step"], slew_us=5.0)),
            f"A145 e72_l{l}_l_p48_1us with the step over 5 us")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
