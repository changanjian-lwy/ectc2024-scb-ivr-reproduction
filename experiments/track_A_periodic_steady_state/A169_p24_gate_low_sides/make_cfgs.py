"""A169 cosim cfgs: the adopted drive (A164 + A167: 50 pH, r_on 3.0 / r_off 0.3 ohm +-20 %, 8 ns turn-on lead ramped in
over 20 us after mode P, A164's per-board trims) with every switch gate-driven (cfg gate "switches" "all"): the low
sides get EPC2067 gates too, through the same resistors and corner (their turn-off sink is the spec's <= 0.3 ohm).
Rows: nom l_p48_1us, L07_l_p48_1us; ff l_p48_1us; hot l_p48_1us; ss l_p48_1us. Writes cosim/cfg_*.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A4D = HERE.parent / "A164_p24_gate_drive_spread"
RAMP_US = 20.0
ROWS = ("ss_l_p48_1us", "nom_L07_l_p48_1us", "hot_l_p48_1us", "ff_l_p48_1us", "nom_l_p48_1us")


def main():
    COS.mkdir(exist_ok=True)
    for name in ROWS:
        cfg = json.loads((A4D / "cosim" / f"cfg_{name}.json").read_text())
        cfg = dict(cfg, driver=dict(cfg["driver"], lead_ramp_us=RAMP_US), gate=dict(cfg["gate"], switches="all"),
                   out=f"run_{name}.json",
                   note=cfg["note"].replace("A164", "A169") + f", lead ramped over {RAMP_US} us, low sides gate-driven")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(ROWS) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
