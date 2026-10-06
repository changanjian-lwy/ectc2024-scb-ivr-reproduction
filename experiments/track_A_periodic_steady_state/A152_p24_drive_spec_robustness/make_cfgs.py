"""A152 cosim cfgs: A151's drive spec (turn-off 72 A/ns, slow turn-on, loop Q 7) plus a start-up Ton compensation
(ton_ns 35.5 + about 36 A / turn-on di/dt: the hard turn-ons of mode S lose that much on-time) on rows A151 did not test.
Each cfg = its ideal-plant frozen-design reference cfg + loop + edge + vds_win + ton_ns (A145 = A143 + the first three
keys exactly), so a row and its reference differ only in the package and its drive.
  s<L>_<row>: spec point S50 (50 pH, 36 A/ns, ton 36.5 ns) or S100 (100 pH, 18 A/ns, ton 37.5 ns) on ROWS
              (references A143 g4_*_k4; slew rows A150 c00_slew*, whose vs_kr / vs_kt 0 keys are the off path; slew5 A143);
  big300_on<d>: loop 300 pH at Q 7, turn-on d A/ns (72 = no fix, ton 35.5; 18 -> 37.5; 9 -> 39.5), row l_p48_1us;
  m4_s<L>_l_p48_1us: four modules (frozen C12 + lo_learn 4, ref A143 g5_l_p48_1us_k4), loop and drive on every module.
Writes cosim/cfg_*.json and cosim/ORDER.txt (longest runs first)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
sys.path.insert(0, str(TA / "A145_p24_finite_switching_edges"))
import a145_edge as E  # noqa: E402

A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
SPEC = {50: (0.8224, 36.0, 36.5), 100: (1.163, 18.0, 37.5)}   # l_ph pH: (rp Ohm at Q 7 as A145, turn-on A/ns, ton_ns)
ROWS = {"l_p48_1us": "g4_s100_l_p48_1us_k4", "s_p62": "g4_s100_s_p62_k4",
        "l_m48_1us": "g4_s100_l_m48_1us_k4", "l_m80_10us": "g4_s100_l_m80_10us_k4",
        "L07_l_p48_1us": "g4_s070_l_p48_1us_k4", "L07_s_p62": "g4_s070_s_p62_k4",
        "L13_l_p48_1us": "g4_s130_l_p48_1us_k4", "L13_s_p62": "g4_s130_s_p62_k4",
        "slew2": "g4_s100_l_p48_1us_k4", "slew3": "g4_s100_l_p48_1us_k4", "slew4": "g4_s100_l_p48_1us_k4",
        "slew5": "g4_s100_l_p48_5us_k4", "slew10": "g4_s100_l_p48_1us_k4"}
BIG = ((72.0, 35.5), (18.0, 37.5), (9.0, 39.5))                # 300 pH: (turn-on A/ns, ton_ns)


def package(cfg, l_ph, rp, d_on, ton):
    return dict(cfg, vds_win=1, ton_ns=ton, loop={"l_ph": float(l_ph), "rp_ohm": rp},
                edge={"didt_a_ns": 72.0} if d_on == 72.0 else {"didt_a_ns": 72.0, "didt_on_a_ns": d_on})


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A152 {name}: {note}"),
                                                         indent=1) + "\n")
        order.append(name)
    m4 = json.loads((A143C / "cfg_g5_l_p48_1us_k4.json").read_text())
    for l, s in SPEC.items():
        put(f"m4_s{l}_l_p48_1us", package(m4, l, *s), f"four modules (A143 g5_l_p48_1us_k4), {l} pH, turn-on {s[1]:g} A/ns, "
            f"ton {s[2]} ns")
    base = json.loads((A143C / "cfg_g4_s100_l_p48_1us_k4.json").read_text())
    rp = round(E.q_rp(300e-12, 7), 3)
    for d, ton in BIG:
        put(f"big300_on{d:g}", package(base, 300, rp, d, ton),
            f"A143 l_p48_1us, loop 300 pH Q 7 (rp {rp}), turn-on {d:g} A/ns, ton {ton} ns")
    for l, s in SPEC.items():
        for row, ref in ROWS.items():
            cfg = json.loads((A143C / f"cfg_{ref}.json").read_text())
            if row.startswith("slew") and row != "slew5":
                cfg = dict(cfg, line_step=dict(cfg["line_step"], slew_us=float(row[4:])))
            put(f"s{l}_{row}", package(cfg, l, *s), f"A143 {ref}, loop {l} pH Q 7, turn-on {s[1]:g} A/ns, ton {s[2]} ns")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
