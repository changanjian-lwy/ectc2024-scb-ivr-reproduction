"""A224's cheaper check (D63, not criteria): A223's D63 setup (a223_predict: L0, the final Ton limits, the gated cap
g25) with the voltage loop's derivative term (Design.kd_ns, dead band kd_db codes) at kd 0 / 355 / 530 ns/V, dead
band 2 (and 3 at 355 / 530); rows: A223's. Per run also Vo's peak-to-peak 5-25 us after the event (the ring) and the
time after which Vo stays within 1 %.
    python3 a224_predict.py -> a224_predictions.json"""
from __future__ import annotations

import importlib.util
import json
import math
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a223_predict", HERE.parent / "A223_p24_cap_on_rising_vin" / "a223_predict.py")
P = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P)
ARMS = {"k0": (0.0, 2), "k355": (355.0, 2), "k530": (530.0, 2), "k355b3": (355.0, 3), "k530b3": (530.0, 3)}
ROWS = [r for r in P.ROWS if not r.startswith("l_p48_50")]


def run(args):
    arm, row = args
    kd, db = ARMS[arm]
    st = P.ROWS[row]
    d = replace(P.P.P.A132.d63_design(1.0, 1.0, 15.625), r_load=1.0 / st[-1], kd_ns=kd, kd_db=db)
    law = P.Cap("gate", thr=25)
    mw, vm = P.ValleyMap(replace(d, mode="cmp")), P.ValleyMap(d)
    for m in (mw, vm):
        m.ton_min, m.ton_max = 4e-9, 2 * 44.48e-9
    s = mw.init_state(P.steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = law(d.vin, ton); ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    for _ in range(200):
        sc, cap = law(d.vin, ton); ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    s["t"], recs = 0.0, []
    while len(recs) < P.N_RUN:
        t = s["t"]
        vin, i_step = d.vin, 0.0
        if st[0] == "line":
            vin += st[1] * min(max((t - P.T_STEP) / (st[2] * 1e-6), 0.0), 1.0)
        elif t >= P.T_STEP:
            i_step = st[1]
        sc, cap = law(vin, ton)
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap)
        ton = r["ton"]
        recs.append(r)
        if not all(math.isfinite(x) and abs(x) < P.DIVERGED_A for x in r["valley"] + r["peak"]):
            break
    a = [r for r in recs if r["t"] >= P.T_STEP]
    ring = [r["vo"] for r in a if 5e-6 <= r["t"] - P.T_STEP < 25e-6]
    back = next((r["t"] - P.T_STEP for i, r in enumerate(a) if all(abs(x["vo"] - 1.0) <= 0.01 for x in a[i:])), None)
    return arm, row, {"peak_a": float(max(max(r["peak"]) for r in a)), "extreme_mv": float(1e3 * max((r["vo"] - 1.0 for r in a), key=abs)),
                      "valley_max_a": float(max(max(r["valley"]) for r in a)), "ring_pp_mv": float(1e3 * (max(ring) - min(ring))),
                      "back_us": None if back is None else float(1e6 * back)}


def main():
    with Pool(10) as p:
        res = p.map(run, [(a, r) for a in ARMS for r in ROWS])
    out = {"arms": ARMS, "runs": {f"{a}|{r}": v for a, r, v in res}}
    (HERE / "a224_predictions.json").write_text(json.dumps(out, indent=1) + "\n")
    R = out["runs"]
    print("row          " + "".join(f"{a:>24s}" for a in ARMS) + "   (peak A / Vo extreme mV / ring pp mV / back us)")
    for r in ROWS:
        print(f"{r:12s} " + "".join(f"{R[f'{a}|{r}']['peak_a']:5.0f}/{R[f'{a}|{r}']['extreme_mv']:+4.0f}/{R[f'{a}|{r}']['ring_pp_mv']:5.1f}/{R[f'{a}|{r}']['back_us'] or -1:4.0f}".rjust(24) for a in ARMS))


if __name__ == "__main__":
    main()
