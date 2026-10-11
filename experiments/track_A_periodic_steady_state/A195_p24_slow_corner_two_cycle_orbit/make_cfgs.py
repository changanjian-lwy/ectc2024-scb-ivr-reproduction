"""A195 cosim cfgs: the slow boards S0 and S75 at 25 C with the final cfg (A192's, lead 9.5 ns), run to 330 us with no
event reached (the line step stays at 500 us), and one setting of the high-side turn-on corrector changed:
- step4: dt_step_ns 0.282843 -> 0.0625 (9 -> 2 LSB of 31.25 ps: the step added after an "early" report);
- shift2: err_shift 1 -> 2 (a "late" report removes a quarter of the error instead of half; also the low-side corrector);
- tgt4: eh_tgt_ps 93.75 -> 375 (the error the corrector aims at, 3 -> 12 LSB);
- step4_shift2: both.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A192 = HERE.parent / "A192_p24_slow_lead_rows" / "cosim"
COS = HERE / "cosim"
VAR = {"step4": {"dt_step_ns": 0.0625}, "shift2": {"err_shift": 2}, "tgt4": {"eh_tgt_ps": 375.0},
       "step4_shift2": {"dt_step_ns": 0.0625, "err_shift": 2}}
RUNS = [("S0", v) for v in VAR] + [("S75", "step4")]


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for b, v in RUNS:
        c = json.loads((A192 / f"cfg_{b}_25_p48_1us_p0.json").read_text())
        assert c["dt_step_ns"] == 0.282843 and c["err_shift"] == 1 and c["eh_tgt_ps"] == 93.75 and c["line_step"]["t_us"] == 500.0
        name = f"{b}_{v}"
        c = dict(c, **VAR[v], t_end_us=330.0, out=f"run_{name}.json",
                 note=f"A195 {name}: board {b}, 25 C, final cfg (lead 9.5 ns), {VAR[v]}, to 330 us, no event reached")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
