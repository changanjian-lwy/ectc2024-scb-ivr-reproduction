"""A130 configurations: A129's cfg_g125_l_m48_5us (adopted design, vff + gth 100) with only line_step changed.
Five rows x two step phases (t_us 800 and 800.33) -> cosim/cfg_<row>_<a|b>.json and ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "A129_cosim_vff_slope_gate" / "cosim" / "cfg_g125_l_m48_5us.json"
ROWS = {"l_m80_6us": (-8.0, 6.0), "l_m80_7p5us": (-8.0, 7.5), "l_p48_2us": (4.8, 2.0), "l_p48_3us": (4.8, 3.0),
        "l_p80_10us": (8.0, 10.0)}
PHASES = {"a": 800.0, "b": 800.33}


def main():
    order = []
    for row, (dv, slew) in ROWS.items():
        for ph, t in PHASES.items():
            c = json.loads(BASE.read_text())
            c["line_step"] = {"t_us": t, "dv": dv, "slew_us": slew}
            name = f"y130_{row}_{ph}"
            c["note"] = f"A130 {name}: adopted design (vff gth 100), line step {dv:+} V over {slew} us at {t} us"
            c["out"] = f"run_{name}.json"
            (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")


if __name__ == "__main__":
    main()
