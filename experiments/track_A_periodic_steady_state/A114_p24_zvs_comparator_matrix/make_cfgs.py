"""A114 configurations: A112's 20% and 25% designs on the 16-row standard matrix with one change, the comparator-decided
phase-1 turn-off (cfg lo_pred = 0, A105's I1; A113 cmp). Writes cosim/cfg_c<pct>_<row>.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A112 = HERE.parent / "A112_p24_zvs_designs_matrix" / "cosim"

if __name__ == "__main__":
    n = 0
    for src in sorted(A112.glob("cfg_p*.json")):
        c = json.loads(src.read_text())
        c["lo_pred"] = 0
        name = "c" + src.stem[5:]
        c["note"] = f"A114 {name}: A112's {src.stem[4:]} with the comparator phase-1 turn-off (lo_pred 0)."
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        n += 1
    print(n, "configurations")
