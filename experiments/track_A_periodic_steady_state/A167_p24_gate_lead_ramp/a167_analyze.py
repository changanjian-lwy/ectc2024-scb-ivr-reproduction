"""A167 analysis: A164's criteria and statistics (a164_analyze.stats / judge, A152 references, matched peak definitions)
on A167's runs, side by side with A164's run of the same name (the same lead without the ramp). Writes a167_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A4D = HERE.parent / "A164_p24_gate_drive_spread"
_s = importlib.util.spec_from_file_location("a164_analyze", A4D / "a164_analyze.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        stem = Path(f).stem[4:]
        st, ref = A4.stats(f), A4.REF[A4.row_of(stem)]
        bad = A4.judge(st, ref, stem.startswith("m4"))
        st["ref"] = {k: ref[k] for k in ("peak_post", "late", "extreme_mv", "back_within_1pct_us", "start_pk")}
        a4 = A4D / "cosim" / f"run_{stem}.json"
        if a4.exists():
            o = A4.stats(str(a4))
            st["a164"] = {k: o.get(k) for k in ("start_pk", "hand_pk", "peak_post", "post_cmd_a", "late",
                                                "late_after_300us", "extreme_mv", "edge_w")}
            st["a164"]["vds_whole"] = o["vds"]["whole"]
        runs[stem], verdict[stem] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a167_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for stem, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[stem].items() if v]
        a = st.get("a164", {})
        print(f"{stem:22s} V {st['vds']['whole']:4.1f} start {st['start_pk'] or 0:5.1f} hand {st.get('hand_pk') or 0:5.1f} "
              f"(A164 {a.get('hand_pk') or 0:5.1f}) post {st['peak_post']:5.1f}/{st['post_cmd_a']:5.1f} late {st['late']:3d} "
              f"({st['late_after_300us']}) ext {st['extreme_mv']:6.1f} P {st['edge_w'] or 0:4.1f} W "
              f"{'PASS' if not miss else 'miss ' + ' '.join(miss)}"[:170])


if __name__ == "__main__":
    main()
