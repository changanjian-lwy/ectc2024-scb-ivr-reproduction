"""A169 analysis: A168's statistics and criteria (a168_analyze: A164's stats, judged against the same row with ideal
low sides, A167 else A164) plus the low sides' gate edge times. Writes a169_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a168_analyze", HERE.parent / "A168_p24_gate_loop_bound" / "a168_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)
LS = ("delay_off_ls_s", "active_off_ls_s", "delay_on_ls_s", "active_on_ls_s")


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        row = Path(f).stem[4:]
        rf = A8.ref_of(row)
        st, ref = A8.safe_stats(f), A8.A4.stats(str(rf))
        st["ref"] = {k: ref.get(k) for k in A8.KEYS}
        st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"{rf.parent.parent.name}/run_{row}.json"
        g = json.loads(Path(f).read_text()).get("gate_stats", {})
        st["ls_ns"] = {k: [None if x is None else x * 1e9 for x in g.get(k, [None, None])] for k in LS}
        st["shoot_on_by_switch"] = g.get("shoot_on")
        runs[row], verdict[row] = st, {str(k): v for k, v in A8.judge(st, ref).items()}
    (HERE / "a169_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for row, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[row].items() if v]
        d = [None if x is None else round(x, 2) for x in st["ls_ns"]["delay_off_ls_s"]]
        print(A8.line(row, st, f" LS off {d} ns shoot {st['shoot_on']}"), 'PASS' if not miss else 'miss ' + ' '.join(miss))


if __name__ == "__main__":
    main()
