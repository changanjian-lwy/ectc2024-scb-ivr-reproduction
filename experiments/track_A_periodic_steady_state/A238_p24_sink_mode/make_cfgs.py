"""A238 cfgs (BOUNDARY Section 1): A237's true-load rows and A230's start-ups into 1 kOhm / full load (final
configuration, lead arm) with the sink mode (cfg "sink").
  python3 make_cfgs.py"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
SINK = {"hi_mv": 20.0, "lo_mv": 3.0, "i_a": -40.0}
SRC = {"A237": TA / "A237_p24_true_light_load" / "cosim", "A230": TA / "A230_p24_handover_slope_lead" / "cosim"}
ROWS = {   # row -> (source experiment, source cfg stem); the reference is the source's record
    "s_c0_N0": ("A237", "c0_N0"), "s_c0_N75": ("A237", "c0_N75"), "s_c2_N0": ("A237", "c2_N0"),
    "s_c10_N0": ("A237", "c10_N0"), "s_c10_N75": ("A237", "c10_N75"),
    "s_cw5_N0": ("A237", "cw5_N0"), "s_cw5_N75": ("A237", "cw5_N75"), "s_c30_S75h": ("A237", "c30_S75h"),
    "s_u_N0_0": ("A230", "u_N0_0_lead"), "s_u_N75_0": ("A230", "u_N75_0_lead"), "s_u_N0_100": ("A230", "u_N0_100_lead"),
}


def main():
    COS.mkdir(exist_ok=True)
    for row, (exp, stem) in ROWS.items():
        c = json.loads((SRC[exp] / f"cfg_{stem}.json").read_text())
        c.update(out=f"run_{row}.json", sink=dict(SINK),
                 note=f"A238: {exp} {stem} + sink {SINK} (scb_ctrl cfg_sink; the bridge's target i_a while sink is set)")
        (COS / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
