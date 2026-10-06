"""A155 cosim cfgs, start-up only (300 us): A151's on18_l100_n0 cfg (frozen design, n0, Q 7) at loop L, turn-on d_on,
turn-off d_off, with the start-up ton from a155_fit.json for V_T = 1.015 V (rows s<L>), and the control c300 with
D68's ton (no L or turn-off term). Combinations never run before. Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
from a144_edge import q_rp  # noqa: E402

V_T = 1.015
ROWS = ((175, 18.0, 56.0), (200, 16.0, 50.0), (250, 12.8, 36.0), (300, 10.0, 30.0))   # (pH, d_on, d_off)


def ton_fit(l, d_on, d_off, f=None):
    f = f or json.loads((HERE / "a155_fit.json").read_text())
    return round(35.5 + (V_T - f["c0"] + f["a"] * d_on ** -0.5 + f["b"] * l * 1e-3 - f["c"] * d_off ** -0.5) / f["s"], 3)


def ton_d68(d_on):
    return round(35.5 + 15.6 * (d_on ** -0.5 - 72.0 ** -0.5), 3)


def main():
    COS.mkdir(exist_ok=True)
    base = json.loads((TA / "A151_p24_slow_hard_turn_on" / "cosim" / "cfg_on18_l100_n0.json").read_text())
    order = []
    def put(name, l, d_on, d_off, ton, note):
        rp = round(q_rp(l * 1e-12, 7), 4)
        cfg = dict(base, t_end_us=300.0, ton_ns=ton, loop={"l_ph": float(l), "rp_ohm": rp},
                   edge={"didt_a_ns": d_off, "didt_on_a_ns": d_on}, out=f"run_{name}.json",
                   note=f"A155 {name}: n0 start-up, loop {l} pH (rp {rp}), turn-on {d_on:g} / turn-off {d_off:g} A/ns, ton {ton} ns ({note})")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    for l, don, doff in ROWS:
        put(f"s{l}", l, don, doff, ton_fit(l, don, doff), "a155 law")
    put("c300", 300, 10.0, 30.0, ton_d68(10.0), "control: D68's ton, no L / turn-off term")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(" ".join(order), [ton_fit(*r) for r in ROWS], ton_d68(10.0))


if __name__ == "__main__":
    main()
