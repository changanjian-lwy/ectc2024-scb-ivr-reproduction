"""A239 cfgs (BOUNDARY Section 1): the ~2 % minimum load (5 A per module) on the rows A237 did not run, final
configuration on nominal boards (A231's per-corner handover lead included).
  python3 make_cfgs.py
u5_*: start-up into 0.2 Ohm from t = 0 (5 A at 1 V), from A231's lead rows, to 300 us.
c2_* / c1_N0: release from 250 A at 300 us, the 4 mOhm load disconnects and a constant current remains (A237's method),
to 750 us; 125 C rows take A231's hot gate and switch resistances."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A31, A37 = TA / "A231_p24_lead_per_corner" / "cosim", TA / "A237_p24_true_light_load" / "cosim"
R_MIN = 1.0 / 5.0                                       # Ohm: 5 A at 1 V
LEAD_US = 0.7                                           # A231: the slope lead on nominal boards
START = {"u5_N0": "u_N0_20_lead", "u5_N75": "u_N75_20_lead", "u5_N0h": "u_N0h_30_lead", "u5_N75h": "u_N75h_30_lead"}
RELEASE = {   # row -> (A237 cfg stem, constant current after 300 us (A), 125 C)
    "c2_N75": ("c0_N75", 5.0, False), "c2_N0h": ("c2_N0", 5.0, True), "c2_N75h": ("c0_N75", 5.0, True),
    "c1_N0": ("c2_N0", 2.5, False)}


def hot():
    c = json.loads((A31 / "cfg_u_N0h_30_lead.json").read_text())
    return c["gate"], c["r_sw_mohm"]


def main():
    COS.mkdir(exist_ok=True)
    for row, stem in START.items():
        c = json.loads((A31 / f"cfg_{stem}.json").read_text())
        c["circuit"] = dict(c["circuit"], r_load=R_MIN)
        c.update(out=f"run_{row}.json", t_end_us=300.0,
                 note=f"A239 {row}: A231 {stem} with the load {R_MIN} Ohm (5 A at 1 V) from t = 0, to 300 us")
        (COS / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    gate_h, rsw_h = hot()
    for row, (stem, i_cc, is_hot) in RELEASE.items():
        c = json.loads((A37 / f"cfg_{stem}.json").read_text())
        c.update(out=f"run_{row}.json", hand_lead_us=LEAD_US, load_step={"t_us": 300.0, "i_a": i_cc},
                 note=f"A239 {row}: A237 {stem} with {i_cc} A after the 300 us release, handover lead {LEAD_US} us"
                      + (", 125 C" if is_hot else ""))
        if is_hot:
            c.update(gate=gate_h, r_sw_mohm=rsw_h)
        (COS / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(START) + len(RELEASE), "cfgs")


if __name__ == "__main__":
    main()
