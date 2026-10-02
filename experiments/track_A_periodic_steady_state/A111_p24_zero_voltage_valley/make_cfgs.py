"""A111 configurations: one factor, the zero-voltage valley measurement (cfg valley_zero = 1), on the adopted single
module at the negative-current targets of A110: 5% and 20% (where V_DS never reaches zero: identity checks against
C02 s1_n0 and A110 n20), 25% and 30%, and at 30% the +/-62.5 A load steps and 30 ps jitter. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C02 = HERE.parents[1] / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
A110 = HERE.parent / "A110_p24_high_side_zvs" / "cosim"
SOURCES = {"z5": C02 / "cfg_s1_n0.json", "z20": A110 / "cfg_n20.json", "z25": A110 / "cfg_n25.json",
           "z30": A110 / "cfg_n30.json", "z30_s_p62": A110 / "cfg_n30_s_p62.json",
           "z30_s_m62": A110 / "cfg_n30_s_m62.json", "z30_j30": A110 / "cfg_n30_j30.json"}

if __name__ == "__main__":
    for name, src in SOURCES.items():
        c = json.loads(src.read_text())
        c["valley_zero"] = 1
        c["note"] = f"A111 {name}: {src.parent.parent.name}'s {src.stem[4:]} with the zero-voltage valley measurement. " + c["note"]
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(SOURCES), "configurations:", ", ".join(SOURCES))
