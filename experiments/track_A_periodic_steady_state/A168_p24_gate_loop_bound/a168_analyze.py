"""A168 analysis: A164's statistics (a164_analyze.stats: physical start / handover / post-step peaks, V_DS windows,
late fires, edge power) on each run and on its 50 pH reference (the same row in A167, else A164), judged by A168's
criteria (BOUNDARY Section 2). Writes a168_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a164_analyze", TA / "A164_p24_gate_drive_spread" / "a164_analyze.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)
REF_DIRS = (TA / "A167_p24_gate_lead_ramp" / "cosim", TA / "A164_p24_gate_drive_spread" / "cosim")
KEYS = ("oracle_new", "start_pk", "hand_pk", "peak_post", "post_cmd_a", "late", "late_after_300us", "extreme_mv",
        "back_within_1pct_us", "edge_w", "vo_143_5")


def ref_of(row):
    for d in REF_DIRS:
        f = d / f"run_{row}.json"
        if f.exists():
            return f
    raise FileNotFoundError(row)


def safe_stats(path):
    """A164's stats; a run that stopped early (stop_on_overlap) gets its stop, whole-run peak and counts only."""
    r = json.loads(Path(path).read_text())
    if r.get("status") == "COMPLETED":
        return A4.stats(str(path))
    return {"stopped": r.get("status"), "t_stop_us": r["sections"][-1]["t_s"] * 1e6, "ipk_a": r.get("ipk_a"),
            "first_overlap": r.get("first_overlap"), "shoot_on": int(sum(r.get("gate_stats", {}).get("shoot_on", [0]))),
            "late": int(sum(r.get("late_fires", [0]))), "dt_pred_final_ns": r.get("dt_pred_final_ns")}


def line(stem, st, extra=""):
    if st.get("stopped"):
        return (f"{stem:26s} {st['stopped']} at {st['t_stop_us']:.1f} us, whole-run peak {st['ipk_a']:.1f} A, "
                f"shoot {st['shoot_on']}, late {st['late']}, dt_pred {[round(x, 1) for x in st['dt_pred_final_ns']]}")
    r = st["ref"]
    return (f"{stem:26s} V {st['vds']['whole']:4.1f} ({r['vds_whole']:4.1f}) start {st['start_pk'] or 0:5.1f} "
            f"hand {st.get('hand_pk') or 0:5.1f} ({r['hand_pk'] or 0:5.1f}) post {st['peak_post']:5.1f} ({r['peak_post']:5.1f}) "
            f"late {st['late']:3d} ({r['late']}) ext {st['extreme_mv']:6.1f} ({r['extreme_mv']:6.1f}) "
            f"P {st['edge_w'] or 0:4.2f} ({r['edge_w'] or 0:4.2f}) W Vo {st['vo_143_5']:.3f}{extra}")


def judge(st, ref):
    bad = {1: [], 2: [], 3: [], 4: []}
    if st.get("stopped"):
        bad[3].append(f"{st['stopped']} at {st['t_stop_us']:.1f} us")
        return bad
    if st["vds"]["whole"] > 40.0:
        bad[1].append(f"{st['vds']['whole']:.1f} V")
    if abs(st["vo_143_5"] - A4.VO_TGT) > A4.VO_TOL:
        bad[2].append(f"Vo {st['vo_143_5']:.3f}")
    for k in ("start_pk", "hand_pk"):
        r, x = ref.get(k) or 0.0, st.get(k)
        lim = r + 3.0 if r > 197.0 else 200.0
        if x is None or x > lim:
            bad[2].append(f"{k} {x}")
    if st["peak_post"] > min(200.0, ref["peak_post"] + 5.0):
        bad[3].append(f"post {st['peak_post']:.1f}")
    for k in ("overlaps", "shoot_on"):
        if st.get(k):
            bad[3].append(f"{k} {st[k]}")
    rn = ref.get("oracle_new") or 0
    if st["oracle_new"] > (1.5 * rn + 5 if rn else 0):
        bad[3].append(f"NEW {st['oracle_new']}")
    if not st["ok_status"]:
        bad[3].append("status")
    if st["late"] > 1.5 * ref["late"] + 5:
        bad[3].append(f"late {st['late']}")
    ext, fext = abs(st["extreme_mv"]), abs(ref["extreme_mv"])
    if ext > fext + 2.0:
        bad[4].append(f"ext {st['extreme_mv']:.1f}")
    if ext > 11.0 and st["back_within_1pct_us"] > ref["back_within_1pct_us"] + 2.0:
        bad[4].append(f"back {st['back_within_1pct_us']:.1f}")
    return bad


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        stem = Path(f).stem[4:]
        conf, row = stem.split("_", 1)
        rf = ref_of(row)
        st, ref = safe_stats(f), A4.stats(str(rf))
        st["ref"] = {k: ref.get(k) for k in KEYS}
        st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"{rf.parent.parent.name}/run_{row}.json"
        bad = judge(st, ref)
        runs[stem], verdict[stem] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a168_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for stem, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[stem].items() if v]
        print(line(stem, st), 'PASS' if not miss else 'miss ' + ' '.join(miss))


if __name__ == "__main__":
    main()
