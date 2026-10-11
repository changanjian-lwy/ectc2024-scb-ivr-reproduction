"""A197 cosim cfgs: A191's 12 runs (slow devices, L x 0.75 / 0.8, 125 C, +4.8 V / 1 us at six step positions, lead
9.5 ns) with the adopted handover request, hand_vo_v 1.045 (A188), in place of A186's 1.03. Nothing else changes, so
A191 is the reference run for run.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A191 = HERE.parent / "A191_p24_slow_corner_lead" / "cosim"
COS = HERE / "cosim"
HAND_VO = 1.045


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for name in (A191 / "ORDER.txt").read_text().split():
        ref = json.loads((A191 / f"cfg_{name}.json").read_text())
        assert (ref["hand_vo_v"], ref["driver"]["hs_on_lead_ns"], ref["gate"]["temp"]) == (1.03, 9.5, 125.0)
        c = dict(ref, hand_vo_v=HAND_VO, out=f"run_{name}.json",
                 note=ref["note"].replace("A191", "A197").replace("A187", "A197") + f"; handover request {HAND_VO} V (A191: 1.03)")
        assert {x for x in c if c[x] != ref[x]} <= {"hand_vo_v", "out", "note"}
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
