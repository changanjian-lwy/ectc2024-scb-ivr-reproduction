"""A157 cosim cfgs: the drive spec under weaker loop damping. A152's s100_l_p48_1us cfg (frozen design, +4.8 V / 1 us at
1000 us, vds_win) at loop L / turn-on d_on / turn-off 72 A/ns with the loop's parallel damper set for ring Q (q_rp) or
removed (Q 0 = rp 0, undamped; A144's undamped runs with instantaneous edges lost the valley tracking), start-up ton by
A155's law. Rows q<Q>_s<L>. Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
from a144_edge import q_rp  # noqa: E402

ROWS = ((15, 50, 36.0), (30, 50, 36.0), (0, 50, 36.0), (0, 100, 18.0), (0, 125, 24.0))     # (Q, pH, turn-on A/ns)


def ton_law(l, d_on, d_off=72.0):
    f = json.loads((TA / "A155_p24_startup_ton_law" / "a155_fit.json").read_text())
    return round(35.5 + (1.015 - f["c0"] + f["a"] * d_on ** -0.5 + f["b"] * l * 1e-3 - f["c"] * d_off ** -0.5) / f["s"], 3)


def main():
    COS.mkdir(exist_ok=True)
    line = json.loads((TA / "A152_p24_drive_spec_robustness" / "cosim" / "cfg_s100_l_p48_1us.json").read_text())
    order = []
    for q, l, d in ROWS:
        rp = round(q_rp(l * 1e-12, q), 4) if q else 0.0
        name, ton = f"q{q}_s{l}", ton_law(l, d)
        cfg = dict(line, ton_ns=ton, loop={"l_ph": float(l), "rp_ohm": rp}, edge={"didt_a_ns": 72.0, "didt_on_a_ns": d},
                   out=f"run_{name}.json", note=f"A157 {name}: A152 s100_l_p48_1us at {l} pH, ring Q {q or 'undamped'} (rp {rp}), "
                   f"turn-on {d:g} / off 72 A/ns, ton {ton} ns")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(" ".join(order))


if __name__ == "__main__":
    main()
