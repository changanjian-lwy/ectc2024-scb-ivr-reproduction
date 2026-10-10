"""A193 cosim cfgs: S75 (slow L x 0.75) below 25 C after +4.8 V / 1 us, with the slow boards' 9.5 ns lead and the
8 ns reference. Base: A190's cold start-up cfgs (A188 start-up, cold trim table, t_il 1.0 ns). Steps at
500 us + k T / 3 (k = 0, 1, 2; T = 0.5048 us x L scale), end + 400 us.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A190 = HERE.parent / "A190_p24_cold_trim_compensation" / "cosim"
COS = HERE / "cosim"
T0_US, POST, PER0 = 500.0, 400.0, 0.5048
RUNS = [("m40", 9.5), ("c0", 9.5), ("m40", 8.0)]


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for temp, lead in RUNS:
        c = json.loads((A190 / f"cfg_S75_{temp}.json").read_text())
        sc = c["circuit"]["L"] / 2.9333333199999997e-09
        for k in (0, 1, 2):
            t = round(T0_US + k / 3 * PER0 * sc, 4)
            name = f"S75_{temp}_l{lead:g}".replace(".", "p") + f"_p{k}"
            cfg = dict(c, line_step={"dv": 4.8, "slew_us": 1.0, "t_us": t}, t_end_us=round(t + POST, 4),
                       driver=dict(c["driver"], hs_on_lead_ns=lead), out=f"run_{name}.json",
                       note=f"A193 {name}: S75, {c['gate']['temp']:g} C, A188 start-up + A190 cold trim, lead {lead:g} ns, "
                            f"+4.8 V / 1 us at {t} us (k = {k})")
            (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
