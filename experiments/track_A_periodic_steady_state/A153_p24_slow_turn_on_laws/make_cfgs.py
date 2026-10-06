"""A153 cosim cfgs: D68's two laws tested at turn-on di/dt and loop inductances no run has used.
  u<d>_l100: start-up only (300 us), A151's n0 cfg at 100 pH with turn-on d = 24 / 12 / 6 A/ns, ton 35.5 ns
             (D68 Section 3: Vo before the handover against the sqrt law);
  v<L>_on<d>: A152's s100_l_p48_1us cfg (frozen design, +4.8 V / 1 us at 1000 us, turn-off 72 A/ns, Q 7, vds_win)
             at loop L / turn-on d with D68's start-up ton (D68 Section 4: x = L * d = 3.0 / 3.0 / 4.0 / 1.8 V).
Writes cosim/cfg_*.json and cosim/ORDER.txt (longest runs first)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
from a144_edge import q_rp  # noqa: E402

K = 15.6                                        # D68: t_lost(d) - t_lost(72) = K (d^-1/2 - 72^-1/2), ns (A/ns)^1/2
UP = (24.0, 12.0, 6.0)
VROWS = ((75, 40.0), (125, 24.0), (125, 32.0), (75, 24.0))


def ton_s(d):
    return round(35.5 + K * (d ** -0.5 - 72.0 ** -0.5), 3)


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A153 {name}: {note}"),
                                                         indent=1) + "\n")
        order.append(name)
    line = json.loads((TA / "A152_p24_drive_spec_robustness" / "cosim" / "cfg_s100_l_p48_1us.json").read_text())
    for l, d in VROWS:
        rp = round(q_rp(l * 1e-12, 7), 4)
        cfg = dict(line, ton_ns=ton_s(d), loop={"l_ph": float(l), "rp_ohm": rp}, edge={"didt_a_ns": 72.0, "didt_on_a_ns": d})
        put(f"v{l}_on{d:g}", cfg, f"A152 s100_l_p48_1us at loop {l} pH (rp {rp}), turn-on {d:g} A/ns, ton {ton_s(d)} ns (D68)")
    n0 = json.loads((TA / "A151_p24_slow_hard_turn_on" / "cosim" / "cfg_on18_l100_n0.json").read_text())
    for d in UP:
        put(f"u{d:02.0f}_l100", dict(n0, t_end_us=300.0, edge={"didt_a_ns": 72.0, "didt_on_a_ns": d}),
            f"A151 on18_l100_n0 with turn-on {d:g} A/ns, ton 35.5 ns, start-up only (300 us)")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs:", " ".join(order))


if __name__ == "__main__":
    main()
