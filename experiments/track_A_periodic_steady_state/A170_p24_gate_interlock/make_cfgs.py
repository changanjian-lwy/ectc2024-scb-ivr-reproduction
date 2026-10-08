"""A170 cosim cfgs: the adopted drive with gate-driven low sides (A169's cfgs) plus the driver interlock (cfg gate
"interlock" 1, "t_il_ns" 0.5: a turn-on waits until its complement stops conducting, then starts 0.5 ns later).
- S50 (50 pH, 3.0 ohm, A164's trims): A169's five rows.
- S50t1: nom L07_l_p48_1us with t_il 1.0 ns.
- Q60 / Q75 (60 pH 3.5 ohm / 75 pH 4.0 ohm, A168's trims, low sides gate-driven): nom L07_l_p48_1us, the row that
  shot through in A168.
Writes cosim/cfg_<conf>_<row>.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A9 = HERE.parent / "A169_p24_gate_low_sides" / "cosim"
A8 = HERE.parent / "A168_p24_gate_loop_bound" / "cosim"
T_IL = 0.5
RUNS = ([("S50", A9 / f"cfg_{r}.json", r, T_IL) for r in ("ss_l_p48_1us", "nom_L07_l_p48_1us", "hot_l_p48_1us",
                                                           "ff_l_p48_1us", "nom_l_p48_1us")]
        + [("S50t1", A9 / "cfg_nom_L07_l_p48_1us.json", "nom_L07_l_p48_1us", 1.0)]
        + [(c, A8 / f"cfg_{c}_nom_L07_l_p48_1us.json", "nom_L07_l_p48_1us", T_IL) for c in ("Q60", "Q75")])


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for conf, src, row, t_il in RUNS:
        cfg = json.loads(src.read_text())
        name = f"{conf}_{row}"
        cfg = dict(cfg, gate=dict(cfg["gate"], switches="all", interlock=1, t_il_ns=t_il), out=f"run_{name}.json",
                   note=f"A170 {name}: {src.parent.parent.name} cfg, low sides gate-driven, driver interlock t_il {t_il} ns")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
