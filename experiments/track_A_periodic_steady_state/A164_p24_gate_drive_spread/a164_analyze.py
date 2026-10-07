"""A164 analysis: each run against A152's 50 pH run of the same row (ramp edges), with matched definitions (A163
RESULTS): command-time post-step peaks against A152's command-time peaks, physical peaks (gate_offs_last) against the
200 A budget. Criteria (BOUNDARY.md):
1 whole-run V_DS <= 40 V; 2 physical start-up peak (t < 300 us) <= 200 A and Vo(143.5 us) within 1.035 +- 0.02 V;
3 physical post-step peak <= 200 A, command-time post-step peak <= min(ref + 5, 200) A, 0 NEW oracle events, late fires
<= ref + 2, 0 overlaps, COMPLETED; 4 Vo |extreme| <= |ref| + 4 mV, back within 1 % <= ref + 2 us when |extreme| > 11 mV.
Four modules: 1-3. Adds the steady edge power (600-950 us), the gate delays, late fires after 300 us (late_log) and
the loss budget's ideal-edge terms (single module). Writes a164_summary.json; prints one line per run."""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a163_analyze", TA / "A163_p24_gate_driven_edges" / "a163_analyze.py")
A3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A3)
B, REF = A3.B, A3.REF
VO_TGT, VO_TOL = 1.035, 0.02


def row_of(stem):
    if stem.startswith("m4"):
        return "m4_s50"
    return "s50_" + stem.split("_", 1)[1].replace("lead0_", "")


def stats(path):
    st = A3.gate_stats(path)                          # physical start / handover / post-step peaks, edge power, delays
    r = B.A.load(path)
    mods = [r] + r.get("modules_rest", [])
    t0 = B.A.t_step(r)
    st["post_cmd_a"] = max(h["i_a"] for m in mods for h in m["highoffs_last"] if h["t_s"] >= t0)
    st["vo_143_5"] = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
    st["overlaps"] = int(np.sum(r["overlaps"])) if isinstance(r["overlaps"], list) else int(r["overlaps"])
    st["overlaps_cmd"] = r.get("overlaps_cmd")
    late300 = 0
    for m in mods:
        s = [q for q in m["sections"] if "late" in q]
        a = [q for q in s if q["t_s"] <= 300e-6]
        if s:
            late300 += int(sum(s[-1]["late"]) - (sum(a[-1]["late"]) if a else 0))
    st["late_after_300us"] = late300
    g = r.get("gate_stats", {})
    st["shoot_on"] = int(sum(g.get("shoot_on", [0])))
    return st


def judge(st, ref, m4):
    bad = {1: [], 2: [], 3: [], 4: []}
    if not st["ok_status"]:
        bad[3].append("status")
    if st["vds"]["whole"] > 40.0:
        bad[1].append(f"{st['vds']['whole']:.1f} V")
    if st["start_pk"] is None or st["start_pk"] > 200.0:
        bad[2].append(f"start {st['start_pk']}")
    if abs(st["vo_143_5"] - VO_TGT) > VO_TOL:
        bad[2].append(f"Vo {st['vo_143_5']:.3f}")
    if st["peak_post"] > 200.0:
        bad[3].append(f"phys {st['peak_post']:.1f}")
    if st["post_cmd_a"] > min(ref["peak_post"] + 5.0, 200.0):
        bad[3].append(f"cmd {st['post_cmd_a']:.1f}")
    if st["oracle_new"]:
        bad[3].append(f"NEW {st['oracle_new']}")
    if st["late"] > ref["late"] + 2:
        bad[3].append(f"late {st['late']}")
    if st["overlaps"]:
        bad[3].append(f"overlaps {st['overlaps']}")
    if not m4:
        ext, fext = abs(st["extreme_mv"]), abs(ref["extreme_mv"])
        if ext > fext + 4.0:
            bad[4].append(f"ext {st['extreme_mv']:.1f}")
        if ext > 11.0 and st["back_within_1pct_us"] > ref["back_within_1pct_us"] + 2.0:
            bad[4].append(f"back {st['back_within_1pct_us']:.1f}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default=str(HERE / "cosim" / "run_*.json"))
    a = ap.parse_args()
    runs, verdict = {}, {}
    for f in sorted(glob.glob(a.files)):
        stem = Path(f).stem[4:]
        st, ref = stats(f), REF[row_of(stem)]
        bad = judge(st, ref, stem.startswith("m4"))
        st["ref"] = {k: ref[k] for k in ("peak_post", "late", "extreme_mv", "back_within_1pct_us", "start_pk")}
        runs[stem], verdict[stem] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a164_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for stem, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[stem].items() if v]
        print(f"{stem:24s} V {st['vds']['whole']:4.1f} Vo {st['vo_143_5']:.3f} start {st['start_pk'] or 0:5.1f} post "
              f"{st['peak_post']:5.1f}/{st['post_cmd_a']:5.1f} late {st['late']:3d} ({st['late_after_300us']}) ext "
              f"{st['extreme_mv']:6.1f} back {st['back_within_1pct_us']:4.1f} P {st['edge_w'] or 0:4.1f} W "
              f"{'PASS' if not miss else 'miss ' + ' '.join(miss)}"[:170])


if __name__ == "__main__":
    main()
