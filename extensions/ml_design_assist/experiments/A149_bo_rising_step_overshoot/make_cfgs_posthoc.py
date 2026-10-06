"""A149 post hoc cosim cfgs (added after criterion 2 failed, before any cosim; BOUNDARY addendum): the two D63 grid
points nearest to criterion 2 that the existing RTL runs (A148's scb_vff lo_add with vs_kt = 0, i.e. the rail term
alone: Vin features only, zero at constant Vin):
r100_<row>: gr 1.0 (vs_kr 1311), rows l_p48_1us / l_p48_5us at L0, l_p48_1us at L x 0.7 / 1.3 (A143 K 4 cfgs);
r100_e72_l<L>_l_p48_1us: the same on A145's 72 A/ns loop + edge cfgs at 50 / 100 pH;
r075_*: gr 0.75 (vs_kr 983), the four loop-free rows and 50 pH loop + edges.
Writes cosim/cfg_*.json and cosim/ORDER.txt (longest first)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parents[3] / "experiments" / "track_A_periodic_steady_state"
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
A145C = TA / "A145_p24_finite_switching_edges" / "cosim"
ARMS = {"r100": 1.0, "r075": 0.75}
KVS = 2 ** 24 * 0.02 / 256                       # vs_kr per unit gain (bridge: g 2^24 vin_lsb / (256 Vo))


def with_kr(base, gr):
    return dict(base, vff=dict(base["vff"], vs_kr=round(gr * KVS), vs_kt=0))


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        c = dict(cfg, out=f"run_{name}.json", note=f"A149 post hoc {name}: {note}")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    for arm, gr in ARMS.items():
        for l in ((50, 100) if arm == "r100" else (50,)):
            put(f"{arm}_e72_l{l}_l_p48_1us", with_kr(json.loads((A145C / f"cfg_e72_l{l}_l_p48_1us.json").read_text()), gr),
                f"A145 e72_l{l}_l_p48_1us + vs_kr {round(gr * KVS)} (gr {gr}), vs_kt 0")
    for arm, gr in ARMS.items():
        for s, row in (("s100", "l_p48_1us"), ("s100", "l_p48_5us"), ("s070", "l_p48_1us"), ("s130", "l_p48_1us")):
            tag = row if s == "s100" else f"{s}_{row}"
            put(f"{arm}_{tag}", with_kr(json.loads((A143C / f"cfg_g4_{s}_{row}_k4.json").read_text()), gr),
                f"A143 g4_{s}_{row}_k4 + vs_kr {round(gr * KVS)} (gr {gr}), vs_kt 0")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
