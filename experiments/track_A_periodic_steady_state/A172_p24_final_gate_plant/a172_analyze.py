"""A172 analysis: A168's statistics and criteria (a168_analyze) against the same row at 50 pH with ideal low sides and
no interlock (A167, else A164: the four-module row), criterion 4 skipped on four modules as in A164; interlock holds
and A171's run of the row alongside. Writes a172_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A1 = HERE.parent / "A171_p24_gate_interlock_threshold" / "cosim"
_s = importlib.util.spec_from_file_location("a168_analyze", HERE.parent / "A168_p24_gate_loop_bound" / "a168_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        row = Path(f).stem[4:]
        rf = A8.ref_of(row)
        st, ref = A8.safe_stats(f), A8.A4.stats(str(rf))
        st["ref"] = {k: ref.get(k) for k in A8.KEYS}
        st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"{rf.parent.parent.name}/run_{row}.json"
        g = json.loads(Path(f).read_text()).get("gate_stats", {})
        st["il_holds"], st["il_hold_max_ns"] = g.get("il_holds"), (g.get("il_hold_max_s") or 0.0) * 1e9
        a1 = A1 / f"run_S50_{row}.json"
        if a1.exists():
            o = A8.safe_stats(str(a1))
            st["a171"] = {k: o.get(k) for k in ("vo_143_5", "start_pk", "hand_pk", "peak_post", "late", "extreme_mv")}
        bad = A8.judge(st, ref)
        if row.startswith("m4"):                       # A164: Vo criterion not applied to four modules
            bad[4] = []
        runs[row], verdict[row] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a172_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for row, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[row].items() if v]
        print(A8.line(row, st, f" holds {sum(st['il_holds'] or [])} max {st['il_hold_max_ns']:.1f} ns"),
              'PASS' if not miss else 'miss ' + ' '.join(miss))


if __name__ == "__main__":
    main()
