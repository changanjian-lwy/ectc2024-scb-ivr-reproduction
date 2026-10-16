"""A238 analysis (BOUNDARY Section 2): each sink-mode row against its source record (A237 / A230).
  python3 a238_analyze.py -> a238_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a238_make_cfgs", HERE / "make_cfgs.py")
A37 = _load("a237_analyze", TA / "A237_p24_true_light_load" / "a237_analyze.py")
A25 = _load("a225_analyze", TA / "A225_p24_startup_items_recheck" / "a225_analyze.py")
A28, A29, A21 = A37.A29.A28, A37.A29, A37.A29.A21
I_LIM, V_LIM, BAND, V_VRD, VALLEY_MIN, TOL_RE, TOL_HAND = 200.0, 40.0, 0.01, 1.05, -55.0, 10.0, 2.0
SKIP_Z = {"s_c10_N0": "z_N0_10", "s_c10_N75": "z_N75_10"}


def ref_path(row):
    exp, stem = MC.ROWS[row]
    return MC.SRC[exp] / f"run_{stem}.json"


def sink(f):
    """Sink episodes [(t_on_us, t_off_us or None)], and the valleys / gate-level peaks while sink was set."""
    r = json.loads(Path(f).read_text())
    log = r.get("sink_log", [])
    eps, t_on = [], None
    for t, s in log:
        if s:
            t_on = t
        elif t_on is not None:
            eps.append((t_on, t)); t_on = None
    if t_on is not None:
        eps.append((t_on, None))
    inside = lambda t: any(a <= t <= (b if b is not None else 1.0) for a, b in eps)
    va = [x["i_a"] for x in r["lowoffs_last"] if inside(x["t_s"])]
    pk = [e["i_max_a"] for e in r["gate_offs_last"] if inside(e["t_s"])]
    rec0 = min((x["t_s"] for x in r["lowoffs_last"]), default=None)
    return {"episodes_us": [[1e6 * a, None if b is None else 1e6 * b] for a, b in eps], "n_episodes": len(eps),
            "low_at_end": t_on is None, "valley_min_a": min(va, default=None), "valley_max_a": max(va, default=None),
            "peak_min_a": min(pk, default=None), "peak_max_a": max(pk, default=None),
            "records_from_us": None if rec0 is None else 1e6 * rec0,
            "ladder_end": A21.ladder_end(r)}


def main():
    res = {"rows": {}}
    for row, (exp, stem) in MC.ROWS.items():
        f, rf = COS / f"run_{row}.json", ref_path(row)
        s = sink(f)
        s_ok = bool(s["low_at_end"] and (s["valley_min_a"] is None or s["valley_min_a"] >= VALLEY_MIN))
        c = {"t7": s_ok}
        if exp == "A237":
            h, ref = A37.one(f), A37.one(rf)
            c["t2"] = h["limits"]
            i_cc = A37.MC.ROWS[stem][1]
            if i_cc == 0.0:
                c["t1"] = bool(h["t_above_vrd_us"] <= 25.0 and h["back_us"] is not None and h["back_us"] <= 25.0
                               and h["vo_end_in"])
            elif "post_pk" in h:
                c["t4"] = bool(h["post_pk"] <= I_LIM and h["post_pk"] <= ref["post_pk"] + TOL_RE and h["vo_end_in"])
            else:
                c["t3"] = h["vo_end_in"]
            if row in SKIP_Z:
                k = A29.skip_file(f, SKIP_Z[row])
                h["skip"] = {q: k[q] for q in ("vmin_a", "vmax_a", "in_band", "q1_run")}
                k = A29.skip_file(rf, SKIP_Z[row])
                ref["skip"] = {q: k[q] for q in ("vmin_a", "vmax_a", "in_band", "q1_run")}
                c["t3"] = bool(c["t3"] and h["skip"]["q1_run"] and h["skip"]["in_band"])
        else:
            h, ref = A25.startup(f), A25.startup(rf)
            lim = bool(h["status"] == "COMPLETED" and h["peak_whole"] <= I_LIM and h["vds_v"] <= V_LIM
                       and not h["overlaps"] and not h["shoot_on"])
            vo_in = bool(all(abs(v - 1) <= BAND for v in h["vo_last"]))
            c["t2"] = lim
            if stem.endswith("_0_lead"):
                c["t5"] = bool(vo_in and h["vo_max_v"] <= V_VRD
                               and s["ladder_end"][1] <= A21.ladder_end(json.loads(rf.read_text()))[1])
            else:
                same = A28.same(f, rf) if s["n_episodes"] == 0 else False
                h["same_as_ref"] = same
                c["t6"] = bool(same or (h["hand_pk"] <= ref["hand_pk"] + TOL_HAND and vo_in))
            ref["ladder_end"] = A21.ladder_end(json.loads(rf.read_text()))
        res["rows"][row] = {"sink": s, "with_sink": h, "ref": ref, "ref_record": str(rf.relative_to(TA)), "criteria": c}
    logs = PROJECT / "tmp" / "logs"
    ident = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a238_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    unit = bool(re.search(r"ALL PASSED 117 tests", (logs / "a238_unit.log").read_text()))
    res["identity"] = dict(ident, unit_117=unit)
    q = {"t0": all(res["identity"].values())}
    for k in ("t1", "t2", "t3", "t4", "t5", "t6", "t7"):
        q[k] = all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"])
    res["criteria_main"] = q
    (HERE / "a238_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    fmt = lambda x: "-" if x is None else f"{x:.1f}"
    for n, v in res["rows"].items():
        h, r, s = v["with_sink"], v["ref"], v["sink"]
        line = f"{n:12s} sink {s['n_episodes']} ep {[[fmt(a), fmt(b)] for a, b in s['episodes_us'][:2]]} valley {fmt(s['valley_min_a'])}..{fmt(s['valley_max_a'])} pk {fmt(s['peak_min_a'])}..{fmt(s['peak_max_a'])} ladder {s['ladder_end'][1]:.2f} V"
        if "vo_rel_peak_mv" in h:
            line += (f" | peak +{h['vo_rel_peak_mv']:.1f} mV back {fmt(h['back_us'])} (ref {fmt(r['back_us'])}) >1.05 {h['t_above_vrd_us']:.1f} us"
                     f" end {h['vo_end_v'][0]:.4f}..{h['vo_end_v'][1]:.4f}")
            if "post_pk" in h:
                line += f" post {h['post_pk']:.1f} (ref {r['post_pk']:.1f}) dip {h['vo_re_min_mv']:+.1f}"
            if "skip" in h:
                line += f" skip {h['skip']['vmin_a']:.1f}..{h['skip']['vmax_a']:.1f} (ref {r['skip']['vmin_a']:.1f}..{r['skip']['vmax_a']:.1f})"
        else:
            line += (f" | vo max {h['vo_max_v']:.4f} last {h['vo_last'][0]:.4f}..{h['vo_last'][1]:.4f} hand {h['hand_pk']:.1f}"
                     f" (ref {r['hand_pk']:.1f}, ladder {r['ladder_end'][1]:.2f}) whole {h['peak_whole']:.1f}")
        print(line + f" | {v['criteria']}")
    print("main", q)


if __name__ == "__main__":
    main()
