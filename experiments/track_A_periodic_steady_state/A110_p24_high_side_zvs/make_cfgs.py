"""A110 configurations: the adopted single module (A105's I2 with C02's slot_lo, C02 cosim/cfg_s1_n0.json) with one
factor, the negative-current target i_target (5% of the 125 A peak in the design), raised to 10-30% to reach high-side
zero-voltage turn-on; at 30% also the +/-62.5 A load steps and 30 ps jitter. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C02 = HERE.parents[1] / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
PEAK = 125.0
ROWS = {f"n{p}": (p, "s1_n0") for p in (10, 15, 20, 25, 30)}
ROWS.update({"n30_s_p62": (30, "s1_s_p62"), "n30_s_m62": (30, "s1_s_m62"), "n30_j30": (30, "s1_j30")})

if __name__ == "__main__":
    for name, (pct, src) in ROWS.items():
        c = json.loads((C02 / f"cfg_{src}.json").read_text())
        c["i_target"] = -pct / 100 * PEAK
        c["note"] = f"A110 {name}: C02's {src} with the negative-current target {pct}% ({c['i_target']:.2f} A)."
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(ROWS), "configurations:", ", ".join(ROWS))
