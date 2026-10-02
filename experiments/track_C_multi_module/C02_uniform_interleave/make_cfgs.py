"""C02 configurations: A105's I2 (one module) and C01's four-module cases, each with one change, cfg "slot_lo" = 1
(the following slots, and the slaves' slots, referenced to phase 1's low-side turn-off). Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A105 = HERE.parents[1] / "track_A_periodic_steady_state" / "A105_p24_integrated_standard_matrix" / "cosim"
C01 = HERE.parent / "C01_four_modules_baseline" / "cosim"
CASES = {   # new name: (source configuration)
    "s1_n0": A105 / "cfg_i2_n0.json", "s1_j30": A105 / "cfg_i2_j30.json",
    "s1_s_m62": A105 / "cfg_i2_s_m62.json", "s1_s_p62": A105 / "cfg_i2_s_p62.json",
    "m4_n0": C01 / "cfg_m4_n0.json", "m4_L5": C01 / "cfg_m4_L5.json", "m4_j30": C01 / "cfg_m4_j30.json",
    "m4_s_m250": C01 / "cfg_m4_s_m250.json", "m4_s_p250": C01 / "cfg_m4_s_p250.json",
}

if __name__ == "__main__":
    for name, src in CASES.items():
        c = json.loads(src.read_text())
        c["note"] = f"C02 {name}: {src.parent.parent.name}'s {src.stem[4:]} with slot_lo = 1 (slots from phase 1's low-side turn-off). " + c["note"]
        c["slot_lo"] = 1
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        print("wrote", f"cfg_{name}.json")
