"""A152 analysis against BOUNDARY Section 2 -> a152_summary.json; prints <= 15 lines. Per run A148's stats (oracle,
Vo) plus, over all modules: start-up peak (high-side turn-off current, t < 300 us), handover peak (140-160 us), post-step
peak, late fires, V_DS windows, and Vo at 143.5 us. Reference = the row's ideal-plant frozen-design record."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "extensions" / "ml_design_assist" / "experiments" / "A148_rl_zvs_line_step"))
import a148_analyze as A  # noqa: E402

_spec = importlib.util.spec_from_file_location("a152_make_cfgs", HERE / "make_cfgs.py")   # A148 has a make_cfgs too
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

COS = HERE / "cosim"
A150C = ROOT / "extensions" / "ml_design_assist" / "experiments" / "A150_gpbo_vo_priced_package" / "cosim"
A151C = HERE.parent / "A151_p24_slow_hard_turn_on" / "cosim"
PRICE = {50: 3.2, 100: 3.8}            # A151's L0 load-step Vo price vs the ideal plant, us (BOUNDARY criterion 4)


def ref_path(row):
    if row.startswith("slew") and row != "slew5":
        return A150C / f"run_c00_{row}.json"
    return M.A143C / f"run_{M.ROWS[row]}.json"


def run_stats(path):
    r = A.load(path)
    s = A.stats(r, Path(path).name)
    mods = [r] + r.get("modules_rest", [])
    t0 = A.t_step(r)
    hi = [e for m in mods for e in m["highoffs_last"]]
    full = max(m["highoffs_last"][0]["t_s"] for m in mods) < 1e-6           # records reach back to the start
    vo = min(r["sections"], key=lambda q: abs(q["t_s"] - 143.5e-6))["vo"]
    out = {k: s.get(k) for k in ("oracle_new", "back_within_1pct_us", "extreme_mv", "vo_mean_pre_mv")}
    out.update(ok_status=all(m["status"] == "COMPLETED" for m in mods) and s["src_modified"] is False,
               start_pk=max(e["i_a"] for e in hi if e["t_s"] < 300e-6) if full else None,
               hand_pk=max(e["i_a"] for e in hi if 140e-6 <= e["t_s"] < 160e-6) if full else None,
               peak_post=max(e["i_a"] for e in hi if e["t_s"] >= t0), late=int(sum(sum(m["late_fires"]) for m in mods)),
               vo_hand=vo, n_mod=len(mods))
    secs = [q for m in mods for q in m["sections"] if "vds_win_v" in q]
    if secs:
        w = lambda a, b: max((max(q["vds_win_v"]) for q in secs if a <= q["t_s"] < b), default=0.0)
        out["vds"] = {"start": w(0, 300e-6), "steady": w(600e-6, t0), "post": w(t0, t0 + 100e-6), "whole": w(0, 1.0)}
    return out


def judge(r, f, load_step, price):
    """Criteria 1-4 for one run r against its reference f; returns {criterion: [misses]}."""
    bad = {1: [], 2: [], 3: [], 4: []}
    if not r["ok_status"]:
        bad[3].append("status")
    if r["vds"]["whole"] > 40.0:
        bad[1].append(f"{r['vds']['whole']:.1f} V")
    if r["start_pk"] is None or r["start_pk"] > max(200.0, f["start_pk"] + 5.0):
        bad[2].append("start " + (f"{r['start_pk']:.0f}" if r["start_pk"] is not None else "n/a"))
    if r["peak_post"] > min(f["peak_post"] + 5.0, 200.0):
        bad[3].append(f"peak {r['peak_post']:.1f}")
    if r["oracle_new"]:
        bad[3].append(f"NEW {r['oracle_new']}")
    if r["late"] > f["late"] + 2:
        bad[3].append(f"late {r['late']}")
    ext, fext = abs(r["extreme_mv"]), abs(f["extreme_mv"])
    if ext > fext + 4.0:
        bad[4].append(f"ext {r['extreme_mv']:.1f}")
    if ext > 11.0 and r["back_within_1pct_us"] > f["back_within_1pct_us"] + 2.0 + (price if load_step else 0.0):
        bad[4].append(f"back {r['back_within_1pct_us']:.1f}")
    return bad


def main():
    refs = {row: run_stats(ref_path(row)) for row in M.ROWS}
    ref_m4 = run_stats(M.A143C / "run_g5_l_p48_1us_k4.json")
    runs, out, lines = {}, {"points": {}}, []
    for l in M.SPEC:
        crit = {1: [], 2: [], 3: [], 4: []}
        for row in M.ROWS:
            p = COS / f"run_s{l}_{row}.json"
            if not p.exists():
                crit[3].append(f"{row} missing")
                continue
            runs[f"s{l}_{row}"] = r = run_stats(p)
            for k, v in judge(r, refs[row], row.endswith("s_p62"), PRICE[l]).items():
                crit[k] += [f"{row} {x}" for x in v]
        m4p = COS / f"run_m4_s{l}_l_p48_1us.json"
        c5 = ["missing"]
        if m4p.exists():
            runs[f"m4_s{l}"] = m4 = run_stats(m4p)
            b = judge(m4, ref_m4, False, 0.0)
            c5 = b[1] + b[2] + b[3]
        out["points"][l] = {f"c{k}": {"pass": not v, "misses": v} for k, v in crit.items()}
        out["points"][l]["c5"] = {"pass": not c5, "misses": c5}
        rs = [runs[f"s{l}_{row}"] for row in M.ROWS if f"s{l}_{row}" in runs]
        lines.append(f"S{l}: " + " ".join(f"C{k} {'PASS' if not v else 'FAIL'}" for k, v in crit.items())
                     + f" C5 {'PASS' if not c5 else 'FAIL'} | V_DS max {max(r['vds']['whole'] for r in rs):.1f} V, "
                     f"start pk max {max(r['start_pk'] or 0 for r in rs):.0f} A, post pk max {max(r['peak_post'] for r in rs):.1f} A")
        for k, v in list(crit.items()) + [(5, c5)]:
            if v:
                lines.append(f"   C{k} misses: " + "; ".join(v[:6]) + (" ..." if len(v) > 6 else ""))
    big = {}
    for d, _ in M.BIG:
        p = COS / f"run_big300_on{d:g}.json"
        if p.exists():
            runs[f"big300_on{d:g}"] = r = run_stats(p)
            b = judge(r, refs["l_p48_1us"], False, 0.0)
            big[d] = {"vds": r["vds"], "start_pk": r["start_pk"], "peak_post": r["peak_post"], "c1_3": b[1] + b[2] + b[3]}
    out["c6"] = {"pass": any(not big[d]["c1_3"] for d in (18.0, 9.0) if d in big), "rows": big}
    lines.append(f"C6 300 pH {'PASS' if out['c6']['pass'] else 'FAIL'}: " + "; ".join(
        f"{d:g} A/ns whole {v['vds']['whole']:.1f} (steady {v['vds']['steady']:.1f}) V, start {v['start_pk']:.0f} A, "
        f"post {v['peak_post']:.0f} A" for d, v in big.items()))
    a151 = {}
    for l, d in ((50, 36), (100, 18)):
        for row in ("l_p48_1us", "s_p62"):
            o, n = run_stats(A151C / f"run_on{d}_l{l}_{row}.json"), runs.get(f"s{l}_{row}")
            if n:
                a151[f"s{l}_{row}"] = {"ton35.5": o, "new": n}
    lines.append("L0 vs A151 (ton 35.5 -> new): " + "; ".join(
        f"{k}: start {v['ton35.5']['start_pk']:.0f}->{v['new']['start_pk']:.0f} A, V {v['ton35.5']['vds']['whole']:.1f}->"
        f"{v['new']['vds']['whole']:.1f}, post {v['ton35.5']['peak_post']:.0f}->{v['new']['peak_post']:.0f}, back "
        f"{v['ton35.5']['back_within_1pct_us']:.1f}->{v['new']['back_within_1pct_us']:.1f}" for k, v in a151.items()))
    out.update(runs=runs, refs=refs, ref_m4=ref_m4, a151_l0=a151)
    (HERE / "a152_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("\n".join(lines[:15]))


if __name__ == "__main__":
    main()
