"""A168 pre check (single gate-driven edges, scripts/p24_gate_edges.edge_plant, A145 state): the loop bound under
A164 / A167's drive. For loop 50 / 60 / 75 pH and a nominal turn-on resistor R of 3.0 / 3.5 / 4.0 ohm (+-20 %):
- fast corner (threshold -0.3 V, driver x 0.8): hard turn-on at 12 / 17 V -> SH2's peak V_DS;
  strong-sink turn-off (0.3 ohm x 0.8) at 200 / 260 A -> SH1's peak V_DS;
- slow corner (threshold +1.0 V, Q_G x 1.29, driver x 1.2) and nominal: turn-on delay at 3.8 / 17 V (the loop hardly
  moves it; measured at every loop anyway).
50 pH / 3.0 ohm is the anchor: A164's cosim fast corner reached 38.5 V there.
  PYTHONPATH=src python3 a168_pre.py [jobs]  -> a168_pre.json"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import p24_gate_edges as G  # noqa: E402

LS, RS, R_OFF = (50, 60, 75), (3.0, 3.5, 4.0), 0.3
FF, SS = {"dk2": -0.3}, {"dk2": 1.0, "cg": 1.29}


def jobs():
    out = []
    for l in LS:
        for r in RS:
            for dv in (12.0, 17.0):
                out.append(("on", dict(l=l, r=round(0.8 * r, 3), dv=dv, spread=FF, tag=f"ff_R{r}")))
            for dv in (3.8, 17.0):
                out.append(("on", dict(l=l, r=round(1.2 * r, 3), dv=dv, spread=SS, tag=f"ss_R{r}")))
                out.append(("on", dict(l=l, r=r, dv=dv, tag=f"nom_R{r}")))
        for i0 in (200.0, 260.0):
            out.append(("off", dict(l=l, r=round(0.8 * R_OFF, 3), i0=i0, spread=FF, tag="ff_off")))
    return out


def main(n=8):
    with Pool(n) as pool:
        rows = pool.map(G._job, jobs(), chunksize=1)
    (HERE / "a168_pre.json").write_text(json.dumps(rows, indent=1, default=float) + "\n")
    for w in rows:
        r = w.get("res", {})
        print(w["kind"], w["l"], w["spread"], w.get("dv", w.get("i0")), w["r"],
              "ERR" if "error" in w else f"vpk {r['vpk_v']:.1f} V delay {r['delay_ns']:.1f} ns")


if __name__ == "__main__":
    main(int(sys.argv[1]) if sys.argv[1:] else 8)
