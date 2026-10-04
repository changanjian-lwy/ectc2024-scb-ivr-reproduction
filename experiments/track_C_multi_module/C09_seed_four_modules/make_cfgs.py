"""C09 configurations: C06's 18 rows (the four-module final design: A129's g125 + modules 4 + slave_floor 1) with the
adopted single-module phase-1 cap and handover restart (cfg vff rel_q8 320, rel_lp 1, seed 1) in every module, C06's
timing (steps at 800 us); plus C06's s_m25 unchanged except for the step, moved to 800.1831 us so it lands 81.3 ns
after the master's phase-1 turn-on, where C08's s_m25 step landed (c06al_s_m25). Writes cosim/cfg_<row>.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C06 = HERE.parent / "C06_slave_floor" / "cosim"
Q = {"rel_q8": 320, "rel_lp": 1, "seed": 1}
T_ALIGN_US = 800.1831                     # C06 s_m25's phase-1 turn-on 800.1018 us + C08's offset 81.3 ns


def main():
    rows = (C06 / "ORDER.txt").read_text().split()
    order = []
    (HERE / "cosim").mkdir(exist_ok=True)
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        c["vff"] = dict(c["vff"], **Q)
        c["note"] = f"C09 {row}: C06's {row} with the adopted vff cap and restart (rel_q8 320, rel_lp 1, seed 1)."
        c["out"] = f"run_{row}.json"
        (HERE / "cosim" / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(row)
    c = json.loads((C06 / "cfg_s_m25.json").read_text())
    c["load_step"] = dict(c["load_step"], t_us=T_ALIGN_US)
    c["note"] = "C09 c06al_s_m25: C06's s_m25 (no change to the design) with the step at C08's offset after phase 1's turn-on."
    c["out"] = "run_c06al_s_m25.json"
    (HERE / "cosim" / "cfg_c06al_s_m25.json").write_text(json.dumps(c, indent=1) + "\n")
    order.append("c06al_s_m25")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
