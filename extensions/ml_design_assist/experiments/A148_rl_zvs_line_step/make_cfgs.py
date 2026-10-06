"""A148 cosim cfgs: the frozen single-module design (A143's K 4 cfgs) with cfg vff "vs_g" (phase 1's low-side edge
offset, the volt-second law, scb_vff lo_add).
id_l_p48_1us: A143's cfg unchanged (option off), the bit-identity check;
v075_<row>: g 0.75 (criterion 1's candidate) on the 8 rows at L0, l_p48_1us and s_p62 at L x 0.7 / 1.3 (s070 / s130);
v075_e72_l<L>_<row>: A145's loop + edges (72 A/ns, Q 7) at 50 / 100 pH, rows l_p48_1us and s_p62 (off = A145's runs);
o_ / v075_e72_l<L>_l_m48_1us: the falling step with loop + edges, option off and on (no earlier record);
v100_*: post hoc g 1.0 arm (rising rows and s_p62 at L0, l_p48_1us with loop + edges).
Writes cosim/cfg_*.json and cosim/ORDER.txt (longest first)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parents[3] / "experiments" / "track_A_periodic_steady_state"
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
A144C = TA / "A144_p24_commutation_loop_inductance" / "cosim"
A145C = TA / "A145_p24_finite_switching_edges" / "cosim"
ROWS = ("n0", "l_p48_1us", "l_p48_5us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62")
LS = (50, 100)


def a143(row, s="s100"):
    name = "g3_s100_n0_k4" if row == "n0" else f"g4_{s}_{row}_k4"
    return json.loads((A143C / f"cfg_{name}.json").read_text())


def with_vs(base, g):
    return dict(base, vff=dict(base["vff"], vs_g=g))


def looped(base, l):
    """A143 cfg + A144's Q 7 loop at l pH + vds_win + A145's 72 A/ns edges."""
    q = json.loads((A144C / f"cfg_q7_l{l}_n0.json").read_text())
    return dict(base, loop=q["loop"], vds_win=1, edge={"didt_a_ns": 72.0})


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        c = dict(cfg, out=f"run_{name}.json", note=f"A148 {name}: {note}")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    for l in sorted(LS, reverse=True):                 # loop + edges first: the longest runs
        for r in ("l_p48_1us", "s_p62"):
            put(f"v075_e72_l{l}_{r}", with_vs(json.loads((A145C / f"cfg_e72_l{l}_{r}.json").read_text()), 0.75),
                f"A145 e72_l{l}_{r} + vs_g 0.75")
        put(f"o_e72_l{l}_l_m48_1us", looped(a143("l_m48_1us"), l), f"A143 l_m48_1us + loop {l} pH Q 7 + edges 72 A/ns")
        put(f"v075_e72_l{l}_l_m48_1us", with_vs(looped(a143("l_m48_1us"), l), 0.75), "the same + vs_g 0.75")
        put(f"v100_e72_l{l}_l_p48_1us", with_vs(json.loads((A145C / f"cfg_e72_l{l}_l_p48_1us.json").read_text()), 1.0),
            f"post hoc: A145 e72_l{l}_l_p48_1us + vs_g 1.0")
    for r in ROWS:
        put(f"v075_{r}", with_vs(a143(r), 0.75), f"A143 {r} (K 4, L0) + vs_g 0.75")
    for s in ("s070", "s130"):
        for r in ("l_p48_1us", "s_p62"):
            put(f"v075_{s}_{r}", with_vs(a143(r, s), 0.75), f"A143 g4_{s}_{r}_k4 + vs_g 0.75")
    for r in ("l_p48_1us", "l_p48_5us", "s_p62"):
        put(f"v100_{r}", with_vs(a143(r), 1.0), f"post hoc: A143 {r} + vs_g 1.0")
    put("id_l_p48_1us", a143("l_p48_1us"), "A143 g4_s100_l_p48_1us_k4 unchanged (option off): identity")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
