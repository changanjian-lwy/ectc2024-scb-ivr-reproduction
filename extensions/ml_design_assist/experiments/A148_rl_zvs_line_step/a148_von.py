"""A148: D63's turn-on V_DS block (p24_valley_map.von_table) at the A124 design's L and t_tr (or L x m)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from scb_ivr.p24_valley_map import von_table

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / "A126_ppo_line_feedforward" / "a126_design.json"


def main(m=1.0):
    """m: L x m with t_tr x sqrt(m) (A132's scaling) -> a148_von_table_m<m>.json (m 1: a148_von_table.json)."""
    c = json.loads(DESIGN.read_text())
    c["lf"], c["t_tr"] = c["lf"] * m, [x * m ** 0.5 for x in c["t_tr"]]
    t = time.time()
    cur, rails, t13, t4 = von_table(c["lf"], c["t_tr"], jobs=10)
    name = "a148_von_table.json" if m == 1.0 else f"a148_von_table_m{round(m * 100):03d}.json"
    (HERE / name).write_text(json.dumps({"lf": c["lf"], "t_tr": c["t_tr"], "currents": cur, "rails": rails,
                                                          "v13": t13, "v4": t4}) + "\n")
    print(f"table {len(rails)} x {len(cur)} x 2 in {time.time() - t:.0f} s")


if __name__ == "__main__":
    import sys
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 1.0)
