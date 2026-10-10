"""A191 cosim cfgs: A187's 12 runs (slow devices, L x 0.75 / 0.8, 125 C, +4.8 V / 1 us at six step positions, A186's
start-up) with the controller-side high-side turn-on lead raised from 8 to LEAD ns (still ramped in over 20 us after
mode P). Nothing else changes, so A187 is the reference run for run.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A187 = HERE.parent / "A187_p24_slow_corner_inductance_hot" / "cosim"
COS = HERE / "cosim"
LEAD = 9.5                                     # the bridge allows [0, t_drv_ns = 10); A164 tried 9.5 ns


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for name in (A187 / "ORDER.txt").read_text().split():
        c = json.loads((A187 / f"cfg_{name}.json").read_text())
        assert c["driver"]["hs_on_lead_ns"] == 8.0
        c = dict(c, driver=dict(c["driver"], hs_on_lead_ns=LEAD), out=f"run_{name}.json",
                 note=c["note"].replace("A187", "A191") + f"; high-side lead {LEAD} ns (A187: 8)")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
