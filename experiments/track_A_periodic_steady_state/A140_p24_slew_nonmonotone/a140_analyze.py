"""A140 analysis against BOUNDARY Section 2 -> a140_summary.json. Peak and validity as A138 (a138_run.response); the
falling-term gate is reconstructed from the record's ADC Vin samples (one per section, the RTL's vin_valid) in
scb_vff's integer arithmetic: lp2 += (v8 - lp2) >> sh2, g = max(lp2 - v8, 0), latch on at g >= gth << 8, off at 0.
Post hoc: duplicate high-side turn-ons (same phase < 20 ns apart), whether the peak follows one, and the spike-free
envelope (max over periods of the median of three consecutive peaks of the peaking phase)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("make_cfgs", HERE / "make_cfgs.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
A138 = M.D._load("a138_run", PROJECT / "extensions/ml_design_assist/experiments/A138_gp_boundary_map/a138_run.py")
UR01 = PROJECT / M.REUSED["B_L070_p4.8_s20.0"]
DUP_S = 20e-9


def gate(d, t_step_s):
    v = d["cfg"].get("vff")
    if not v:
        return {"open": False, "t_gate_us": None, "g_max": 0.0}
    lsb, sh2, gth = v["vin_lsb_v"], v["sh2"], v["gth"]
    lp2, on, out = None, False, {"open": False, "t_gate_us": None, "g_max": 0.0}
    for q in d["sections"]:
        if q["t_s"] < t_step_s - 100e-6:
            continue
        v8 = round(q["vin_v"] / lsb) << 8
        lp2 = v8 if lp2 is None else lp2 + ((v8 - lp2) >> sh2)
        g = max(lp2 - v8, 0)
        on = True if g >= gth << 8 else (False if g == 0 else on)
        if q["t_s"] >= t_step_s:
            out["g_max"] = max(out["g_max"], g / 256)
            if on and not out["open"]:
                out.update(open=True, t_gate_us=(q["t_s"] - t_step_s) * 1e6)
    return out


def stats(path):
    d = json.loads(Path(path).read_text())
    ts = d["cfg"]["line_step"]["t_us"]
    y, f = A138.response(path, ts)
    ts *= 1e-6
    hi = max((q for q in d["highoffs_last"] if q["t_s"] >= ts), key=lambda q: q["i_a"])
    pre = [q for q in d["sections"] if ts - 50e-6 <= q["t_s"] < ts]
    post = [q for q in d["sections"] if ts <= q["t_s"] < ts + 100e-6]
    # post hoc (RESULTS 0): a second high-side turn-on of the same phase within DUP_S restarts the Ton timer
    ons = [o for o in d["turnons_last"] if o["t_s"] >= ts]
    last, dup = {}, []
    for o in ons:
        if o["phase"] in last and o["t_s"] - last[o["phase"]] < DUP_S:
            dup.append(o)
        last[o["phase"]] = o["t_s"]
    pk_dup = any(o["phase"] == hi["phase"] and 0 < hi["t_s"] - o["t_s"] < 60e-9 for o in dup)
    ys = [q["i_a"] for q in d["highoffs_last"] if q["phase"] == hi["phase"] and q["t_s"] >= ts]
    env3 = max(float(np.median(ys[i:i + 3])) for i in range(len(ys) - 2))
    return {"peak": y, "phase": hi["phase"], "t_pk_us": (hi["t_s"] - ts) * 1e6, **gate(d, ts),
            "dup_on": len(dup), "peak_after_dup": pk_dup, "env3": env3,
            "ton_pre": float(np.mean([q["ton_lsb"] for q in pre])), "ton_max": max(q["ton_lsb"] for q in post),
            "rail1_max": max(q["vin_v"] - q["vcs_v"][0] for q in post), "valid": f["valid"], "late": f["late"],
            "overlaps": f["overlaps"]}


def rise(ys):
    """Worst increase from a faster to a slower slew (ys ordered by slew)."""
    ys = np.asarray(ys)
    return float(np.max(np.maximum.accumulate(ys[::-1])[::-1] - ys))


def line(R, arm, m, dv):
    key = f"{arm}_L{round(m * 100):03d}_{'m' if dv < 0 else 'p'}{abs(dv):.1f}_s"
    pts = sorted((float(n[len(key):]), n) for n in R if n.startswith(key) and "_q" not in n)
    return [s for s, _ in pts], [R[n] for _, n in pts]


def main():
    pred = json.loads((HERE / "a140_predictions.json").read_text())["runs"]
    R = {}
    for n in pred:
        p = PROJECT / M.REUSED[n] if n in M.REUSED else HERE / "cosim" / f"run_{n}.json"
        if p.exists():
            R[n] = stats(p) | {"d63": pred[n]["mean"]}
    out = {"runs": R, "criteria": {}}
    # 1. identity
    a, b = (json.loads(p.read_text()) for p in (HERE / "cosim" / "run_G_L070_p4.8_s20.0.json", UR01))
    same = len(a["sections"]) == len(b["sections"]) and all(
        x["vo"] == y["vo"] and x["ton_lsb"] == y["ton_lsb"] for x, y in zip(a["sections"], b["sections"]))
    out["criteria"]["1_identity"] = {"pass": bool(same), "sections": len(a["sections"])}
    # 2. falling mechanism (B), 3. monotone (G), 4b. envelope
    c2, c3, c4b = {}, {}, {}
    for dv in (-4.8, -6.4):
        sb, rb = line(R, "B", 1.0, dv)
        sg, rg = line(R, "G", 1.0, dv)
        worst = max(rb, key=lambda r: r["peak"])
        opened = [r for r in rb if r["open"]]
        gap = worst["peak"] - opened[0]["peak"] if opened else None
        c2[dv] = {"slews": sb, "peaks": [r["peak"] for r in rb], "open": [r["open"] for r in rb],
                  "g_max": [r["g_max"] for r in rb], "worst_closed": not worst["open"], "gap_a": gap,
                  "pass": bool(not worst["open"] and gap is not None and gap >= 10.0)}
        c3[dv] = {"slews": sg, "peaks": [r["peak"] for r in rg], "open": [r["open"] for r in rg],
                  "rise_a": rise([r["peak"] for r in rg])}
        c3[dv]["pass"] = c3[dv]["rise_a"] <= 3.0
        gb = max(r["peak"] for s, r in zip(sb, rb) if s >= 2.4)
        gg = max(r["peak"] for s, r in zip(sg, rg) if s >= 2.4)
        c4b[dv] = {"B": gb, "G": gg, "pass": gg <= gb}
    out["criteria"]["2_mechanism"] = c2 | {"pass": all(v["pass"] for v in c2.values())}
    out["criteria"]["3_monotone"] = c3 | {"pass": all(v["pass"] for v in c3.values())}
    slow = {n: R[n]["peak"] for n in ("G_L100_m8.0_s10.0", "G_L130_m8.0_s10.0", "G_L130_m8.0_s12.1")}
    out["criteria"]["4_cost"] = {"a": slow, "b": c4b,
                                 "pass": max(slow.values()) <= 190.0 and all(v["pass"] for v in c4b.values())}
    # 5. rising mechanism
    o5, o20 = R["O_L070_p4.8_s5.0"]["peak"], R["O_L070_p4.8_s20.0"]["peak"]
    b20 = [R[n]["peak"] for n in ("B_L070_p4.8_s20.0", "B_L070_p4.8_s20.0_q1", "B_L070_p4.8_s20.0_q2",
                                  "B_L070_p4.8_s20.0_q3")]
    b5 = R["B_L070_p4.8_s5.0"]["peak"]
    out["criteria"]["5_rising"] = {"O_5": o5, "O_20": o20, "B_5": b5, "B_20": b20, "B_20_median": float(np.median(b20)),
                                   "pass": o20 >= o5 + 5 and float(np.median(b20)) >= b5 + 5}
    out["valid_all"] = all(r["valid"] and not r["overlaps"] for r in R.values())
    (HERE / "a140_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    c = out["criteria"]
    print(f"runs {len(R)}, all valid {out['valid_all']}; 1 identity {c['1_identity']['pass']}")
    for dv in (-4.8, -6.4):
        print(f"2 B {dv}: " + " ".join(f"{s}:{p:.1f}{'o' if o else 'c'}" for s, p, o in
                                       zip(c2[dv]['slews'], c2[dv]['peaks'], c2[dv]['open'])) + f" gap {c2[dv]['gap_a']}")
        print(f"3 G {dv}: " + " ".join(f"{s}:{p:.1f}{'o' if o else 'c'}" for s, p, o in
                                       zip(c3[dv]['slews'], c3[dv]['peaks'], c3[dv]['open'])) + f" rise {c3[dv]['rise_a']:.1f}")
    print(f"2 {c['2_mechanism']['pass']}  3 {c['3_monotone']['pass']}  4 {c['4_cost']['pass']} "
          f"(slow {', '.join(f'{v:.1f}' for v in slow.values())}; env B/G " +
          ", ".join(f"{v['B']:.1f}/{v['G']:.1f}" for v in c4b.values()) + ")")
    print(f"5 {c['5_rising']['pass']}: O 5/20 {o5:.1f}/{o20:.1f}; B 5 {b5:.1f}, 20 us x4 {', '.join(f'{v:.1f}' for v in b20)}")
    rest = [n for n in R if n.startswith(("B_L100_m8", "G_L100_m8", "B_L130", "G_L130", "B_L070_m", "G_L070_m",
                                           "B_L070_p8", "B_L070_p4.8_s10", "B_L070_p4.8_s40"))]
    print("dup-on peaks: " + ", ".join(f"{n} {r['peak']:.1f}/{r['env3']:.1f}" for n, r in R.items() if r["peak_after_dup"]))
    print("dup-on counts (runs with any): " + ", ".join(f"{n} {r['dup_on']}" for n, r in R.items() if r["dup_on"]))
    print("other: " + "; ".join(f"{n} {R[n]['peak']:.1f}{'o' if R[n]['open'] else ''}" for n in rest))


if __name__ == "__main__":
    main()
