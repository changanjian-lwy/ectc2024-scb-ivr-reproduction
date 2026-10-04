"""A134 predictions (registered, not criteria) and the D63 half of the diagnosis: D63 at L x m (A132's d63_design) with
the RTL-exact feed-forward of scb_vff.v (A128's law_rtl: phase 1's cap round(k / rail) LSB from the previous Vin
sample; A129's slope gate on the falling term in Q8 integers), for three arms - f: k as adopted (L0 x 180 A, the
nominal L), z: k = 0 (no cap, the falling term kept), c: k x m (the cap calibrated to the part's L). Rows: A124's seven
step rows + n0, step at 20 us after an 800-period warm-up (600 comparator, 200 timed), 1500 periods after the start.
Per run: peak after the step, Vo extreme and final, final rails and valleys, phase 1's final Ton vs the loop's, and the
outcome: lock if the ladder deviation max |Vc_k / Vin - (N - k) / N| (A106) over the last 200 periods is > 1 %, or the
mean Vo there is < 0.99 V; diverged past D63's validity; else ok. Writes a134_predictions.json."""
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
from scb_ivr.extensions.ml_rl_ff import A124_ROWS  # noqa: E402
from scb_ivr.p24_valley_map import DIVERGED_A, ValleyMap, steady_ton  # noqa: E402

spec = importlib.util.spec_from_file_location("a132_predict", HERE.parent / "A132_p24_neg_current_autotune" / "a132_predict.py")
A132 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A132)
VFF = json.loads((PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim/cfg_g125_n0.json").read_text())["vff"]
LSBV, LSB, VO = VFF["vin_lsb_v"], 4e-9 / 128, round(1.0 / VFF["vin_lsb_v"])
K0 = VFF["k"]
MS = (0.7, 0.85, 0.9, 1.0, 1.05, 1.1, 1.2, 1.3)
ARMS = {"f": lambda m: K0, "z": lambda m: 0, "c": lambda m: round(K0 * m)}
ROWS = {k.split("_", 1)[1]: v for k, v in A124_ROWS.items()} | {"n0": ("none",)}
T_STEP, N_RUN = 20e-6, 1500


class Law:
    """scb_vff.v per Vin sample: (scale per phase, cap per phase) for the period that starts at the sample."""

    def __init__(self, k):
        self.k, self.st = k, {}

    def __call__(self, vin):
        st, v = self.st, round(vin / LSBV)
        if not st:
            st.update(lp2=v, lp20=v, cap=None, vp=v, q2=v * 256, gate=False)
        cap_prev = st["cap"]
        st["lp2"] += (v - st["lp2"]) / 2 ** VFF["sh2"]
        st["lp20"] += (v - st["lp20"]) / 2 ** VFF["sh20"]
        g = max(st["lp2"] - v, 0.0)
        scale = [min(max(1 + c * g / 65536, 0.5), 1.25) for c in VFF["c"]]
        rail = (2 * v - st["vp"]) - 0.75 * st["lp20"] - VO
        st["vp"] = v
        st["cap"] = round(self.k / rail) * LSB if (rail > 0 and self.k > 0) else math.inf
        st["q2"] += (v * 256 - st["q2"]) >> VFF["sh2"]
        g8 = max(st["q2"] - v * 256, 0)
        st["gate"] = True if g8 >= VFF["gth"] * 256 else (False if g8 == 0 else st["gate"])
        return (scale if st["gate"] else [1.0] * 4), [cap_prev if cap_prev is not None else math.inf] + [math.inf] * 3


def ladder_dev(r, vin):
    vc = np.cumsum(r["rails"][::-1])[::-1][1:]                       # Vc_k = rails k+1..N
    return max(abs(vc[j] / vin - (3 - j) / 4) for j in range(3))


def run(m, k, row):
    d = A132.d63_design(1.0, m, 15.625)
    law = Law(k)
    mw = ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(steady_ton(d))
    for _ in range(600):
        sc, cap = law(d.vin); mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)
    vm = ValleyMap(d)
    for _ in range(200):
        sc, cap = law(d.vin); vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)
    s["t"], recs, div = 0.0, [], False
    st = ROWS[row]
    while len(recs) < N_RUN:
        t = s["t"]
        vin, i_step = d.vin, 0.0
        if st[0] == "line":
            vin += st[1] * min(max((t - T_STEP) / (st[2] * 1e-6), 0.0), 1.0)
        elif st[0] == "load" and t >= T_STEP:
            i_step = st[1]
        sc, cap = law(vin)
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap)
        r["ton1"], r["vin"] = min(r["ton"] * sc[0], cap[0]), vin
        recs.append(r)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"]):
            div = True
            break
    a = [r for r in recs if r["t"] >= T_STEP]
    tail = recs[-200:]
    dev = max(ladder_dev(r, r["vin"]) for r in tail)
    vo_end = float(np.mean([r["vo"] for r in tail]))
    out = "diverged" if div else ("lock" if dev > 0.01 or vo_end < 0.99 else "ok")
    return {"peak_a": float(max(max(r["peak"]) for r in a)), "extreme_mv": float(1e3 * max((r["vo"] - 1.0 for r in a), key=abs)),
            "vo_end": vo_end, "ladder_dev_end": float(dev), "outcome": out,
            "rails_end_v": [float(np.mean([r["rails"][j] for r in tail])) for j in range(4)],
            "valley_end_a": [float(np.mean([r["valley"][j] for r in tail])) for j in range(4)],
            "ton_end_ns": float(tail[-1]["ton"] * 1e9), "ton1_end_ns": float(tail[-1]["ton1"] * 1e9)}


def main():
    out = {"k0": K0, "ms": MS, "runs": {}}
    for arm, kf in ARMS.items():
        for m in MS:
            for row in ROWS:
                out["runs"][f"{arm}{round(m * 100):03d}_{row}"] = run(m, kf(m), row)
    (HERE / "a134_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    R = out["runs"]
    for arm in ARMS:
        for m in MS:
            rs = {row: R[f"{arm}{round(m * 100):03d}_{row}"] for row in ROWS}
            bad = [row for row, r in rs.items() if r["outcome"] != "ok"]
            print(f"{arm} L x{m:4.2f}: pk {max(r['peak_a'] for r in rs.values()):4.0f} A, not ok: {','.join(bad) or '-'}")


if __name__ == "__main__":
    main()
