"""A172 cosim cfgs: the final package plant - A167's drive (50 pH, 3.0 / 0.3 ohm +-20 %, 8 ns lead ramped over 20 us),
every switch gate-driven (A169) and the threshold-form driver interlock (A171, t_il 0.5 ns).
- nom L07_l_p48_1us with the board re-trimmed under this plant: A171's run of that row gave Vo(143.5 us) 1.0101 V at
  A164's 34.813 ns, so ton = 34.813 + (1.035 - 1.0101) / 0.026 = 35.769 ns;
- four modules, nom l_p48_1us (A164's m4 cfg with A164's nom_L0 trim).
Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A1 = HERE.parent / "A171_p24_gate_interlock_threshold" / "cosim"
A4 = HERE.parent / "A164_p24_gate_drive_spread" / "cosim"
TON_L07 = 35.769


def main():
    COS.mkdir(exist_ok=True)
    c = json.loads((A1 / "cfg_S50_nom_L07_l_p48_1us.json").read_text())
    c = dict(c, ton_ns=TON_L07, out="run_nom_L07_l_p48_1us.json",
             note=f"A172 nom_L07_l_p48_1us: A171's S50 cfg, board re-trimmed under the final plant (ton {TON_L07} ns)")
    (COS / "cfg_nom_L07_l_p48_1us.json").write_text(json.dumps(c, indent=1) + "\n")
    m = json.loads((A4 / "cfg_m4_nom_l_p48_1us.json").read_text())
    m = dict(m, driver=dict(m["driver"], lead_ramp_us=20.0),
             gate=dict(m["gate"], switches="all", interlock="threshold", t_il_ns=0.5), out="run_m4_nom_l_p48_1us.json",
             note="A172 m4_nom_l_p48_1us: A164's four-module cfg, lead ramped over 20 us, all switches gate-driven, "
                  "threshold interlock t_il 0.5 ns")
    (COS / "cfg_m4_nom_l_p48_1us.json").write_text(json.dumps(m, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("m4_nom_l_p48_1us\nnom_L07_l_p48_1us\n")
    print("2 cfgs")


if __name__ == "__main__":
    main()
