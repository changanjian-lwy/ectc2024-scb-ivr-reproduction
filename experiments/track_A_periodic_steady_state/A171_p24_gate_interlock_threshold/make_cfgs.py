"""A171 cosim cfgs: A170's eight runs with the threshold form of the driver interlock (cfg gate "interlock"
"threshold": a turn-on's gate charges as usual and, if its channel would start while the complement conducts, waits
at that level until the complement stops, then starts t_il later). Same rows, trims, t_il (0.5 ns; S50t1 1.0 ns)
and names as A170. Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A0 = HERE.parent / "A170_p24_gate_interlock" / "cosim"


def main():
    COS.mkdir(exist_ok=True)
    order = (A0 / "ORDER.txt").read_text().split()
    for name in order:
        cfg = json.loads((A0 / f"cfg_{name}.json").read_text())
        cfg = dict(cfg, gate=dict(cfg["gate"], interlock="threshold"), out=f"run_{name}.json",
                   note=cfg["note"].replace("A170", "A171") + ", threshold form")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
