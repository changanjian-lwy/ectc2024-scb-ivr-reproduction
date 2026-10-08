"""A167 cosim cfgs: A164's spec (50 pH, 3.0 / 0.3 ohm +-20 %, per-board start-up trim, the 8 ns lead on the predictive
high-side turn-on only) with the lead grown from 0 over 20 us after mode P starts (bridge driver lead_ramp_us), so the
handover sees no on-time step (A164: 218.6 A at L x 0.7) while every later edge has A164's full lead (A165 / A166: a
pulse-shifted or a per-board 1.3 ns lead let L x 0.7 reach 211 / 208 A after +4.8 V / 1 us). Rows: nom L07_l_p48_1us,
l_p48_1us; ss l_p48_1us, s_p62; hot l_p48_1us. Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A4D = HERE.parent / "A164_p24_gate_drive_spread"
RAMP_US = 20.0
ROWS = ("nom_L07_l_p48_1us", "ss_l_p48_1us", "ss_s_p62", "nom_l_p48_1us", "hot_l_p48_1us")


def main():
    COS.mkdir(exist_ok=True)
    for name in ROWS:
        cfg = json.loads((A4D / "cosim" / f"cfg_{name}.json").read_text())
        cfg = dict(cfg, driver=dict(cfg["driver"], lead_ramp_us=RAMP_US), out=f"run_{name}.json",
                   note=cfg["note"].replace("A164", "A167") + f", lead ramped in over {RAMP_US} us after mode P")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(ROWS) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
