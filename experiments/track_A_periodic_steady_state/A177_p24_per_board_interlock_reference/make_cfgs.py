"""A177 cosim cfgs: the per-board interlock reference (comparator at V_th - 0.2 V: t_il 1.4 ns at the slow corner,
A173's estimate) on the slow-corner rows where A174's fixed 1.0 V reference (8.3 ns) failed: A173's cfgs of
ss s_p62, ss l_m80_10us, ss slew4 and four modules ss l_p48_1us with t_il 1.4 ns.
Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A3 = HERE.parent / "A173_p24_final_plant_coverage" / "cosim"
ROWS = ("m4_ss_l_p48_1us", "ss_s_p62", "ss_l_m80_10us", "ss_slew4")
T_IL = 1.4


def main():
    COS.mkdir(exist_ok=True)
    for row in ROWS:
        c = json.loads((A3 / f"cfg_{row}.json").read_text())
        name = f"pb_{row}"
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(
            c, gate=dict(c["gate"], t_il_ns=T_IL), out=f"run_{name}.json",
            note=f"A177 {name}: {row} on the final plant, per-board interlock reference t_il {T_IL} ns"), indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(f"pb_{r}" for r in ROWS) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
