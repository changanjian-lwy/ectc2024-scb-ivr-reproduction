"""A154 cosim cfgs: the turn-off side for loops above 150 pH. A152's s100_l_p48_1us cfg (frozen design, +4.8 V / 1 us at
1000 us, Q 7, vds_win) at loop L with turn-off di/dt d_off and turn-on d_on = X_ON / L (D68's rule with margin), start-up
ton by D68's law. f<L>_off<d_off>: x_off = L * d_off = 9.6 / 10.0 / 9.6 / 7.2 / 14.4 V.
Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
from a144_edge import q_rp  # noqa: E402

K = 15.6                     # D68 start-up law, ns (A/ns)^1/2 (referred to a 72 A/ns turn-off; see BOUNDARY)
X_ON = 2.4                   # V: turn-on L * di/dt, below D68's x* 3.2 V
ROWS = ((200, 48.0), (250, 40.0), (300, 32.0), (300, 24.0), (300, 48.0))


def d_on(l):
    return round(X_ON / (l * 1e-3), 2)


def ton_s(d):
    return round(35.5 + K * (d ** -0.5 - 72.0 ** -0.5), 3)


def main():
    COS.mkdir(exist_ok=True)
    order = []
    line = json.loads((TA / "A152_p24_drive_spec_robustness" / "cosim" / "cfg_s100_l_p48_1us.json").read_text())
    for l, doff in ROWS:
        rp, don = round(q_rp(l * 1e-12, 7), 4), d_on(l)
        name = f"f{l}_off{doff:g}"
        cfg = dict(line, ton_ns=ton_s(don), loop={"l_ph": float(l), "rp_ohm": rp}, edge={"didt_a_ns": doff, "didt_on_a_ns": don},
                   out=f"run_{name}.json", note=f"A154 {name}: A152 s100_l_p48_1us at loop {l} pH (rp {rp}), turn-off {doff:g} "
                   f"A/ns, turn-on {don:g} A/ns, ton {ton_s(don)} ns")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs:", " ".join(order))


if __name__ == "__main__":
    main()
