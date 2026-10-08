"""A175 analysis (BOUNDARY Section 2): A164's statistics (via a168_analyze) on each run, judged against A163's s50 run
of the same row with A175's limits (absolute 200 A; Vo |A163| + 5 mV). Writes a175_summary.json; one line per run."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a173_analyze", TA / "A173_p24_final_plant_coverage" / "a173_analyze.py")
A3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A3)
A8 = A3.A8
REF = TA / "A163_p24_gate_driven_edges" / "cosim"


def judge(st, ref):
    bad = {1: [], 2: [], 3: [], 4: []}
    if st.get("stopped"):
        bad[3].append(f"{st['stopped']} at {st['t_stop_us']:.1f} us")
        return bad
    if st["vds"]["whole"] > 40.0:
        bad[1].append(f"{st['vds']['whole']:.1f} V")
    if abs(st["vo_143_5"] - A8.A4.VO_TGT) > A8.A4.VO_TOL:
        bad[2].append(f"Vo {st['vo_143_5']:.3f}")
    for k in ("start_pk", "hand_pk"):
        if st.get(k) is None or st[k] > 200.0:
            bad[2].append(f"{k} {st.get(k)}")
    if st["peak_post"] > 200.0:
        bad[3].append(f"post {st['peak_post']:.1f}")
    for k in ("overlaps", "shoot_on"):
        if st.get(k):
            bad[3].append(f"{k} {st[k]}")
    if st["oracle_new"]:
        bad[3].append(f"NEW {st['oracle_new']}")
    if not st["ok_status"]:
        bad[3].append("status")
    if st["late"] > 1.5 * ref["late"] + 5:
        bad[3].append(f"late {st['late']}")
    ext = abs(st["extreme_mv"])
    if ext > abs(ref["extreme_mv"]) + 5.0:
        bad[4].append(f"ext {st['extreme_mv']:.1f}")
    if ext > 11.0 and st["back_within_1pct_us"] > ref["back_within_1pct_us"] + 5.0:
        bad[4].append(f"back {st['back_within_1pct_us']:.1f}")
    return bad


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        st = A8.safe_stats(f)
        g = json.loads(Path(f).read_text()).get("gate_stats", {})
        st["il_holds"], st["il_hold_max_ns"] = g.get("il_holds"), (g.get("il_hold_max_s") or 0.0) * 1e9
        if not st.get("stopped"):
            st["edge_steady_w"], st["edge_steady_mod_w"] = A3.steady_edge(f)
        rf = REF / f"run_s50_{name[4:]}.json"
        ref = A8.A4.stats(str(rf))
        st["ref"] = {k: ref.get(k) for k in A8.KEYS}
        st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"A163_p24_gate_driven_edges/{rf.name}"
        bad = judge(st, ref)
        runs[name], verdict[name] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a175_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for name, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[name].items() if v]
        extra = f" holds {sum(st['il_holds'] or [])} E {st.get('edge_steady_w', 0):.2f} W"
        print(A8.line(name, st, extra), "PASS" if not miss else "miss " + " ".join(miss))


if __name__ == "__main__":
    main()
