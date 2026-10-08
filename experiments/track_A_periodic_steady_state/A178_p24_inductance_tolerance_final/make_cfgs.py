"""A178 cosim cfgs: where the final plant's 200 A budget holds in inductance. L x 0.75 and L x 0.8 boards (nominal
devices), each re-trimmed under the final plant, on +4.8 V / 1 us at five step phases (k T / 5, k = 0..4; T taken
proportional to L from the nominal 510.1 ns).
Base: A171's S50 nominal cfg (= A173's final() of A164's nominal row) with circuit L scaled; nothing else differs
between A143's L rows (checked).
  python3 make_cfgs.py cal   stage 1: cosim_cal/cfg_L<s>.json, start-up to 150 us at a first-guess trim interpolated
                             between A172's L x 0.7 (35.769 ns) and A164's L0 (39.615 ns)
  python3 make_cfgs.py       stage 2: trims.json (one shot, A164's slope) and cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
BASE = HERE.parent / "A171_p24_gate_interlock_threshold" / "cosim" / "cfg_S50_nom_l_p48_1us.json"
L0, T0 = 2.9333333199999997e-09, 0.5101          # nominal inductance (H), nominal steady period (us)
SCALES = (0.75, 0.8)
TON07, TON10 = 35.769, 39.615
VO_TGT, SLOPE = 1.035, 0.026


def tag(s):
    return f"L{int(round(s * 100)):03d}"


def board(s, ton):
    c = json.loads(BASE.read_text())
    return dict(c, circuit=dict(c["circuit"], L=L0 * s), ton_ns=ton)


def guess(s):
    return round(TON07 + (TON10 - TON07) * (s - 0.7) / 0.3, 3)


def check_identity():
    """board(0.7, A172's trim) is A172's L x 0.7 cfg key for key (out / note aside; L to 1e-12 relative)."""
    a = board(0.7, TON07)
    b = json.loads((HERE.parent / "A172_p24_final_gate_plant" / "cosim" / "cfg_nom_L07_l_p48_1us.json").read_text())
    assert abs(a["circuit"]["L"] / b["circuit"]["L"] - 1) < 1e-12
    a["circuit"] = b["circuit"]
    assert {k: v for k, v in a.items() if k not in ("out", "note")} == {k: v for k, v in b.items() if k not in ("out", "note")}


def cal():
    check_identity()
    CAL.mkdir(exist_ok=True)
    for s in SCALES:
        c = dict(board(s, guess(s)), t_end_us=150.0, out=f"run_{tag(s)}.json",
                 note=f"A178 stage 1: L x {s} board start-up under the final plant at ton {guess(s)} ns")
        (CAL / f"cfg_{tag(s)}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(SCALES), "cal cfgs")


def main():
    COS.mkdir(exist_ok=True)
    tr, order = {}, []
    for s in SCALES:
        r = json.loads((CAL / f"run_{tag(s)}.json").read_text())
        vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
        ton = round(guess(s) + (VO_TGT - vo) / SLOPE, 3)
        tr[tag(s)] = {"ton0_ns": guess(s), "vo0": vo, "ton_ns": ton}
        c0 = board(s, ton)
        for k in range(5):
            t = round(c0["line_step"]["t_us"] + k * T0 * s / 5, 4)
            name = f"{tag(s)}_sh{k}_l_p48_1us"
            c = dict(c0, line_step=dict(c0["line_step"], t_us=t), out=f"run_{name}.json",
                     note=f"A178 {name}: L x {s} board (ton {ton} ns), final plant, step at {t} us")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (HERE / "trims.json").write_text(json.dumps(tr, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", tr)


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
