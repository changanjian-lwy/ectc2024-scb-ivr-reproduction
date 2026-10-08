"""A170 analysis: A168's statistics and criteria (a168_analyze: A164's stats, judged against the same row at 50 pH with
ideal low sides and no interlock, A167 else A164) plus the interlock's holds and the low sides' edge times; A169's run
of the same row (no interlock) alongside where it exists. Writes a170_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A9 = HERE.parent / "A169_p24_gate_low_sides" / "cosim"
_s = importlib.util.spec_from_file_location("a168_analyze", HERE.parent / "A168_p24_gate_loop_bound" / "a168_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        stem = Path(f).stem[4:]
        conf, row = stem.split("_", 1)
        rf = A8.ref_of(row)
        st, ref = A8.safe_stats(f), A8.A4.stats(str(rf))
        st["ref"] = {k: ref.get(k) for k in A8.KEYS}
        st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"{rf.parent.parent.name}/run_{row}.json"
        g = json.loads(Path(f).read_text()).get("gate_stats", {})
        st["il_holds"], st["il_hold_max_ns"] = g.get("il_holds"), (g.get("il_hold_max_s") or 0.0) * 1e9
        st["delay_off_ls_ns"] = [None if x is None else x * 1e9 for x in g.get("delay_off_ls_s", [None, None])]
        a9 = A9 / f"run_{row}.json"
        if conf == "S50" and a9.exists():
            o = A8.safe_stats(str(a9))
            st["a169"] = {k: o.get(k) for k in ("start_pk", "hand_pk", "peak_post", "late", "extreme_mv", "shoot_on",
                                                "overlaps", "edge_w")}
        runs[stem], verdict[stem] = st, {str(k): v for k, v in A8.judge(st, ref).items()}
    (HERE / "a170_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for stem, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[stem].items() if v]
        a = st.get("a169", {})
        print(A8.line(stem, st, f" holds {sum(st['il_holds'] or [])} max {st['il_hold_max_ns']:.1f} ns, A169 late "
                                f"{a.get('late')} post {a.get('peak_post')}"), 'PASS' if not miss else 'miss ' + ' '.join(miss))


if __name__ == "__main__":
    main()
