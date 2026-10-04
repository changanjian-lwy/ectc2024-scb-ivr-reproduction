"""A135 predictions (registered, not criteria): D63 at L x m (A132's d63_design) with scb_vff.v in the RTL's integer
arithmetic (Q8 low-passes by arithmetic shifts, the slope gate, the restoring divider's floor) for three phase-1 caps -
r: relative, cap = ton x ((rss x 333) >> 8) / rail (A135); f: absolute k = 844 800 (as adopted); c: k x m (A134's
calibrated arm). Rows: A124's seven step rows + n0 + x_l_p80_10us (+8 V / 10 us, A130's slope limit), step at 20 us
after A134's warm-up, 1500 periods. Per run: peak after the step, Vo extreme, outcome (A134's lock rule), the number of
periods the cap binds before the step and in the last 200. Writes a135_predictions.json."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.p24_valley_map import DIVERGED_A, ValleyMap, steady_ton  # noqa: E402

spec = importlib.util.spec_from_file_location("a134_predict", HERE.parent / "A134_p24_inductance_cap_lock" / "a134_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
VFF, LSB, K0 = P.VFF, P.LSB, P.K0
REL = 333                                                         # 1 + mu = 1.30 in Q8
MS = (0.7, 0.85, 1.0, 1.15, 1.3)
ROWS = dict(P.ROWS) | {"x_l_p80_10us": ("line", 8.0, 10.0)}
ARMS = {"r": lambda m: {"rel": REL}, "f": lambda m: {"k": K0}, "c": lambda m: {"k": round(K0 * m)}}


class VffRTL:
    """scb_vff.v per Vin sample (vin_valid at phase 1's turn-on): (scale, cap) for the next period; ton is the loop's."""

    def __init__(self, k=0, rel=0):
        self.k, self.rel, self.s = k, rel, None

    def __call__(self, vin, ton_s):
        v = round(vin / VFF["vin_lsb_v"])
        v8, vo8 = v << 8, round(1.0 / VFF["vin_lsb_v"]) << 8
        s = self.s
        if s is None:
            lp2n = lp20n = vpred = v8
            s = self.s = {"gate": False, "cap": None}
        else:
            lp2n = s["lp2"] + ((v8 - s["lp2"]) >> VFF["sh2"])
            lp20n = s["lp20"] + ((v8 - s["lp20"]) >> VFF["sh20"])
            vpred = 2 * v8 - (s["vprev"] << 8)
        gn = max(lp2n - v8, 0)
        gate = True if gn >= VFF["gth"] << 8 else (False if gn == 0 else s["gate"])
        rail = vpred - ((lp20n * 3) >> 2) - vo8
        rss = lp20n - ((lp20n * 3) >> 2) - vo8
        cap_prev, ton = s["cap"], round(ton_s / LSB)
        if rail > 0 and self.rel and rss > 0:
            s["cap"] = min(ton * ((rss * self.rel) >> 8), 2 ** 32 - 1) // rail
        elif rail > 0 and not self.rel and self.k:
            s["cap"] = (self.k << 8) // rail
        else:
            s["cap"] = None
        s.update(lp2=lp2n, lp20=lp20n, vprev=v, gate=gate)
        g = gn if gate else 0
        scale = [1 + max(min(c * g, 1 << 22), -(1 << 23)) / 2 ** 24 for c in VFF["c"]]
        return scale, [cap_prev * LSB if cap_prev is not None else math.inf] + [math.inf] * 3


def run(m, law, row):
    d = P.A132.d63_design(1.0, m, 15.625)
    mw = ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = law(d.vin, ton); ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    vm = ValleyMap(d)
    for _ in range(200):
        sc, cap = law(d.vin, ton); ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    s["t"], recs, div, st = 0.0, [], False, ROWS[row]
    while len(recs) < P.N_RUN:
        t = s["t"]
        vin, i_step = d.vin, 0.0
        if st[0] == "line":
            vin += st[1] * min(max((t - P.T_STEP) / (st[2] * 1e-6), 0.0), 1.0)
        elif st[0] == "load" and t >= P.T_STEP:
            i_step = st[1]
        sc, cap = law(vin, ton)
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap)
        ton, r["vin"], r["bind"] = r["ton"], vin, cap[0] < r["ton"] * sc[0]
        recs.append(r)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"]):
            div = True
            break
    a, tail = [r for r in recs if r["t"] >= P.T_STEP], recs[-200:]
    dev = max(P.ladder_dev(r, r["vin"]) for r in tail)
    vo_end = float(np.mean([r["vo"] for r in tail]))
    return {"peak_a": float(max(max(r["peak"]) for r in a)), "extreme_mv": float(1e3 * max((r["vo"] - 1.0 for r in a), key=abs)),
            "outcome": "diverged" if div else ("lock" if dev > 0.01 or vo_end < 0.99 else "ok"), "ladder_dev_end": float(dev),
            "bind_pre": int(sum(r["bind"] for r in recs if r["t"] < P.T_STEP)), "bind_tail": int(sum(r["bind"] for r in tail))}


def main():
    out = {"rel_q8": REL, "ms": MS, "runs": {}}
    for arm, kw in ARMS.items():
        for m in MS:
            for row in ROWS:
                out["runs"][f"{arm}{round(m * 100):03d}_{row}"] = run(m, VffRTL(**kw(m)), row)
    (HERE / "a135_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    R = out["runs"]
    for arm in ARMS:
        for m in MS:
            rs = {row: R[f"{arm}{round(m * 100):03d}_{row}"] for row in ROWS}
            a124 = [x["peak_a"] for row, x in rs.items() if not row.startswith("x_")]
            bad = [row for row, x in rs.items() if x["outcome"] != "ok"]
            print(f"{arm} L x{m:4.2f}: A124 rows pk {max(a124):4.0f} A, +8V/10us {rs['x_l_p80_10us']['peak_a']:4.0f} A, "
                  f"bind pre/tail {max(x['bind_pre'] for x in rs.values())}/{max(x['bind_tail'] for x in rs.values())}, not ok: {','.join(bad) or '-'}")


if __name__ == "__main__":
    main()
