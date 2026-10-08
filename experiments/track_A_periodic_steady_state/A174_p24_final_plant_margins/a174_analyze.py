"""A174 analysis (BOUNDARY Section 2). Step-position rows (sh<k>_<row>): A168's criteria against the row's reference
(A167 / A164), plus the decision quantities over the five positions (the original run: A172 / A173). Fixed-reference
rows (fr_<row>): criterion 4 against A173's t_il 0.5 run of the same row. Writes a174_summary.json."""
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
ORIG = {"nom_L07_l_p48_1us": TA / "A172_p24_final_gate_plant" / "cosim" / "run_nom_L07_l_p48_1us.json",
        "ff_l_m80_10us": TA / "A173_p24_final_plant_coverage" / "cosim" / "run_ff_l_m80_10us.json"}
A173C = TA / "A173_p24_final_plant_coverage" / "cosim"


def stats(path):
    st = A8.safe_stats(str(path))
    r = json.loads(Path(path).read_text())
    g = r.get("gate_stats", {})
    st["il_holds"], st["il_hold_max_ns"] = g.get("il_holds"), (g.get("il_hold_max_s") or 0.0) * 1e9
    st["t_step_us"] = (r["cfg"].get("line_step") or r["cfg"]["load_step"])["t_us"]
    return st


def judge_fr(st, b):
    """Criterion 4 (BOUNDARY): the change the fixed-reference delay causes against A173's t_il 0.5 run."""
    bad = []
    if st.get("stopped") or not st["ok_status"]:
        return ["status"]
    if st["vds"]["whole"] > 40.0:
        bad.append(f"{st['vds']['whole']:.1f} V")
    if abs(st["peak_post"] - b["peak_post"]) > 3.0:
        bad.append(f"post {st['peak_post']:.1f} vs {b['peak_post']:.1f}")
    if st["late"] > 1.5 * b["late"] + 5:
        bad.append(f"late {st['late']} vs {b['late']}")
    if st["oracle_new"] > b["oracle_new"] + 2:
        bad.append(f"NEW {st['oracle_new']} vs {b['oracle_new']}")
    if abs(abs(st["extreme_mv"]) - abs(b["extreme_mv"])) > 2.0:
        bad.append(f"ext {st['extreme_mv']:.1f} vs {b['extreme_mv']:.1f}")
    if st.get("shoot_on") or st.get("overlaps"):
        bad.append("shoot / overlap")
    return bad


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        kind, row = name.split("_", 1)
        st = stats(f)
        if kind == "fr":
            b = A8.safe_stats(str(A173C / f"run_{row}.json"))
            st["a173"] = {k: b.get(k) for k in ("peak_post", "late", "oracle_new", "extreme_mv", "start_pk", "hand_pk")}
            runs[name], verdict[name] = st, {"4": judge_fr(st, b)}
        else:
            ref = A8.A4.stats(str(A8.ref_of(row)))
            st["ref"] = {k: ref.get(k) for k in A8.KEYS}
            st["ref"]["vds_whole"] = ref["vds"]["whole"]
            runs[name], verdict[name] = st, {str(k): v for k, v in A8.judge(st, ref).items()}
    dec = {}
    for row, f0 in ORIG.items():
        pos = [(0, stats(f0))] + [(int(n[2]), runs[n]) for n in sorted(runs) if n.startswith("sh") and n[4:] == row]
        dec[row] = {"positions": len(pos),
                    "post": {k: s.get("peak_post") for k, s in pos}, "new": {k: s.get("oracle_new") for k, s in pos},
                    "ext": {k: s.get("extreme_mv") for k, s in pos}, "late": {k: s.get("late") for k, s in pos}}
    out = {"runs": runs, "verdict": verdict, "decision": dec}
    out["decision_2_L07_all_le_200"] = all(v <= 200.0 for v in dec["nom_L07_l_p48_1us"]["post"].values() if v is not None)
    out["decision_3_ff_new_at_new_positions"] = sum(1 for k, v in dec["ff_l_m80_10us"]["new"].items() if k and v)
    (HERE / "a174_summary.json").write_text(json.dumps(out, indent=1, default=float))
    for name, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[name].items() if v]
        if st.get("stopped"):
            print(f"{name}: {st['stopped']}")
            continue
        print(f"{name:26s} t {st['t_step_us']:.4f} V {st['vds']['whole']:4.1f} post {st['peak_post']:5.1f} late {st['late']:3d} "
              f"NEW {st['oracle_new']} ext {st['extreme_mv']:6.1f} back {st['back_within_1pct_us']:4.1f} holds "
              f"{sum(st['il_holds'] or [])} max {st['il_hold_max_ns']:.1f}", "PASS" if not miss else "miss " + " ".join(miss))
    for row, d in dec.items():
        print(row, "post", {k: round(v, 1) for k, v in d["post"].items()}, "NEW", d["new"])
    print("L07 all <= 200:", out["decision_2_L07_all_le_200"], "| ff NEW at new positions:",
          out["decision_3_ff_new_at_new_positions"])


if __name__ == "__main__":
    main()
