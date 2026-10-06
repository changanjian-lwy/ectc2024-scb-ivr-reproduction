"""A150 analysis: criteria 1-4 (BOUNDARY), the price of the candidate (or of the closest point when none is feasible),
and the cross-checks: physical trade-off signs of the final GP means, A143's phases 2-4 valley signature on the 5 us
rows, the SH-block proxy bias, D63 as prior mean (LOO), the final feasibility map. Writes a150_summary.json; prints
<= 15 lines."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a150_bo as M  # noqa: E402

A, B, ROOT, KVS = M.A, M.B, M.ROOT, M.KVS
_s = importlib.util.spec_from_file_location("a143_analyze", B.A143C.parent / "a143_analyze.py")
A143 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A143)
FROZEN = {"e50": B.A145C / "run_e72_l50_l_p48_1us.json", "l0": B.A143C / "run_g4_s100_l_p48_1us_k4.json",
          "l07": B.A143C / "run_g4_s070_l_p48_1us_k4.json", "l13": B.A143C / "run_g4_s130_l_p48_1us_k4.json",
          "l5": B.A143C / "run_g4_s100_l_p48_5us_k4.json", "l5_s070": B.A143C / "run_g4_s070_l_p48_5us_k4.json",
          "l5_s130": B.A143C / "run_g4_s130_l_p48_5us_k4.json", "s_p62": B.A143C / "run_g4_s100_s_p62_k4.json",
          "l_m48_1us": B.A143C / "run_g4_s100_l_m48_1us_k4.json"}


def gxy(p):
    return round(p["kr"] / KVS, 3), round(p["kt"] / KVS, 3)


def steady(path):
    r = A.load(path)
    t0 = A.t_step(r)
    s = A.stats(r)
    pk = max(e["i_a"] for e in r["highoffs_last"] if 600e-6 <= e["t_s"] < t0)
    return {"vo_mv": s["vo_mean_pre_mv"], "von1": s["von1_pre_mean"], "peak": pk}


def price(p):
    rows = p["m"]["rows"]
    out = {}
    for k in ("l0", "l07", "l13"):
        f = A.stats(A.load(FROZEN[k]))
        out[k] = {"back_us": rows[k]["back_within_1pct_us"], "vo_mv": rows[k]["extreme_mv"], "iae": rows[k]["iae"],
                  "peak": rows[k]["peak_post"], "frozen_back_us": f["back_within_1pct_us"], "frozen_vo_mv": f["extreme_mv"],
                  "frozen_peak": f["peak_post"]}
    out["l5_peak"] = rows["l5"]["peak_post"]
    out["late"] = {k: sum(v["late"]) for k, v in rows.items()}
    return out


def conf_check(conf, cand):
    """Criterion 3 on one confirmed point: its own rows (c<idx>_*) <= 200 A, e50 rows <= 40.0 V, all 0 NEW and Vo back
    finite; the frozen slew references (c00_*) are reported, not judged."""
    if not conf or (cand is not None and conf["idx"] != cand["idx"]):
        return {"pass": False, "ran": False}
    rows, ok, own = {}, True, f"c{conf['idx']:02d}_"
    for name, rel in conf["rows"].items():
        p = ROOT / rel
        if not p.exists():
            rows[name] = None
            ok &= not name.startswith(own)
            continue
        r = A.load(p)
        s = A.stats(r, name)
        v = rows[name] = {"peak": s["peak_post"], "new": s["oracle_new"], "back_us": s["back_within_1pct_us"],
                          "vo_mv": s["extreme_mv"], "vds": (s.get("vds") or {}).get("whole"), "status": s["status"],
                          "late": sum(s["late"])}
        if name.startswith(own):
            good = (v["status"] == "COMPLETED" and s["src_modified"] is False and v["new"] == 0
                    and bool(np.isfinite(v["back_us"])) and v["peak"] <= 200.0
                    and (not name.endswith("_e50") or v["vds"] <= 40.0))
            v["ok"] = bool(good)
            ok &= bool(good)
    fails = [k for k, v in rows.items() if v and v.get("ok") is False]
    return {"pass": bool(ok), "ran": True, "idx": conf["idx"], "x": [round(conf["kr"] / KVS, 3), round(conf["kt"] / KVS, 3)],
            "fails": fails, "rows": rows}


def main():
    st = M.load_state()
    M.refresh(st, json.loads((B.HERE / "a149_sh_table.json").read_text())["L50_e72"])
    pts = st["points"]
    # 1. forecast calibration
    z = [(p["idx"], c, (p["m"][c] - p["pred"][c][0]) / p["pred"][c][1]) for p in pts if "pred" in p
         for c in ("V50", "PK1", "PK5") if c in p["m"]]
    c1 = {"n": len(z), "within_2sd": sum(abs(v) <= 2 for _, _, v in z), "z": [(i, c, round(v, 2)) for i, c, v in z]}
    c1["pass"] = bool(z) and c1["within_2sd"] >= 0.7 * len(z)
    # 2. feasible point
    cand = M.candidate(st)
    c2 = {"pass": cand is not None, "feasible": [gxy(p) for p in pts if p["m"].get("feasible")]}
    # final models and map
    d63 = M.d63_prior()
    models = M.fit_models(pts, d63)
    pof = np.ones(len(M.GRID))
    for c, lim in M.LIM.items():
        mu, sd = models[c].predict(M.GRID)
        pof *= norm.cdf((lim - mu) / sd)
    ref = cand or max((p for p in pts if "V50" in p["m"] and "PK1" in p["m"] and "PK5" in p["m"]),
                      key=lambda p: min((M.LIM[c] - p["m"][c]) / {"V50": 0.5, "PK1": 3.0, "PK5": 3.0}[c] for c in M.LIM))
    x = np.array(gxy(ref))
    h = 0.05
    grad = {c: [float((models[c].predict(x + d)[0][0] - models[c].predict(x - d)[0][0]) / (2 * h))
                for d in (np.array([h, 0]), np.array([0, h]))] for c in ("V50", "PK1", "PK5")}
    # 3. confirmation (registered candidate; the post hoc largest-margin point the same way)
    c3 = conf_check(st.get("confirm"), cand)
    c3_post = conf_check(st.get("confirm_posthoc"), None)
    # 4. steady state
    c4 = {"pass": False}
    if cand is not None:
        a, f = steady(ROOT / cand["src"]["l0"]), steady(FROZEN["l0"])
        c4 = {"cand": a, "frozen": f, "pass": bool(abs(a["vo_mv"] - f["vo_mv"]) <= 0.5 and abs(a["von1"] - f["von1"]) <= 0.3
                                                    and abs(a["peak"] - f["peak"]) <= 1.0)}
    # cross-checks
    sig = []
    for p in pts:
        rel = p["src"].get("l5")
        if rel and (ROOT / rel).exists():
            s = A143.stats(ROOT / rel)
            sig.append({"x": gxy(p), "pk5": p["m"].get("PK5"), "lo234_pos": s.get("lo234_pos"), "lo234_max": s.get("lo234_max")})
    bias = [{"x": gxy(p), "bias": p["m"]["rows"]["l0"]["sh50_block"] - p["m"]["V50"]} for p in pts
            if "V50" in p["m"] and p["m"]["rows"].get("l0")]
    out = {"stop": st.get("stop"), "n_points": len(pts), "candidate": gxy(cand) if cand else None, "reference": gxy(ref),
           "criteria": {"1": c1, "2": c2, "3": c3, "4": c4}, "posthoc_confirm": c3_post, "price": price(ref),
           "final_models": {c: m.info() for c, m in models.items()}, "grad_at_reference": grad,
           "map": {"max_pof": float(pof.max()), "argmax": M.GRID[int(np.argmax(pof))].tolist(),
                   "area_pof_gt_0.5": float(np.mean(pof > 0.5))},
           "signature_5us": sig, "proxy_bias": bias,
           "points": [{"idx": p["idx"], "x": gxy(p), "batch": p["batch"],
                       **{k: p["m"].get(k) for k in ("V50", "PK1", "PK5", "OBJ", "new", "feasible")}} for p in pts]}
    (HERE / "a150_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"stop {out['stop']}; {len(pts)} points; feasible {c2['feasible']}; candidate {out['candidate']}")
    print(f"C1 {c1['within_2sd']}/{c1['n']} within 2 sd ({'PASS' if c1['pass'] else 'FAIL'}); C2 {'PASS' if c2['pass'] else 'FAIL'}; "
          f"C3 {'PASS' if c3['pass'] else ('FAIL' if c3['ran'] else 'not run')}; C4 {'PASS' if c4['pass'] else 'FAIL/none'}")
    for lab, c in (("C3", c3), ("post hoc", c3_post)):
        if c["ran"]:
            print(f"{lab} {c['x']}: {'PASS' if c['pass'] else 'FAIL'}; fails {c['fails']}")
    print(f"map: max P(feasible) {out['map']['max_pof']:.3f} at {out['map']['argmax']}, area P>0.5 {out['map']['area_pof_gt_0.5']:.3f}")
    near = lambda p: min((M.LIM[c] - p["m"].get(c, 1e9)) / {"V50": 0.5, "PK1": 3.0, "PK5": 3.0}[c] for c in M.LIM)
    for p in sorted(sorted(pts, key=near, reverse=True)[:9], key=gxy):
        m = p["m"]
        print(f"  {gxy(p)} b{p['batch']} V50 {m.get('V50', float('nan')):.2f} PK1 {m.get('PK1', float('nan')):.1f} "
              f"PK5 {m.get('PK5', float('nan')):.1f} IAE {np.exp(m.get('OBJ', np.nan)):.0f} new {m.get('new')} {'F' if m.get('feasible') else ''}")
    pr = out["price"]
    print(f"price at {out['reference']}: " + "; ".join(f"{k} back {v['back_us']:.1f} us ({v['frozen_back_us']:.1f}) "
                                                        f"Vo {v['vo_mv']:+.1f} pk {v['peak']:.1f} ({v['frozen_peak']:.1f})"
                                                        for k, v in pr.items() if k in ("l0", "l07", "l13")))


if __name__ == "__main__":
    main()
