"""A140 D63 mechanism scan (cheap check before the cosim runs): post-step peak vs line-step slew for the adopted
single-module design (D63 + scb_vff in the RTL's integer arithmetic, A136's low-pass relative cap), with one vff block
or parameter changed at a time. Lines: F = L x 1.0, Cs x 1.0, -4.8 V, slew 1-6 us; R = L x 0.7, Cs x 1.0, +4.8 V,
slew 1-20 us (stage s1); s2 sweeps gth on -4.8 / -6.4 / -8 V at L x 0.7 / 1.0 / 1.3; s3 sweeps sh20 on +4.8 / +8 V
up to 100 us. Each point is the mean / max over 8 step positions within one period. D63's falling-step error is large
(A139: +7.8 +- 19.6 A), so these curves locate mechanisms; they do not set numbers. Writes a140_d63_<stage>.json.
Usage: a140_d63.py [stage] [jobs]"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


Q = _load("a136_predict", TA / "A136_p24_relative_cap_lowpass" / "a136_predict.py")
P, PP = Q.P, Q.P.P           # a135_predict (VffRTL, ValleyMap), a134_predict (A132, VFF, LSB, T_STEP, N_RUN)
VFF, LSB = PP.VFF, PP.LSB
BASE = {"c": list(VFF["c"]), "sh2": VFF["sh2"], "sh20": VFF["sh20"], "gth": VFF["gth"], "rel": 320, "lp": 1, "cap": 1}
N_POS, PERIOD = 8, 0.5e-6


class Vff:
    """scb_vff.v per Vin sample with every parameter exposed (base = Q.VffLP() bit for bit); .last holds internals."""

    def __init__(self, p):
        self.p, self.s, self.tlp, self.last = p, None, None, {}

    def __call__(self, vin, ton_s):
        p = self.p
        t = round(ton_s / LSB)
        if p["lp"]:
            t8 = t << 8
            self.tlp = t8 if self.tlp is None else self.tlp + ((t8 - self.tlp) >> p["sh20"])
            t = self.tlp >> 8
        v = round(vin / VFF["vin_lsb_v"])
        v8, vo8 = v << 8, round(1.0 / VFF["vin_lsb_v"]) << 8
        s = self.s
        if s is None:
            lp2n = lp20n = vpred = v8
            s = self.s = {"gate": False, "cap": None}
        else:
            lp2n = s["lp2"] + ((v8 - s["lp2"]) >> p["sh2"])
            lp20n = s["lp20"] + ((v8 - s["lp20"]) >> p["sh20"])
            vpred = 2 * v8 - (s["vprev"] << 8)
        gn = max(lp2n - v8, 0)
        gate = True if gn >= p["gth"] << 8 else (False if gn == 0 else s["gate"])
        rail = vpred - ((lp20n * 3) >> 2) - vo8
        rss = lp20n - ((lp20n * 3) >> 2) - vo8
        cap_prev = s["cap"]
        s["cap"] = min(t * ((rss * p["rel"]) >> 8), 2 ** 32 - 1) // rail if (p["cap"] and rail > 0 and rss > 0) else None
        s.update(lp2=lp2n, lp20=lp20n, vprev=v, gate=gate)
        g = gn if gate else 0
        scale = [1 + max(min(c * g, 1 << 22), -(1 << 23)) / 2 ** 24 for c in p["c"]]
        self.last = {"g": gn / 256, "gate": gate, "tlp": t, "rail": rail / 256, "rss": rss / 256}
        return scale, [cap_prev * LSB if cap_prev is not None else math.inf] + [math.inf] * 3


def run(m, c, dv, slew, p, pos=0, trace=False):
    """D63 run as a138_run.prior with the step at T_STEP + pos/N_POS of a period; returns a summary (and a trace)."""
    d = PP.A132.d63_design(1.0, m, 15.625)
    d = replace(d, cs=d.cs * c)
    law = Vff(p)
    mw = P.ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(P.steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = law(d.vin, ton); ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    vm = P.ValleyMap(d)
    for _ in range(200):
        sc, cap = law(d.vin, ton); ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    ts = PP.T_STEP + pos / N_POS * PERIOD
    s["t"], out, tr = 0.0, {"peak": 0.0, "ph": None, "t_pk_us": None, "gate_n": 0, "t_gate_us": None, "g_max": 0.0,
                            "bind_n": 0, "div": False}, []
    for _ in range(PP.N_RUN):
        t = s["t"]
        vin = d.vin + dv * min(max((t - ts) / (slew * 1e-6), 0.0), 1.0)
        sc, cap = law(vin, ton)
        r = vm.period(s, vin, 0.0, ton_scale=sc, ton_cap=cap)
        ton, L = r["ton"], law.last
        if not all(math.isfinite(v) and abs(v) < P.DIVERGED_A for v in r["valley"] + r["peak"]):
            out.update(div=True, peak=260.0)
            break
        if r["t"] >= ts:
            k = int(np.argmax(r["peak"]))
            if r["peak"][k] > out["peak"]:
                out.update(peak=float(r["peak"][k]), ph=k + 1, t_pk_us=(r["t"] - ts) * 1e6)
            out["g_max"] = max(out["g_max"], L["g"])
            if L["gate"]:
                out["gate_n"] += 1
                out["t_gate_us"] = out["t_gate_us"] if out["t_gate_us"] is not None else (r["t"] - ts) * 1e6
            out["bind_n"] += int(cap[0] < r["ton"] * sc[0] + 1e-15)
            if trace and r["t"] < ts + 60e-6:
                tr.append({"t_us": (r["t"] - ts) * 1e6, "vin": vin, "ton_ns": r["ton"] * 1e9, "peak": r["peak"],
                           "valley": r["valley"], "rails": r["rails"], "scale1": sc[0], "cap_ns": cap[0] * 1e9,
                           **L})
    return (out, tr) if trace else out


SL20 = [round(float(x), 2) for x in 10 ** np.linspace(0, math.log10(20), 25)]
SL100 = [round(float(x), 2) for x in 10 ** np.linspace(0, 2, 30)]
GTH = {"base": {}} | {f"gth{g}": {"gth": g} for g in (75, 60, 50, 40, 30, 0)} | {"noff": {"c": [0, 0, 0, 0]}}
SH20 = {"base": {}, "off": {"c": [0, 0, 0, 0], "cap": 0}, "sh20_7": {"sh20": 7}, "sh20_8": {"sh20": 8}}
# stage -> {line: ((m, c, dv, slews), variants)}
STAGES = {
    "s1": {"F": ((1.0, 1.0, -4.8, [round(x, 2) for x in np.arange(1.0, 6.01, 0.1)]),
                 {"base": {}, "gth0": {"gth": 0}, "gth50": {"gth": 50}, "gth65": {"gth": 65}, "gth80": {"gth": 80},
                  "noff": {"c": [0, 0, 0, 0]}, "nocap": {"cap": 0}, "sh2_1": {"sh2": 1}, "sh2_3": {"sh2": 3},
                  "off": {"c": [0, 0, 0, 0], "cap": 0}}),
           "R": ((0.7, 1.0, 4.8, SL20),
                 {"base": {}, "nocap": {"cap": 0}, "nolp": {"lp": 0}, "sh20_5": {"sh20": 5}, "sh20_7": {"sh20": 7},
                  "rel288": {"rel": 288}, "rel352": {"rel": 352}, "off": {"c": [0, 0, 0, 0], "cap": 0}})},
    "s2": {f"F{m}_{a}": ((m, 1.0, -a, SL20), GTH) for m in (0.7, 1.0, 1.3) for a in (4.8, 6.4, 8.0)},
    "s3": {f"R{m}_{a}": ((m, 1.0, a, SL100), SH20) for m in (0.7, 1.0, 1.3) for a in (4.8, 8.0)},
}
def job(a):
    stage, line, var, slew, pos = a
    (m, c, dv, _), var_map = STAGES[stage][line]
    return a, run(m, c, dv, slew, BASE | var_map[var], pos)


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "s1"
    jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    lines = STAGES[stage]
    # identity: base Vff = Q.VffLP() through a138_run.prior's loop (A138 grid point L 1.0 Cs 1.0 -4.8 V 2.264 us)
    a138 = _load("a138_run", HERE.parents[2] / "extensions/ml_design_assist/experiments/A138_gp_boundary_map/a138_run.py")
    ident = [a138.prior((1.0, 1.0, -4.8, 2.264)), run(1.0, 1.0, -4.8, 2.264, BASE)["peak"]]
    t0 = time.time()
    tasks = [(stage, ln, v, sl, k) for ln, (spec, var_map) in lines.items() for v in var_map for sl in spec[3]
             for k in range(N_POS)]
    with Pool(jobs) as pool:
        res = pool.map(job, tasks, chunksize=8)
    out = {"stage": stage, "identity_prior_vs_base": ident, "lines": {k: v[0][:3] for k, v in lines.items()},
           "n_pos": N_POS, "curves": {}}
    for ln, (spec, var_map) in lines.items():
        for v in var_map:
            rows = []
            for sl in spec[3]:
                rs = [r for (a, r) in res if a[1] == ln and a[2] == v and a[3] == sl]
                pk = [r["peak"] for r in rs]
                rows.append({"slew": sl, "mean": float(np.mean(pk)), "max": float(np.max(pk)), "min": float(np.min(pk)),
                             "gate_frac": float(np.mean([r["gate_n"] > 0 for r in rs])),
                             "g_max": float(np.mean([r["g_max"] for r in rs])),
                             "bind": float(np.mean([r["bind_n"] for r in rs])),
                             "ph": [r["ph"] for r in rs], "t_pk_us": float(np.median([r["t_pk_us"] for r in rs]))})
            out["curves"][f"{ln}_{v}"] = rows
    (HERE / f"a140_d63_{stage}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"identity prior {ident[0]:.4f} vs base {ident[1]:.4f}; {len(tasks)} runs, {time.time() - t0:.0f} s")
    for key, rows in list(out["curves"].items())[:12]:
        mean = np.array([r["mean"] for r in rows])
        k = int(np.argmax(mean))
        rise = float(np.max(np.maximum.accumulate(mean[::-1])[::-1] - mean))    # worst later-minus-earlier rise
        print(f"{key:10s} max {mean[k]:6.1f} @ {rows[k]['slew']:5.2f} us; first {mean[0]:6.1f} last {mean[-1]:6.1f}; "
              f"rise with slower slew {rise:5.1f} A")


if __name__ == "__main__":
    main()
