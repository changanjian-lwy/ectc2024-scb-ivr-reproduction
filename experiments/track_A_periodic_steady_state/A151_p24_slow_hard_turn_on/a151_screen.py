"""A151 single-edge screen (A145 harness, rails 12 V, 48 V in): SH1 turned on hard, turn-off kept at 72 A/ns, turn-on
di/dt 72 / 36 / 18 / 9 A/ns, loop 50 / 100 / 150 pH at Q 7 (and Q 3 for comparison). Cases: valley turn-on at V_DS
dv = 3.8 V (steady state), 12 V and 17 V (A147 / A148: phase 1 after +4.8 V / 1 us turns on at 17-19 V), and A145's
rev40 (SL1 reverse-conducting 40 A, the start-up case). Per case: SH2's peak V_DS, the channel's edge energy and the
loop dampers' energy per event. Writes a151_screen.json; prints <= 15 lines."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A145_p24_finite_switching_edges"))
import a145_edge as E  # noqa: E402
from scb_ivr.cosim.circuit import Sim  # noqa: E402

DIDT_ON, LS, QS = (72, 36, 18, 9), (50, 100, 150), (7, 3)
CASES = {"v3.8": (3.8, 0.0, None), "v12": (12.0, 0.0, None), "v17": (17.0, 0.0, None),
         "rev40": (12.0, 40.0, [False] * 4 + [True, False, False, False])}


def on(l_ph, q, didt_on, case):
    dv, i1, diode = CASES[case]
    p = dataclasses.replace(E.params(l_ph, E.q_rp(l_ph * 1e-12, q), 10e-12), edge_didt_off=72e9,
                            edge_didt_on=didt_on * 1e9)
    y = E.y0(p, 0.0)
    s = Sim(p)
    a1 = 48.0 - dv
    y[s.idx["a1"]], y[s.idx["x1"]] = a1, a1 - E.VCS[0]
    if s.nlp:
        y[s.idx["h2"]] = a1
        y[s.nv + 4 + s.na] = 0.0
    y[s.nv] = i1
    pl, tr, ts, el, st = E.run_edge(p, y, [False] * 4, [False, True, True, True], diode, 0, True, (0, 1, 2, 3), E.FastPlant)
    return {"sh2_v": float(tr[1].max()), "e_edge_nj": st["e_total_j"][0] * 1e9 if st else 0.0, "e_loop_nj": el * 1e9,
            "on_ns": st["on_t_max_s"] * 1e9 if st else 0.0}


def main():
    out = [dict(l_ph=l, q=q, didt_on=d, case=c, **on(l, q, d, c))
           for l in LS for q in QS for c in CASES for d in DIDT_ON if q == 7 or c == "v17"]
    (HERE / "a151_screen.json").write_text(json.dumps(out, indent=1) + "\n")
    get = {(r["l_ph"], r["q"], r["case"], r["didt_on"]): r for r in out}
    for l in LS:
        for c in ("v17", "rev40", "v3.8"):
            print(f"L{l} {c:5s} Q7 SH2 " + " ".join(f"{d}:{get[(l, 7, c, d)]['sh2_v']:.1f}" for d in DIDT_ON)
                  + " | E edge+loop nJ " + " ".join(f"{get[(l, 7, c, d)]['e_edge_nj'] + get[(l, 7, c, d)]['e_loop_nj']:.0f}"
                                                    for d in DIDT_ON))
        print(f"L{l} v17   Q3 SH2 " + " ".join(f"{d}:{get[(l, 3, 'v17', d)]['sh2_v']:.1f}" for d in DIDT_ON))


if __name__ == "__main__":
    main()
