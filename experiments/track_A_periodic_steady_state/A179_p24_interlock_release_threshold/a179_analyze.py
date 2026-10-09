"""A179 analysis (BOUNDARY Section 2). Runs t<il>_p<k>_<row>: per-run stats (A174's, = A164 / A168 chain) with late
fires split at the step; criterion 1 (sections before the step equal the old-window run: A173 at 0.5 ns, A177 at
1.4 ns), criterion 2 (old-window run inside the new positions' range + A174 tolerances), criterion 3 (worst over
positions against the 0.5 ns runs of the row). Old-window records: A173 / A177 cosim (release records-a173 / -a177).
edge_w from the chain uses 600-950 us, which here is after the step: not used. Writes a179_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a174_analyze", TA / "A174_p24_final_plant_margins" / "a174_analyze.py")
A74 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A74)
OLD = {0.5: TA / "A173_p24_final_plant_coverage" / "cosim" / "run_{row}.json",
       1.4: TA / "A177_p24_per_board_interlock_reference" / "cosim" / "run_pb_{row}.json"}
KEYS = ("peak_post", "late_pre", "late_post", "oracle_new", "extreme_mv", "vds_whole", "il_holds", "t_step_us")


def late_split(r, t0):
    pre = post = 0
    for m in [r] + r.get("modules_rest", []):
        s = [q for q in m["sections"] if "late" in q]
        a = [q for q in s if q["t_s"] < t0]
        n_pre = sum(a[-1]["late"]) if a else 0
        pre, post = pre + n_pre, post + sum(s[-1]["late"]) - n_pre
    return pre, post


def stats(path):
    st = A74.stats(path)
    r = json.loads(Path(path).read_text())
    st["late_pre"], st["late_post"] = late_split(r, st["t_step_us"] * 1e-6)
    st["vds_whole"] = st["vds"]["whole"] if "vds" in st else None
    return st


def identity(new, old):
    """Criterion 1: every section before the new run's step equals the old-window run's (vo, vcs, late; all modules)."""
    a, b = json.loads(Path(new).read_text()), json.loads(Path(old).read_text())
    t0 = (a["cfg"].get("line_step") or a["cfg"]["load_step"])["t_us"] * 1e-6
    n = 0
    for ma, mb in zip([a] + a.get("modules_rest", []), [b] + b.get("modules_rest", [])):
        sa = [q for q in ma["sections"] if q["t_s"] < t0]
        sb = [q for q in mb["sections"] if q["t_s"] < t0]
        if len(sa) != len(sb):
            return {"equal": False, "why": f"{len(sa)} vs {len(sb)} sections"}
        for qa, qb in zip(sa, sb):
            for k in ("t_s", "vo", "vcs_v", "late"):
                if qa.get(k) != qb.get(k):
                    return {"equal": False, "why": f"{k} at {qa['t_s'] * 1e6:.3f} us"}
            n += 1
    return {"equal": True, "sections": n}


def ok(st):
    return (not st.get("stopped") and st["ok_status"] and not st.get("shoot_on") and not st.get("overlaps")
            and st["vds_whole"] <= 40.0 and st["peak_post"] <= 200.0)


def inside(old, runs):
    """Criterion 2: the old-window run inside the new positions' range widened by A174's tolerances."""
    lo = lambda k: min(r[k] for r in runs)
    hi = lambda k: max(r[k] for r in runs)
    bad = []
    if not lo("peak_post") - 3 <= old["peak_post"] <= hi("peak_post") + 3:
        bad.append("post")
    if not lo("oracle_new") - 2 <= old["oracle_new"] <= hi("oracle_new") + 2:
        bad.append("NEW")
    e = [abs(r["extreme_mv"]) for r in runs]
    if not min(e) - 2 <= abs(old["extreme_mv"]) <= max(e) + 2:
        bad.append("ext")
    if not lo("late_post") / 1.5 - 5 <= old["late_post"] <= 1.5 * hi("late_post") + 5:
        bad.append("late_post")
    return bad


def judge(runs, base):
    """Criterion 3: worst over positions against the 0.5 ns runs' worst (W0)."""
    w = lambda rs, k, f=lambda x: x: max(f(r[k]) for r in rs)
    bad = [f"status/limit {r['name']}" for r in runs if not ok(r)]
    if w(runs, "peak_post") > w(base, "peak_post") + 3:
        bad.append(f"post {w(runs, 'peak_post'):.1f} vs {w(base, 'peak_post'):.1f}")
    if w(runs, "late_post") > 1.5 * w(base, "late_post") + 5:
        bad.append(f"late_post {w(runs, 'late_post')} vs {w(base, 'late_post')}")
    if w(runs, "oracle_new") > w(base, "oracle_new") + 2:
        bad.append(f"NEW {w(runs, 'oracle_new')} vs {w(base, 'oracle_new')}")
    if w(runs, "extreme_mv", abs) > w(base, "extreme_mv", abs) + 2:
        bad.append(f"ext {w(runs, 'extreme_mv', abs):.1f} vs {w(base, 'extreme_mv', abs):.1f}")
    if w(runs, "late_pre") > 1.5 * w(base, "late_pre") + 5:
        bad.append(f"late_pre {w(runs, 'late_pre')} vs {w(base, 'late_pre')}")
    return bad


def main():
    groups = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        m = re.match(r"t(\d\d)_p(\d)_(.+)", name)
        til, k, row = int(m.group(1)) / 10, int(m.group(2)), m.group(3)
        full = stats(f)
        st = {key: full.get(key) for key in KEYS} | {"name": name, "k": k}
        st.update(ok_status=full["ok_status"], stopped=full.get("stopped"), shoot_on=full.get("shoot_on"),
                  overlaps=full.get("overlaps"))
        if til in OLD:
            st["identity"] = identity(f, str(OLD[til]).format(row=row))
        groups.setdefault(row, {}).setdefault(til, []).append(st)
    out = {"runs": {r["name"]: r for by in groups.values() for runs in by.values() for r in runs},
           "old": {}, "misses": {"c2": {}, "c3": {}}}
    for row, by in groups.items():
        for til, runs in by.items():
            old = Path(str(OLD[til]).format(row=row)) if til in OLD else None
            if old and old.exists():
                o = stats(str(old))
                out["old"][f"{row} {til}"] = {k: o.get(k) for k in KEYS}
                out["misses"]["c2"][f"{row} {til}"] = inside(o, runs)
            if 0.5 in by:
                out["misses"]["c3"][f"{row} {til}"] = judge(runs, by[0.5])
    c3 = out["misses"]["c3"]
    passing = [t for t in (1.4, 1.0, 0.8) if not c3.get(f"ss_l_m80_10us {t}", ["not run"])]
    x = max(passing, default=None)
    out["criteria"] = {"1_identity": {n: r["identity"]["equal"] for n, r in out["runs"].items() if "identity" in r},
                       "2_window": {k: not v for k, v in out["misses"]["c2"].items()},
                       "3_release": {k: not v for k, v in c3.items()}}
    out["decision"] = {"x_ns": x, "r2_at_x": not c3.get(f"ss_s_p62 {x}", ["not run"]),
                       "m4_at_1.4": not c3.get("m4_ss_l_p48_1us 1.4", ["not run"])}
    (HERE / "a179_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for row, by in groups.items():
        for til in sorted(by):
            for r in sorted(by[til], key=lambda x: x["k"]):
                print(f"{r['name']:26s} step {r['t_step_us']:9.4f} post {r['peak_post']:6.1f} late {r['late_pre']:4d} + "
                      f"{r['late_post']:4d} NEW {r['oracle_new']:3d} ext {r['extreme_mv']:6.1f} V {r['vds_whole']:4.1f} "
                      f"holds {r['il_holds']} id {r.get('identity', {}).get('equal')}")
            key = f"{row} {til}"
            if key in out["old"]:
                o = out["old"][key]
                print(f"{'  old window':26s} step {o['t_step_us']:9.4f} post {o['peak_post']:6.1f} late {o['late_pre']:4d} + "
                      f"{o['late_post']:4d} NEW {o['oracle_new']:3d} ext {o['extreme_mv']:6.1f}   c2 {out['misses']['c2'][key]}")
            print(f"  c3 {key}: {c3.get(key)}")
    print("decision", out["decision"])


if __name__ == "__main__":
    main()
