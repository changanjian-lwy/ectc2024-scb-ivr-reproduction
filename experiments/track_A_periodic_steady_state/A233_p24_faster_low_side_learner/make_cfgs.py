"""A233 cosim cfgs: the final configuration (A229 + A231: plant V7, A222's trims, skipping, vff rel_gate 25, kd 355 /
dead band 2 / kd_hold / kd_band_ns 4.0, hand_lead_us 0.7 on N0 / N75) with phase 1's low-side learner allowed larger
steps: cfg lo_smax 128 (s128, 4 ns per decision) and 255 (s255, ~8 ns); the final configuration has 64 (2 ns). One
module, 25 C unless named. Rows, each from an existing cfg of the final configuration at lo_smax 64 (its reference):
- item 2: A225's a_S75h_d2 / d10 / d20 and a_S75_d20 (+4.8 V / 1 us 2-20 us after mode P's entry) + kd_band_ns 4.0;
- the binding row k_S75h (S75 125 C, +4.8 V / 1 us at 500.3155 us), k_N0 (+62.5 A), w5_N0 / w20_N0 / w5_N75
  (re-applications), z_N0_10_t0 (N0 10 %, skipping): A229's arm b;
- l_N0_p48 / l_N0_m80 (+4.8 V / 2 us, -8 V / 10 us): A228's arm h + kd_band_ns 4.0.
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
SMAX = (128, 255)
SRC = {**{r: f"A225_p24_startup_items_recheck/cosim/cfg_{r}.json" for r in ("a_S75h_d2", "a_S75h_d10", "a_S75h_d20", "a_S75_d20")},
       **{r: f"A229_p24_kd_band/cosim/cfg_{r}_b.json" for r in ("k_S75h", "k_N0", "w5_N0", "w20_N0", "w5_N75")},
       "z_N0_10": "A229_p24_kd_band/cosim/cfg_z_N0_10_t0_b.json",
       **{r: f"A228_p24_damped_loop_adoption/cosim/cfg_{r}_h.json" for r in ("l_N0_p48", "l_N0_m80")}}
NOMINAL = ("k_N0", "w5_N0", "w20_N0", "w5_N75", "z_N0_10", "l_N0_p48", "l_N0_m80")


def final(row):
    c = json.loads((TA / SRC[row]).read_text())
    assert c["vff"].get("rel_gate") == 25 and c.get("kd_ns_per_v") == 355.0 and c.get("kd_hold") == 1 and c["lo_smax"] == 64
    c["kd_band_ns"] = 4.0
    if row in NOMINAL:
        c["hand_lead_us"] = 0.7
    return c


def arm(row, smax):
    c = copy.deepcopy(final(row))
    c["lo_smax"] = smax
    name = f"{row}_s{smax}"
    c["out"] = f"run_{name}.json"
    c["note"] = (f"A233 {name}: {SRC[row].split('/')[0][:4]}'s {Path(SRC[row]).stem[4:]} on the final configuration (A229 + A231), "
                 f"phase 1's low-side learner lo_smax {smax} (final: 64)")
    return name, c


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [arm(r, s) for s in SMAX for r in SRC]
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs")
