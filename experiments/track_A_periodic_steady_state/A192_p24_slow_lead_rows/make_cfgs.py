"""A192 cosim cfgs: the slow corner's other rows with the 9.5 ns lead (A191) and the adopted start-up (A188: 200 ns mode
S at its own trim, bumpless seed, handover at Vo >= 1.045 V or 144 us). Steps at 500 us + k T / 3 (A179's positions,
T = 0.5048 us x L scale), end + 400 us, t_il 1.0 ns.
- S0 (slow L0) 25 C: -8 V / 10 us and +62.5 A load step at k = 0, 1, 2 (A179's t_il 1.0 ns runs are the 8 ns
  references); -4.8 V / 1 us and +4.8 V / 1 us at k = 0.
- S0 125 C: +4.8 V / 1 us and -8 V / 10 us at k = 0.
- S75 (slow L x 0.75) 25 C: +4.8 V / 1 us at k = 0, 1, 2.
- four slow modules 25 C (A173's m4_ss cfg): +4.8 V / 1 us at 500 us.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A186 = TA / "A186_p24_vo_triggered_handover" / "cosim"
SEEDS = json.loads((TA / "A185_p24_bumpless_loop_seed" / "seeds.json").read_text())
TRIMS = json.loads((TA / "A183_p24_startup_period_ladder" / "trims.json").read_text())["trims_ns"]
COS = HERE / "cosim"
LEAD, HAND_VO, T0_US, POST, PER0 = 9.5, 1.045, 500.0, 400.0, 0.5048
ROWS = {"p48_1us": {"line_step": {"dv": 4.8, "slew_us": 1.0}}, "m48_1us": {"line_step": {"dv": -4.8, "slew_us": 1.0}},
        "m80_10us": {"line_step": {"dv": -8.0, "slew_us": 10.0}}, "s_p62": {"load_step": {"i_a": 62.5}}}
RUNS = [("S0", 25.0, "m80_10us", (0, 1, 2)), ("S0", 25.0, "s_p62", (0, 1, 2)), ("S0", 25.0, "m48_1us", (0,)),
        ("S0", 25.0, "p48_1us", (0,)), ("S0", 125.0, "p48_1us", (0,)), ("S0", 125.0, "m80_10us", (0,)),
        ("S75", 25.0, "p48_1us", (0, 1, 2))]


def with_row(c, row, t):
    c = {k: v for k, v in c.items() if k not in ("line_step", "load_step")}
    (key, val), = ROWS[row].items()
    return dict(c, **{key: dict(val, t_us=t)}, t_end_us=round(t + POST, 4))


def single(b, temp, row, k):
    c = json.loads((A186 / f"cfg_{b}_25_p0.json").read_text())
    sc = c["circuit"]["L"] / 2.9333333199999997e-09
    t = round(T0_US + k / 3 * PER0 * sc, 4)
    g = dict(c["gate"])
    if temp != 25.0:
        g["temp"] = temp
    return with_row(dict(c, gate=g, hand_vo_v=HAND_VO, driver=dict(c["driver"], hs_on_lead_ns=LEAD)), row, t)


def m4():
    c = json.loads((TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_m4_ss_l_p48_1us.json").read_text())
    assert c["modules"] == 4 and c["ton_ns"] == 48.348
    c = dict(c, t0_ns=200.0, ton_s_ns=TRIMS["S0"], ton_ns=SEEDS["S0"]["seed_ns"], hand_vo_v=HAND_VO,
             gate=dict(c["gate"], t_il_ns=1.0), driver=dict(c["driver"], hs_on_lead_ns=LEAD))
    return with_row(c, "p48_1us", T0_US)


def main():
    COS.mkdir(exist_ok=True)
    order = ["M4ss_25_p48_1us_p0"]
    c = dict(m4(), out=f"run_{order[0]}.json", note=f"A192 {order[0]}: four slow modules, adopted start-up, lead {LEAD} ns, +4.8 V / 1 us at 500 us")
    (COS / f"cfg_{order[0]}.json").write_text(json.dumps(c, indent=1) + "\n")
    for b, temp, row, ks in RUNS:
        for k in ks:
            name = f"{b}_{'hot' if temp != 25.0 else '25'}_{row}_p{k}"
            c = dict(single(b, temp, row, k), out=f"run_{name}.json",
                     note=f"A192 {name}: slow board {b}, {temp:g} C, adopted start-up, lead {LEAD} ns, row {row}, step position k = {k}")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
