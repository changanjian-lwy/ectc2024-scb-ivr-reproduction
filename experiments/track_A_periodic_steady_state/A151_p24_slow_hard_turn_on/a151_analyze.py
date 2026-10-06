"""A151 analysis against BOUNDARY Section 2 -> a151_summary.json. Per run A148's stats (V_DS windows, peaks, oracle,
late, Vo) and the channel's edge power over 900-1000 us; references are A145's 72 A/ns records of the same rows.
Criterion 1 compares the change in whole-run max V_DS on l_p48_1us with the harness's SH2 change (a151_screen.json,
V_on 17 V, Q 7). Prints <= 15 lines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "extensions" / "ml_design_assist" / "experiments" / "A148_rl_zvs_line_step"))
import a148_analyze as A  # noqa: E402

COS = HERE / "cosim"
A145C = HERE.parent / "A145_p24_finite_switching_edges" / "cosim"
PLAN = {50: ((36, 18), ("l_p48_1us", "n0", "s_p62")), 100: ((36, 18, 9), ("l_p48_1us", "n0", "s_p62")),
        150: ((18, 9), ("l_p48_1us", "n0"))}


def run_stats(path):
    r = A.load(path)
    s = A.stats(r)
    secs = [q for q in r["sections"] if 900e-6 <= q["t_s"] < 1000e-6 and "edge_energy_j" in q]
    s["edge_w"] = float(np.sum([np.sum(q["edge_energy_j"]) for q in secs]) / 100e-6) if secs else None
    return {k: s.get(k) for k in ("status", "src_modified", "peak_post", "oracle_new", "late", "back_within_1pct_us",
                                  "extreme_mv", "vo_mean_pre_mv", "vds", "edge_w", "von_max")}


def main():
    scr = {(r["l_ph"], r["q"], r["case"], r["didt_on"]): r for r in json.loads((HERE / "a151_screen.json").read_text())}
    runs, ref = {}, {}
    for l, (ds, rows) in PLAN.items():
        for row in rows:
            ref[(l, row)] = run_stats(A145C / f"run_e72_l{l}_{row}.json")
            for d in ds:
                p = COS / f"run_on{d}_l{l}_{row}.json"
                runs[(l, d, row)] = run_stats(p) if p.exists() else None
    # 1. harness transfer
    c1 = []
    for l, (ds, _) in PLAN.items():
        for d in ds:
            r = runs[(l, d, "l_p48_1us")]
            if r is None:
                continue
            dc = r["vds"]["whole"] - ref[(l, "l_p48_1us")]["vds"]["whole"]
            dp = r["vds"]["post"] - ref[(l, "l_p48_1us")]["vds"]["post"]
            dh = scr[(l, 7, "v17", d)]["sh2_v"] - scr[(l, 7, "v17", 72)]["sh2_v"]
            c1.append({"l": l, "d": d, "cosim_whole": dc, "cosim_post": dp, "harness": dh, "ok": abs(dc - dh) <= 2.0})
    out = {"c1": {"pairs": c1, "pass": sum(x["ok"] for x in c1) >= 5}}

    def ctl(l, d):
        bad = []
        for row in PLAN[l][1]:
            r, f = runs[(l, d, row)], ref[(l, row)]
            if r is None or r["status"] != "COMPLETED" or r["src_modified"] is not False:
                bad.append(f"{row} status")
                continue
            if r["peak_post"] > min(f["peak_post"] + 5.0, 200.0):
                bad.append(f"{row} peak {r['peak_post']:.1f}")
            if r["oracle_new"]:
                bad.append(f"{row} NEW {r['oracle_new']}")
            if sum(r["late"]) > sum(f["late"]) + 2:
                bad.append(f"{row} late {sum(r['late'])}")
            if r["back_within_1pct_us"] > f["back_within_1pct_us"] + 2.0:
                bad.append(f"{row} back {r['back_within_1pct_us']:.1f}")
            if row == "n0" and abs(r["vo_mean_pre_mv"] - f["vo_mean_pre_mv"]) > 0.5:
                bad.append("n0 Vo")
        return bad
    for k, l in (("c2", 50), ("c3", 100)):
        ds = PLAN[l][0]
        ok = [d for d in ds if all(runs[(l, d, row)] is not None and runs[(l, d, row)]["vds"]["whole"] <= 40.0
                                   for row in PLAN[l][1])]
        d = max(ok) if ok else None
        out[k] = {"pass": d is not None, "didt_on": d,
                  "whole": {dd: {row: runs[(l, dd, row)]["vds"]["whole"] if runs[(l, dd, row)] else None
                                 for row in PLAN[l][1]} for dd in ds}}
        if d is not None:
            bad = ctl(l, d)
            n0, f0 = runs[(l, d, "n0")], ref[(l, "n0")]
            ew = n0["edge_w"] - f0["edge_w"]
            out[k].update(c4={"pass": not bad, "bad": bad}, c5={"pass": ew <= 0.5, "edge_w_delta": ew})
    out["c150"] = {d: {row: runs[(150, d, row)]["vds"]["whole"] if runs[(150, d, row)] else None for row in PLAN[150][1]}
                   for d in PLAN[150][0]}
    out["edge_w"] = {f"l{l}_d{d}": runs[(l, d, "n0")]["edge_w"] for l, (ds, _) in PLAN.items() for d in ds
                     if runs[(l, d, "n0")]}
    out["edge_w_ref"] = {f"l{l}": ref[(l, "n0")]["edge_w"] for l in PLAN}
    slew = {}
    for l in (50, 100):
        p = COS / f"run_s5_l{l}_l_p48.json"
        if p.exists():
            s = run_stats(p)
            slew[l] = {"whole": s["vds"]["whole"], "post": s["vds"]["post"], "peak": s["peak_post"], "new": s["oracle_new"]}
    out["slew5"] = slew
    out["runs"] = {f"on{d}_l{l}_{row}": v for (l, d, row), v in runs.items()}
    (HERE / "a151_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"C1 {sum(x['ok'] for x in c1)}/{len(c1)} ({'PASS' if out['c1']['pass'] else 'FAIL'}): " + "; ".join(
        f"L{x['l']} {x['d']}: {x['cosim_whole']:+.1f} (post {x['cosim_post']:+.1f}) vs {x['harness']:+.1f}" for x in c1))
    for k, l in (("c2", 50), ("c3", 100)):
        c = out[k]
        print(f"{k.upper()} {l} pH: {'PASS at ' + str(c['didt_on']) + ' A/ns' if c['pass'] else 'FAIL'}; whole " + "; ".join(
            f"{d}: " + "/".join(f"{v:.1f}" if v else "-" for v in w.values()) for d, w in c["whole"].items()))
        if c["pass"]:
            print(f"   C4 {'PASS' if c['c4']['pass'] else 'FAIL ' + str(c['c4']['bad'])}; C5 edge W {c['c5']['edge_w_delta']:+.2f} "
                  f"({'PASS' if c['c5']['pass'] else 'FAIL'})")
    print("150 pH whole (l_p48/n0):", {d: [round(v, 1) for v in w.values() if v] for d, w in out["c150"].items()})
    print("edge W n0:", {k: round(v, 2) for k, v in out["edge_w"].items()}, "ref", {k: round(v, 2) for k, v in out["edge_w_ref"].items()})
    print("+4.8 V / 5 us, 72/72:", {l: {k: round(v, 1) for k, v in s.items()} for l, s in slew.items()})


if __name__ == "__main__":
    main()
