"""A254 cfgs (BOUNDARY Section 1): the final configuration + "ocp" {"i_a": a254_screen.level(L), "t_ns": 1} on every
reference row the screen marks (a254_screen.json, n > 0) and on two identity rows the screen leaves out although their
current crosses the level in every full-load period. Out: cosim/cfg_l_<row>.json -> run_l_<row>.json; queue.txt puts
the four-module rows first, then the longest.
  python3 make_cfgs.py -> cosim/cfg_l_*.json, cosim/queue.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
IDENT = ("p_N75_100k", "p_N0_100k")
T_NS = 1.0


def rows():
    s = json.loads((HERE / "a254_screen.json").read_text())
    return {r: x for r, x in s.items() if x["n"] or r in IDENT}


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    cost = {}
    for r, x in rows().items():
        c = json.loads((TA / x["cfg"]).read_text())      # init_run is project-relative in all 70
        ocp = {"i_a": x["level_a"], "t_ns": T_NS}
        c.update(ocp=ocp, out=f"run_l_{r}.json", note=f"A254: {x['cfg']} + ocp {ocp}")
        (HERE / "cosim" / f"cfg_l_{r}.json").write_text(json.dumps(c, indent=1) + "\n")
        cost[r] = c["t_end_us"] * int(c.get("modules", 1)) ** 2
    order = sorted(cost, key=lambda r: -cost[r])
    (HERE / "cosim" / "queue.txt").write_text("".join(f"cfg_l_{r}.json\n" for r in order))
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
