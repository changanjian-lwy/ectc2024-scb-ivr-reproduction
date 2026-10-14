"""A220 cosim cfgs: A217's six skipping rows with the pause's last low-side intervals ended at zero current (cfg skip
"zcd_a": the front ends' threshold, the latency of their edges, 8 ns, times the current's slope Vo / L, as A217's
res_ofs_a), and the edge log widened to the last 20 us (more resumes per row).
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
ROWS = ("z_N0_25_10", "z_N0_25_0", "z_N75_25_10", "z_S75_25_10", "z_S75_hot_10", "u_N0_25_5_s62")


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for name in ROWS:
        c = json.loads((TA / "A217_p24_resume_offset" / "cosim" / f"cfg_{name}.json").read_text())
        z = c["skip"]["res_ofs_a"]
        c = dict(c, skip=dict(c["skip"], zcd_a=z), out=f"run_{name}.json")
        c["debug_edges_us"] = [c["t_end_us"] - 20.0, c["debug_edges_us"][1]]
        c["note"] = c["note"].replace("A217", "A220", 1) + f"; the pause's last intervals end at zero current (threshold {z} A)"
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(ROWS) + "\n")
    print(len(ROWS), "cfgs:", {n: json.loads((COS / f"cfg_{n}.json").read_text())["skip"] for n in ROWS})
