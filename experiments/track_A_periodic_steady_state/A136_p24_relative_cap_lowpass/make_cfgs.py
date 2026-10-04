"""A136 configurations: A135's rows and timing (steps at 1000 us, end 1400 us; m / j rows end 1200 us) with the relative
phase-1 cap on ton's low-pass (cfg vff rel_q8 320 = 1.25, rel_lp 1; scb_vff A136). `1`: stage 1 - l_p48_1us,
l_p48_5us, x_l_p80_10us, s_p62, n0 at L x 0.7 / 1.0 / 1.3; `2`: stage 2 - every other row of A135's plan (A124's seven
step rows + n0 + A129's matrix at L x 0.7 / 0.85 / 1.0 / 1.15 / 1.3, x_l_p80_10us at 0.7 / 1.0 / 1.3). `ident`: A135's
r100_l_p48_1us (rel_lp absent) -> tmp/identity_a136/. Writes cosim/cfg_q<mmm>_<row>.json, ORDER_<stage>.txt."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("a135_cfgs", HERE.parent / "A135_p24_relative_cap" / "make_cfgs.py")
A135 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A135)
REL = 320
STAGE1 = [(m, row) for m in (0.7, 1.0, 1.3) for row in ("l_p48_1us", "l_p48_5us", "x_l_p80_10us", "s_p62", "n0")]
ALL = [(m, row) for m in A135.MS for row in A135.STEP_ROWS + A135.MATRIX_ROWS] + [(m, "x_l_p80_10us") for m in (0.7, 1.0, 1.3)]


def cfg(m, row):
    _, c = A135.cfg("r", m, row)
    c["vff"] = dict(c["vff"], rel_q8=REL, rel_lp=1)
    name = f"q{round(m * 100):03d}_{row}"
    src = "l_p48_5us" if row == "x_l_p80_10us" else row
    c["note"] = (f"A136 {name}: A129's g125_{src} at k_L {m:g}" + (", +8 V / 10 us" if row.startswith("x_") else "")
                 + f", relative cap on ton's low-pass (rel_q8 {REL}, rel_lp 1)")
    c["out"] = f"run_{name}.json"
    return name, c


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "1"
    if stage == "ident":
        out = PROJECT / "tmp" / "identity_a136"
        out.mkdir(parents=True, exist_ok=True)
        src = HERE.parent / "A135_p24_relative_cap" / "cosim" / "cfg_r100_l_p48_1us.json"
        (out / src.name).write_text(src.read_text())
        print("1 identity cfg")
        return
    plan = STAGE1 if stage == "1" else [x for x in ALL if x not in STAGE1]
    (HERE / "cosim").mkdir(exist_ok=True)
    order = []
    for m, row in plan:
        name, c = cfg(m, row)
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (HERE / "cosim" / f"ORDER_{stage}.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs, stage", stage)


if __name__ == "__main__":
    main()
