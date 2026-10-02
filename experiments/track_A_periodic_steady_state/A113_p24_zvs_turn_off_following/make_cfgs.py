"""A113 configurations: the 25% design (A112 p25_<row>) on its failing transient rows and n0, with phase 1's turn-off
made to follow Ton, two ways (one factor each):
- ff: A100's feed-forward of the learned on-low interval, cfg lo_ff = 1, lo_kff = 11 (d dlo / d Ton = (V_rail - Vo) / Vo);
- cmp: the comparator-decided phase-1 turn-off (A105's I1), cfg lo_pred = 0.
Writes cosim/cfg_<ff|cmp>_<row>.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A112 = HERE.parent / "A112_p24_zvs_designs_matrix" / "cosim"
ROWS = ("n0", "s_m62", "l_m48_1us", "l_m80_10us")
VARIANTS = {"ff": {"lo_ff": 1, "lo_kff": 11}, "cmp": {"lo_pred": 0}}

if __name__ == "__main__":
    for v, change in VARIANTS.items():
        for row in ROWS:
            c = json.loads((A112 / f"cfg_p25_{row}.json").read_text())
            c.update(change)
            c["note"] = f"A113 {v}_{row}: A112's p25_{row} with {change}."
            c["out"] = f"run_{v}_{row}.json"
            (HERE / "cosim" / f"cfg_{v}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(VARIANTS) * len(ROWS), "configurations")
