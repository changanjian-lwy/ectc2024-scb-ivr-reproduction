"""C08 configurations: C06's 18 rows (the four-module final design: A129's g125 + modules 4 + slave_floor 1) with A136's
phase-1 cap (cfg vff rel_q8 320, rel_lp 1) in every module, C06's timing (steps at 800 us); plus s_p62 with every
module's L x 1.2, the step at 1000 us (end 1400 us), with A128's absolute cap (l12a_s_p62) and with A136's (l12q_s_p62).
Writes cosim/cfg_<row>.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C06 = HERE.parent / "C06_slave_floor" / "cosim"
Q = {"rel_q8": 320, "rel_lp": 1}


def main():
    rows = (C06 / "ORDER.txt").read_text().split()
    order = []
    (HERE / "cosim").mkdir(exist_ok=True)
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        c["vff"] = dict(c["vff"], **Q)
        c["note"] = f"C08 {row}: C06's {row} with A136's relative phase-1 cap on ton's low-pass (rel_q8 320, rel_lp 1)."
        c["out"] = f"run_{row}.json"
        (HERE / "cosim" / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(row)
    for arm in ("a", "q"):
        c = json.loads((C06 / "cfg_s_p62.json").read_text())
        c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * 1.2)
        c["load_step"] = dict(c["load_step"], t_us=1000.0)
        c["t_end_us"] = 1400.0
        if arm == "q":
            c["vff"] = dict(c["vff"], **Q)
        name = f"l12{arm}_s_p62"
        c["note"] = f"C08 {name}: C06's s_p62 with every module's L x 1.2, step at 1000 us, " + \
            ("A128's absolute cap." if arm == "a" else "A136's relative cap on ton's low-pass.")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
