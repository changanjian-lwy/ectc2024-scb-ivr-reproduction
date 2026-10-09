"""A178 analysis (BOUNDARY Section 2): per run A164's statistics (a168_analyze.safe_stats) against absolute limits;
per board the maximum post-step peak over the five step phases; A174's L x 0.7 phases alongside. Writes
a178_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a174_analyze", TA / "A174_p24_final_plant_margins" / "a174_analyze.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)
A8 = A4.A8


def judge(st):
    bad = {1: [], 2: [], 3: [], 4: []}
    if st.get("stopped"):
        return {1: [], 2: [], 3: [f"{st['stopped']}"], 4: []}
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
    if st["late"] > 8:
        bad[3].append(f"late {st['late']}")
    back = st.get("back_within_1pct_us")
    if back is None or not math.isfinite(back):
        bad[4].append("Vo not back within 1 %")
    return bad


def main():
    runs, verdict, boards = {}, {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        st = A4.stats(f)
        runs[name], verdict[name] = st, {str(k): v for k, v in judge(st).items()}
        b = boards.setdefault(name.split("_")[0], {"post": {}, "pass": True})
        b["post"][name.split("_")[1]] = st.get("peak_post")
        b["pass"] &= not any(verdict[name].values())
    for b in boards.values():
        b["max_post"] = max(v for v in b["post"].values() if v is not None)
    l07 = json.loads((TA / "A174_p24_final_plant_margins" / "a174_summary.json").read_text())["decision"]
    boards["L070 (A172 / A174)"] = {"post": l07["nom_L07_l_p48_1us"]["post"],
                                    "max_post": max(l07["nom_L07_l_p48_1us"]["post"].values())}
    (HERE / "a178_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict, "boards": boards}, indent=1,
                                                       default=float))
    for name, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[name].items() if v]
        print(f"{name:22s} t {st['t_step_us']:.4f} V {st['vds']['whole']:4.1f} start {st['start_pk']:5.1f} hand "
              f"{st['hand_pk']:5.1f} post {st['peak_post']:5.1f} late {st['late']} NEW {st['oracle_new']} ext "
              f"{st['extreme_mv']:5.1f} Vo {st['vo_143_5']:.3f} holds {sum(st['il_holds'] or [])}",
              "PASS" if not miss else "miss " + " ".join(miss))
    for k, b in boards.items():
        print(k, "max post", round(b["max_post"], 1), {p: round(v, 1) for p, v in b["post"].items()})


if __name__ == "__main__":
    main()
