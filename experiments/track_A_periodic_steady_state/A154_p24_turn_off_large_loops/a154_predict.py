"""A154 registered predictions -> a154_predictions.json; prints <= 15 lines.
Whole-run max V_DS = max(turn-on part, turn-off part):
  turn-on part: D68's co-simulated x-curve at x_on = L * d_on;
  turn-off part: A145's single-edge harness, SH1 turned off at the post-step peak current 172 A (A151 / A152 at
  150 / 300 pH: 170-173 A), plus the line-step offset +2.4 V (A152 big300_on9: 57.8 V against the harness's 55.4 V
  at 72 A/ns, 170 A; rail 1 is ~16 V after the step, 12 V in the harness).
Loss per module in the steady window: harness edge + damper energy at 143 A, x 4 phases x 1.98 MHz (A145: the harness
reads ~20 % above the records)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TA = HERE.parent
sys.path.insert(0, str(TA / "A145_p24_finite_switching_edges"))
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
import a145_edge as E  # noqa: E402
_spec = importlib.util.spec_from_file_location("a154_make_cfgs", HERE / "make_cfgs.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

I_POST, OFFSET, F_SW = 172.0, 2.4, 1.0 / 504e-9


def main():
    d68 = json.loads((ROOT / "diagnostics" / "D68_slow_turn_on.json").read_text())
    xs, vs = [c[0] for c in d68["overshoot_curve"]], [c[1] for c in d68["overshoot_curve"]]
    ref, _ = E.turn_off(50, 7, 72.0, i0=143.0)
    p_ref = (ref["e_edge_nj"] + ref["e_loop_nj"]) * 1e-9 * F_SW * 4
    out = {"p_ref_50ph_72_w": p_ref, "rows": {}}
    for l, doff in M.ROWS:
        don = M.d_on(l)
        on_v = float(np.interp(l * don * 1e-3, xs, vs))
        r, _ = E.turn_off(l, 7, doff, i0=I_POST)
        r143, _ = E.turn_off(l, 7, doff, i0=143.0)
        off_v = r["vds_pk"] + OFFSET
        v = max(on_v, off_v)
        p = (r143["e_edge_nj"] + r143["e_loop_nj"]) * 1e-9 * F_SW * 4
        out["rows"][f"f{l}_off{doff:g}"] = dict(l_ph=l, d_off=doff, d_on=don, x_off=l * doff * 1e-3, x_on=l * don * 1e-3,
                                               ton_ns=M.ton_s(don), on_part_v=on_v, off_part_v=off_v, vds_max_v=v,
                                               band=[v - 1.5, v + 1.5], le_40=v <= 40.0, p_off_w=p, p_extra_w=p - p_ref,
                                               p_edge_w=r143["e_edge_nj"] * 1e-9 * F_SW * 4, p_damper_w=r143["e_loop_nj"] * 1e-9 * F_SW * 4)
    (HERE / "a154_predictions.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"reference 50 pH / 72 A/ns: {p_ref:.1f} W per module (harness)")
    for n, q in out["rows"].items():
        print(f"{n}: x_off {q['x_off']:.1f} V, on {q['d_on']:g} A/ns (x_on {q['x_on']:.1f}), ton {q['ton_ns']} -> max V_DS "
              f"{q['vds_max_v']:.1f} V (on {q['on_part_v']:.1f} / off {q['off_part_v']:.1f}; {'<=' if q['le_40'] else '>'} 40), "
              f"loss {q['p_off_w']:.1f} W (+{q['p_extra_w']:.1f}; edge {q['p_edge_w']:.1f})")


if __name__ == "__main__":
    main()
