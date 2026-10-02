"""A108 configurations: the adopted single module (A105's I2 with C02's slot_lo, C02 cosim/cfg_s1_n0.json) with a
+/-4.8 V (10%) input step at 400 us over 1, 2, 3, 5 and 10 us. One factor: the input slew. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "track_C_multi_module" / "C02_uniform_interleave" / "cosim" / "cfg_s1_n0.json"
SLEWS_US = (1.0, 2.0, 3.0, 5.0, 10.0)
SLEWS_ADDED_US = (20.0, 50.0)          # added after the first ten runs (RESULTS Section 2)

if __name__ == "__main__":
    base = json.loads(BASE.read_text())
    names = []
    for dv in (4.8, -4.8):
        for slew in SLEWS_US + SLEWS_ADDED_US:
            name = f"{'p' if dv > 0 else 'm'}48_{slew:g}us"
            c = dict(base)
            c["line_step"] = {"t_us": 400.0, "dv": dv, "slew_us": slew}
            c["t_end_us"] = 600.0 if slew <= 50 else 400.0 + slew + 150.0
            c["note"] = f"A108 {name}: A105's I2 with slot_lo (C02 s1), input {dv:+.1f} V over {slew:g} us at 400 us."
            c["out"] = f"run_{name}.json"
            (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            names.append(name)
    print(len(names), "configurations:", ", ".join(names))
