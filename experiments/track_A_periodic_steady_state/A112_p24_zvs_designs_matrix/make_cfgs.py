"""A112 configurations: the standard matrix (scb_ivr.cosim.matrix.ROWS, 16 rows) on the two A110 candidates, the adopted
single module with a negative-current target of 20% (efficiency optimum) and 25% (practical high-side zero voltage).
Writes cosim/cfg_p20_<row>.json and cfg_p25_<row>.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from scb_ivr.cosim.matrix import configs  # noqa: E402

A110 = HERE.parent / "A110_p24_high_side_zvs" / "cosim"

if __name__ == "__main__":
    n = 0
    for pct in (20, 25):
        base = json.loads((A110 / f"cfg_n{pct}.json").read_text())
        for row, c in configs(base).items():
            c["note"] = f"A112 p{pct}_{row}: A110's {pct}% design (i_target {base['i_target']:.2f} A), standard-matrix row {row}."
            c["out"] = f"run_p{pct}_{row}.json"
            (HERE / "cosim" / f"cfg_p{pct}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
            n += 1
    print(n, "configurations")
