"""C14 analysis against BOUNDARY Section 2 -> c14_summary.json. Per run: A143's stats (A142 oracle classes, overlaps,
late fires, post-step peak), matrix.step_stats at 800 us; per module (p24_loss_budget.measure over the last 200
periods before the step, D66's measurement): current (mean of valley and peak, summed over phases) and the largest
phase-mean peak; per module the largest high-side turn-off current after the step. Nominal references: A143's g5
records and nom_l_m48_1us."""
from __future__ import annotations

import importlib.util
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from scb_ivr.cosim.matrix import step_stats
from scb_ivr.p24_loss_budget import measure

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent.parent / "track_A_periodic_steady_state"
spec = importlib.util.spec_from_file_location("a143_analyze", TA / "A143_p24_short_comparator_phase" / "a143_analyze.py")
A143 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A143)
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
ROWS = ("n0", "s_p62", "l_p48_1us", "l_m48_1us")
STEP_ROWS = ROWS[1:]
T_STEP = 800e-6
HEAVY = 1
D66 = {"w5": {"share": (7.1, 9.6), "steady": (154, 156), "peak": (199, 201)},
       "o10": {"share": (7.7, 10.2), "steady": (156, 157), "peak": (201, 202)},
       "w10": {"share": (14.5, 19.8), "steady": (165, 169), "peak": (210, 214)}}


def one(path):
    path = Path(path)
    d = json.loads(path.read_text())
    s = A143.stats(path)
    mods = [d] + d.get("modules_rest", [])
    stepped = bool(d["cfg"].get("line_step") or d["cfg"].get("load_step"))
    cur, pk_st, pk_post = [], [], []
    for m in mods:
        ph = measure(m, t1=T_STEP if stepped else None)["phases"]
        cur.append(sum((p["valley"] + p["peak"]) / 2.0 for p in ph))
        pk_st.append(max(p["peak"] for p in ph))
        pk_post.append(max([q["i_a"] for q in m["highoffs_last"] if q["t_s"] >= T_STEP], default=None) if stepped else None)
    x = {"file": path.name, "status": s["status"], "src_modified": s["src_modified"], "overlaps": s["overlaps"],
         "new": s["new"], "classes": s["classes"], "late": s["late"], "ipk": s["ipk"], "peak_post": s["peak_post"],
         "vo_end": s["vo_end"], "cur_a": cur, "share_pct": [100 * (c / np.mean(cur) - 1) for c in cur],
         "peak_steady_a": pk_st, "peak_post_a": pk_post}
    if stepped:
        x["step"] = step_stats(d, T_STEP)
    return x


def main():
    ref = {r: A143C / f"run_g5_{r}_k4.json" for r in ROWS if r != "l_m48_1us"}
    ref["l_m48_1us"] = COS / "run_nom_l_m48_1us.json"
    paths = {f"nom_{r}": p for r, p in ref.items()}
    paths.update({p.stem[4:]: p for p in COS.glob("run_*.json") if not p.stem.startswith("run_nom")})
    with Pool(8) as pool:
        runs = dict(zip(paths, pool.map(one, [str(p) for p in paths.values()])))
    crit = {}
    for sp, band in D66.items():
        rs = {r: runs.get(f"{sp}_{r}") for r in ROWS}
        if not all(rs.values()):
            crit[sp] = None
            continue
        integ = all(q["status"] == "COMPLETED" and q["overlaps"] == 0 and q["new"] == 0 for q in rs.values()) and \
            all(bool(np.isfinite(rs[r]["step"]["back_within_1pct_us"])) for r in STEP_ROWS)
        share = rs["n0"]["share_pct"][HEAVY]
        steady = rs["n0"]["peak_steady_a"][HEAVY]
        peak = max(rs[r]["peak_post"] for r in STEP_ROWS)
        crit[sp] = {"1_integrity": integ, "share_pct": share,
                    "2_share": bool(band["share"][0] - 1.5 <= share <= band["share"][1] + 1.5),
                    "steady_a": steady, "3_steady": bool(band["steady"][0] - 4 <= steady <= band["steady"][1] + 4),
                    "peak_a": peak, "peak_row": max(STEP_ROWS, key=lambda r: rs[r]["peak_post"]),
                    "peak_module": int(np.argmax([v or 0 for v in rs[max(STEP_ROWS, key=lambda r: rs[r]["peak_post"])]["peak_post_a"]])) + 1,
                    "4_peak": bool(band["peak"][0] - 7 <= peak <= band["peak"][1] + 7),
                    "all_rows_le_200": all((q["peak_post"] if q["peak_post"] is not None else q["ipk"]) <= 200.0 for q in rs.values())}
    ok = [sp for sp in ("w10", "o10", "w5") if crit.get(sp) and crit[sp]["all_rows_le_200"]]
    out = {"runs": runs, "criteria": crit, "5_spec_largest_spread_le_200": ok[0] if ok else None}
    (HERE / "c14_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in ROWS:
        q = runs[f"nom_{r}"]
        print(f"nom {r:10s} peak_post {q['peak_post'] or 0:6.1f} share {['%+.1f' % v for v in q['share_pct']]}")
    for sp, c in crit.items():
        if c:
            print(f"{sp}: integrity {c['1_integrity']} | share {c['share_pct']:+.1f} % {c['2_share']} | steady {c['steady_a']:.1f} A "
                  f"{c['3_steady']} | peak {c['peak_a']:.1f} A ({c['peak_row']}, module {c['peak_module']}) {c['4_peak']} | all <= 200: "
                  f"{c['all_rows_le_200']}")
            print("    post-step peaks: " + ", ".join(f"{r} {runs[f'{sp}_{r}']['peak_post']:.1f}" for r in STEP_ROWS))
    print("spec (largest spread with every row <= 200 A):", out["5_spec_largest_spread_le_200"])


if __name__ == "__main__":
    main()
