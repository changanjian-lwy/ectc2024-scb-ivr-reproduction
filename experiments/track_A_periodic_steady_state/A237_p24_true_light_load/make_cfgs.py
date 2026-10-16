"""A237 cfgs (BOUNDARY Section 1): A229's adopted rows with the release at 300 us made a true constant-current load:
the 4 mOhm resistive load disconnects at 300 us (t_load_off_us) and the load steps alone remain.
  python3 make_cfgs.py"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A29 = TA / "A229_p24_kd_band" / "cosim"
ROWS = {   # row -> (A229 reference cfg stem, constant current after 300 us (A), re-application at 380 us (A) or None)
    "c0_N0": ("z_N0_0_t0_b", 0.0, None), "c2_N0": ("z_N0_0_t0_b", 5.0, None), "c10_N0": ("z_N0_10_t0_b", 25.0, None),
    "c0_N75": ("z_N75_10_t0_b", 0.0, None), "c10_N75": ("z_N75_10_t0_b", 25.0, None),
    "cw5_N0": ("w5_N0_b", 12.5, 237.5), "cw5_N75": ("w5_N75_b", 12.5, 237.5), "c30_S75h": ("w30_S75h_b", 75.0, 175.0),
}
REF = {"c0_N0": "z_N0_0_t0_b", "c10_N0": "z_N0_10_t0_b", "c10_N75": "z_N75_10_t0_b", "cw5_N0": "w5_N0_b",
       "cw5_N75": "w5_N75_b", "c30_S75h": "w30_S75h_b"}                 # the same release on the 4 mOhm base


def main():
    for row, (stem, i_cc, i_re) in ROWS.items():
        c = json.loads((A29 / f"cfg_{stem}.json").read_text())
        c.pop("load_step2", None)
        c.update(out=f"run_{row}.json", t_load_off_us=300.0, load_step={"t_us": 300.0, "i_a": i_cc},
                 note=f"A237: A229 {stem}, at 300 us the 4 mOhm load disconnects, {i_cc} A constant current"
                      + (f", +{i_re} A at 380 us" if i_re else ""))
        if i_re:
            c["load_step2"] = {"t_us": 380.0, "i_a": i_re}
        (COS / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
