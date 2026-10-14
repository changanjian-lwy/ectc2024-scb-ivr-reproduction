"""A223's cheaper check (D63, not criteria): phase 1's relative cap (scb_vff, A136: tlp x 1.25 x rss / rail on ton's
low-pass) in the RTL's integer arithmetic, four arms - lp: as adopted; none: no cap; common: the same cap on all four
phases; g<thr>: the cap only at samples where rail - rss >= thr Vin codes, tlp restarting from ton at the others (A223's
rgth). D63 at L0 (A132's d63_design) with the final configuration's Ton limits (4 ns, 2 x 44.48 ns); rows: A124's
line and load rows at full load, +8 V / 10 us, and load re-applications from 5-75 % (r_load set to the start load),
step at 20 us after the warm-up (600 comparator + 200 timed periods), 1500 periods. Also, per rising line row, the
periods in which the adopted cap binds and those in which rail - rss stays >= 25 codes.
    python3 a223_predict.py -> a223_predictions.json"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from scb_ivr.p24_valley_map import DIVERGED_A, ValleyMap, steady_ton  # noqa: E402

spec = importlib.util.spec_from_file_location("a135_predict", HERE.parent / "A135_p24_relative_cap" / "a135_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
VFF, LSB = P.VFF, P.LSB
T_STEP, N_RUN, THR_LEVELS = 20e-6, 1500, (100, 50, 25, 10)
ROWS = {k.split("_", 1)[1]: v + (250.0,) for k, v in P.P.ROWS.items() if k != "n0"} | {
    "l_p80_10us": ("line", 8.0, 10.0, 250.0), "l_p48_20us": ("line", 4.8, 20.0, 250.0), "l_p48_50us": ("line", 4.8, 50.0, 250.0),
    "w20_p200": ("load", 200.0, 50.0), "w20_p150": ("load", 150.0, 50.0), "w20_p100": ("load", 100.0, 50.0),
    "w5_p237": ("load", 237.5, 12.5), "w50_p125": ("load", 125.0, 125.0), "w75_p62": ("load", 62.5, 187.5),
    "w30_p62": ("load", 62.5, 75.0)}
ARMS = {"lp": dict(mode="lp"), "none": dict(mode="none"), "common": dict(mode="common"),
        "g10": dict(mode="gate", thr=10), "g25": dict(mode="gate", thr=25), "g50": dict(mode="gate", thr=50)}


class Cap:
    """scb_vff per Vin sample: (scale per phase, cap per phase) for the period that starts at the sample."""

    def __init__(self, mode, rel=320, thr=0):
        self.mode, self.rel, self.thr, self.s, self.open, self.d = mode, rel, thr, None, False, 0

    def __call__(self, vin, ton_s):
        v = round(vin / VFF["vin_lsb_v"])
        v8, vo8, t8 = v << 8, round(1.0 / VFF["vin_lsb_v"]) << 8, round(ton_s / LSB) << 8
        s = self.s
        if s is None:
            lp2n = lp20n = vpred = v8
            s = self.s = {"gate": False, "cap": None, "tlp": t8}
        else:
            lp2n = s["lp2"] + ((v8 - s["lp2"]) >> VFF["sh2"])
            lp20n = s["lp20"] + ((v8 - s["lp20"]) >> VFF["sh20"])
            vpred = 2 * v8 - (s["vprev"] << 8)
        gn = max(lp2n - v8, 0)
        gate = True if gn >= VFF["gth"] << 8 else (False if gn == 0 else s["gate"])
        rail = vpred - ((lp20n * 3) >> 2) - vo8
        rss = lp20n - ((lp20n * 3) >> 2) - vo8
        self.d = rail - rss
        self.open = self.mode != "gate" or self.d >= self.thr << 8
        tlp = s["tlp"] + ((t8 - s["tlp"]) >> VFF["sh20"]) if self.open else t8
        on = self.mode != "none" and self.open
        cap_prev = s["cap"]
        s["cap"] = min((tlp >> 8) * ((rss * self.rel) >> 8), 2 ** 32 - 1) // rail if (on and rail > 0 and rss > 0) else None
        s.update(lp2=lp2n, lp20=lp20n, vprev=v, gate=gate, tlp=tlp)
        g = gn if gate else 0
        scale = [1 + max(min(c * g, 1 << 22), -(1 << 23)) / 2 ** 24 for c in VFF["c"]]
        c = cap_prev * LSB if cap_prev is not None else math.inf
        return scale, ([c] * 4 if self.mode == "common" else [c] + [math.inf] * 3)


def run(args):
    arm, row = args
    st = ROWS[row]
    d = replace(P.P.A132.d63_design(1.0, 1.0, 15.625), r_load=1.0 / st[-1])
    law = Cap(**ARMS[arm])
    mw, vm = ValleyMap(replace(d, mode="cmp")), ValleyMap(d)
    for m in (mw, vm):
        m.ton_min, m.ton_max = 4e-9, 2 * 44.48e-9
    s = mw.init_state(steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = law(d.vin, ton); ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    for _ in range(200):
        sc, cap = law(d.vin, ton); ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    s["t"], recs, div, ton_pre = 0.0, [], False, ton
    while len(recs) < N_RUN:
        t = s["t"]
        vin, i_step = d.vin, 0.0
        if st[0] == "line":
            vin += st[1] * min(max((t - T_STEP) / (st[2] * 1e-6), 0.0), 1.0)
        elif t >= T_STEP:
            i_step = st[1]
        sc, cap = law(vin, ton)
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap)
        ton, r["vin"], r["bind"], r["d"] = r["ton"], vin, cap[0] < r["ton"] * sc[0], law.d
        recs.append(r)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"]):
            div = True
            break
    i0 = next(i for i, r in enumerate(recs) if r["t"] >= T_STEP)
    a, tail = recs[i0:], recs[-200:]
    binds = [i - i0 for i, r in enumerate(recs) if r["bind"]]
    out = {"peak_a": float(max(max(r["peak"]) for r in a)), "valley_max_a": float(max(max(r["valley"]) for r in a)),
           "extreme_mv": float(1e3 * max((r["vo"] - 1.0 for r in a), key=abs)), "rail1_max_v": float(max(r["rails"][0] for r in a)),
           "diverged": div, "ladder_dev_end": float(max(P.P.ladder_dev(r, r["vin"]) for r in tail)),
           "vo_end": float(np.mean([r["vo"] for r in tail])), "binds_after_step": len([b for b in binds if b >= 0]),
           "bind_periods": [min(binds), max(binds)] if binds else None, "ton_before_ns": ton_pre * 1e9}
    if arm == "lp" and st[0] == "line" and st[1] > 0:
        out["d_ge_codes"] = {L: ([min(x), max(x)] if (x := [i - i0 for i, r in enumerate(recs) if r["d"] >= L << 8]) else None)
                             for L in THR_LEVELS}
    return arm, row, out


def main():
    with Pool(10) as p:
        res = p.map(run, [(a, r) for a in ARMS for r in ROWS])
    out = {"rows": ROWS, "arms": ARMS, "runs": {f"{a}|{r}": v for a, r, v in res}}
    (HERE / "a223_predictions.json").write_text(json.dumps(out, indent=1) + "\n")
    R = out["runs"]
    print("row          " + "  ".join(f"{a:>12s}" for a in ARMS) + "   (peak A / Vo extreme mV / binds)")
    for r in ROWS:
        print(f"{r:12s} " + "  ".join(f"{R[f'{a}|{r}']['peak_a']:5.0f}/{R[f'{a}|{r}']['extreme_mv']:+4.0f}/{R[f'{a}|{r}']['binds_after_step']:3d}" for a in ARMS))


if __name__ == "__main__":
    main()
