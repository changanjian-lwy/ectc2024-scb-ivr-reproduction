"""A173 analysis (BOUNDARY Section 2): A168's statistics and criteria (a168_analyze) against the same row at 50 pH
with ideal low sides and no interlock (A167, else A164); rows without such a reference (L x 0.7 s_p62, four modules)
against absolute limits and their ideal-switch record's late fires. Adds interlock holds, the t_il 0.5 ns run of the
comparator rows (A171 / A172), and the steady edge power over 600 us .. step - 10 us (a163's 600-950 us window
contains the four-module step at 800 us). Writes a173_summary.json; prints one line per run."""
from __future__ import annotations

import glob
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a168_analyze", TA / "A168_p24_gate_loop_bound" / "a168_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)
T05 = {"ss_l_p48_1us": TA / "A171_p24_gate_interlock_threshold" / "cosim" / "run_S50_ss_l_p48_1us.json",
       "nom_L07_l_p48_1us": TA / "A172_p24_final_gate_plant" / "cosim" / "run_nom_L07_l_p48_1us.json"}
# rows without a 50 pH gate-level reference: (start / handover reference, late of the ideal-switch record or None)
ABS = {"nom_L07_s_p62": (202.546, 2),       # A167 L x 0.7 start-up; A143 g4_s070_s_p62_k4
       "m4_nom_s_p62": (0.0, 0),            # A143 g5_s_p62_k4
       "m4_w5_l_p48_1us": (0.0, 9),         # C14 w5_l_p48_1us
       "m4_ss_l_p48_1us": (0.0, None)}      # slow corner: late reported only


def steady_edge(path):
    """Mean steady channel edge + reverse-conduction power per module (W), 600 us .. step - 10 us."""
    r = json.loads(Path(path).read_text())
    t1 = (r["cfg"].get("line_step") or r["cfg"]["load_step"])["t_us"] * 1e-6 - 10e-6
    out = []
    for m in [r] + r.get("modules_rest", []):
        s = [q for q in m["sections"] if 600e-6 <= q["t_s"] <= t1 and q.get("edge_energy_j")]
        dt = s[-1]["t_s"] - s[0]["t_s"]
        out.append(float(np.sum([np.add(q["edge_energy_j"], q["rev_energy_j"]) for q in s[1:]]) / dt))
    return float(np.mean(out)), [round(x, 3) for x in out]


def main():
    runs, verdict = {}, {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        name = Path(f).stem[4:]
        base = name.split("_", 1)[1] if name.startswith("il") else name
        st = A8.safe_stats(f)
        r = json.loads(Path(f).read_text())
        g = r.get("gate_stats", {})
        st["il_holds"], st["il_hold_max_ns"] = g.get("il_holds"), (g.get("il_hold_max_s") or 0.0) * 1e9
        st["t_il_ns"] = r["cfg"]["gate"].get("t_il_ns")
        if not st.get("stopped"):
            st["edge_steady_w"], st["edge_steady_mod_w"] = steady_edge(f)
        if base in ABS:
            s0, late0 = ABS[base]
            ref = {"start_pk": s0, "hand_pk": s0, "peak_post": 195.0, "oracle_new": 0,
                   "late": math.inf if late0 is None else late0, "extreme_mv": math.inf, "back_within_1pct_us": math.inf}
            st["ref"] = {"start_pk": s0, "late_ideal": late0, "file": "absolute (BOUNDARY Section 2)",
                         "vds_whole": 0.0, "hand_pk": s0, "peak_post": 200.0, "late": late0 or 0,
                         "extreme_mv": 0.0, "edge_w": 0.0}
            bad = A8.judge(st, ref)
            bad[4] = [] if base.startswith("m4") or st.get("stopped") else (
                [] if st.get("back_within_1pct_us") is not None and math.isfinite(st["back_within_1pct_us"]) else
                ["Vo not back within 1 %"])
        else:
            rf = A8.ref_of(base)
            ref = A8.A4.stats(str(rf))
            st["ref"] = {k: ref.get(k) for k in A8.KEYS}
            st["ref"]["vds_whole"], st["ref"]["file"] = ref["vds"]["whole"], f"{rf.parent.parent.name}/run_{base}.json"
            bad = A8.judge(st, ref)
        if name.startswith("il") and base in T05:
            o = A8.safe_stats(str(T05[base]))
            st["t_il_0p5"] = {k: o.get(k) for k in ("start_pk", "hand_pk", "peak_post", "late", "oracle_new", "extreme_mv")}
        runs[name], verdict[name] = st, {str(k): v for k, v in bad.items()}
    (HERE / "a173_summary.json").write_text(json.dumps({"runs": runs, "verdict": verdict}, indent=1, default=float))
    for name, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[name].items() if v]
        extra = f" holds {sum(st['il_holds'] or [])} max {st['il_hold_max_ns']:.1f} ns E {st.get('edge_steady_w', 0):.2f} W"
        print(A8.line(name, st, extra), "PASS" if not miss else "miss " + " ".join(miss))


if __name__ == "__main__":
    main()
