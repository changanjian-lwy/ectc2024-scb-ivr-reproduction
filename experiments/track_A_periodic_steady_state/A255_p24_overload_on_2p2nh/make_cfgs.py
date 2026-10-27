"""A255 cfgs (BOUNDARY Section 1): A246's k_N0 (+62.5 A at 500 us, 125 % load) built on the 2.2 nH boards. k_N0 is
A246's p_N0_10k without its train (load_pulse, t_load_off_us, skip, hand_lead_us), with load_step, ending at 620 us;
the same change to p_N75_10k / p_S75h_10k gives o125_N75 / o125_S75h. Arms: h = the final configuration, l = + A254's
limit (110 A on 2.2 nH, t_ns 1). The construction is checked against k_N0 itself.
  python3 make_cfgs.py -> cosim/cfg_{h,l}_o125_*.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A46 = HERE.parent / "A246_p24_held_report_floor" / "cosim"
DROP = ("load_pulse", "t_load_off_us", "skip", "hand_lead_us")
STEP = {"load_step": {"i_a": 62.5, "t_us": 500.0}, "t_end_us": 620.0}
OCP = {"i_a": 110.0, "t_ns": 1.0}
BOARDS = ("N75", "S75h")


def overload(board):
    c = json.loads((A46 / f"cfg_h_p_{board}_10k.json").read_text())
    for k in DROP:
        c.pop(k, None)                                     # hand_lead_us is on N0 only
    return c | STEP


def main():
    k = json.loads((A46 / "cfg_h_k_N0.json").read_text())
    n0 = overload("N0")
    assert {x: v for x, v in n0.items() if x not in ("out", "note")} == {x: v for x, v in k.items() if x not in ("out", "note")}
    (HERE / "cosim").mkdir(exist_ok=True)
    for b in BOARDS:
        for arm, extra in (("h", {}), ("l", {"ocp": OCP})):
            c = overload(b) | extra
            c.update(out=f"run_{arm}_o125_{b}.json", note=f"A255 arm {arm}: A246 cfg_h_p_{b}_10k as k_N0 (+62.5 A at 500 us)"
                     + (f" + ocp {OCP}" if extra else ""))
            (HERE / "cosim" / f"cfg_{arm}_o125_{b}.json").write_text(json.dumps(c, indent=1) + "\n")
    print("k_N0 reproduced; 4 cfgs")


if __name__ == "__main__":
    main()
