"""A163 analysis: each run against A152's 50 pH run of the same row (a152_summary.json, ramp edges), with A152's
criteria (a152_analyze.judge). Peaks are the physical high-side turn-off currents (record "gate_offs_last": the
phase current's maximum in each turn-off edge), not the command-time currents, because the gate delays the
turn-off by up to a few ns. Adds per run: the steady edge power (sections 600-950 us, all switches, W per module),
the gate statistics (turn-on / turn-off delays, forced ends), the median turn-on V_DS at the channel's start, and
the loss budget's ideal-edge switching terms on the same run (p24_loss_budget "middle": hard turn-on at the energy
balance's minimum + turn-off overlap at t_f 0.75 ns, 200 periods before 950 us): delta_w = edge_w - those terms is
what the efficiency headline (D72) leaves out.
Writes a163_summary.json; prints <= 15 lines. --files GLOB analyses other runs."""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_spec = importlib.util.spec_from_file_location("a152_analyze", TA / "A152_p24_drive_spec_robustness" / "a152_analyze.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
REF = json.loads((TA / "A152_p24_drive_spec_robustness" / "a152_summary.json").read_text())["runs"]
RAMP_W = json.loads((HERE / "a152_ramp_edge_power.json").read_text())["rows"]     # A152 s50 rows' steady edge power
_sl = importlib.util.spec_from_file_location("p24_loss_budget_script", TA.parents[1] / "scripts" / "p24_loss_budget.py")
LB = importlib.util.module_from_spec(_sl)
_sl.loader.exec_module(LB)


def row_of(name):
    stem = name.replace("run_", "").replace(".json", "")
    if stem.startswith("m4"):
        return "m4_s50"
    return "s50_" + stem.split("_", 1)[1]


def gate_stats(path):
    out = B.run_stats(path)
    r = B.A.load(path)
    mods = [r] + r.get("modules_rest", [])
    t0 = B.A.t_step(r)
    go = [e for m in mods for e in m.get("gate_offs_last", [])]
    full = min(e["t_s"] for e in go) < 1e-6 if go else False
    if go:
        out.update(start_pk=max(e["i_max_a"] for e in go if e["t_s"] < 300e-6) if full else None,
                   hand_pk=max(e["i_max_a"] for e in go if 140e-6 <= e["t_s"] < 160e-6) if full else None,
                   peak_post=max(e["i_max_a"] for e in go if e["t_s"] >= t0))
    pw = []
    for m in mods:
        s = [q for q in m["sections"] if 600e-6 <= q["t_s"] <= 950e-6 and q.get("edge_energy_j")]
        if len(s) > 2:
            pw.append(float(np.sum([q["edge_energy_j"] for q in s[1:]]) / (s[-1]["t_s"] - s[0]["t_s"])))
    g = r.get("gate_stats", {})
    tn = [t for m in mods for t in m.get("turnons_last", []) if 600e-6 <= t["t_s"] <= 950e-6 and "vds_act_v" in t]
    if len(mods) == 1:                                  # the budget's ideal-edge switching terms, same window
        from scb_ivr.p24_loss_budget import budget, measure
        mm = measure(r, t1=950e-6)
        b = budget(mm["phases"], mm["ton_s"], mm["period_s"], 2.9333333e-9, LB.SCENARIOS["middle"], mm["rails_v"],
                   mm["dv_next_v"], p_rev=mm["p_rev_w"], p_out=mm["p_out_w"])
        out.update(budget_on_w=b["hard_turn_on"], budget_off_w=b["turn_off_overlap"],
                   delta_w=(float(np.mean(pw)) - b["hard_turn_on"] - b["turn_off_overlap"]) if pw else None)
    out.update(edge_w=float(np.mean(pw)) if pw else None,
               delay_on_ns=[None if x is None else x * 1e9 for x in g.get("delay_on_s", [None, None])],
               delay_off_ns=[None if x is None else x * 1e9 for x in g.get("delay_off_s", [None, None])],
               forced=g.get("forced"), vds_act_med=float(np.median([t["vds_act_v"] for t in tn])) if tn else None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default=str(COS / "run_*.json"))
    a = ap.parse_args()
    runs, verdict = {}, {}
    for f in sorted(glob.glob(a.files)):
        name = Path(f).name
        stem = name.replace("run_", "").replace(".json", "")
        st = gate_stats(f)
        ref = REF[row_of(name)]
        row = row_of(name)
        load = "s_p62" in row
        bad = B.judge(st, ref, load, 0.0)
        if stem.startswith("m4"):
            bad = {k: v for k, v in bad.items() if k in (1, 2, 3)}
        rr = RAMP_W.get(row, {})                         # matched definitions: physical vs physical, command vs command
        rmods = B.A.load(f)
        st["ipk_run_a"] = max(m["ipk_a"] for m in [rmods] + rmods.get("modules_rest", []))
        st["ref_ipk_run_a"] = rr.get("ipk_run_a")
        st["post_cmd_a"] = max(h["i_a"] for m in [rmods] + rmods.get("modules_rest", []) for h in m["highoffs_last"]
                               if h["t_s"] >= B.A.t_step(rmods))
        st["ref_post_cmd_a"] = rr.get("post_cmd_a")
        rw = rr.get("edge_w")
        st["ramp_edge_w"] = rw
        st["gate_minus_ramp_w"] = (st["edge_w"] - rw) if (rw is not None and st.get("edge_w") is not None) else None
        runs[stem], verdict[stem] = st, {str(k): v for k, v in bad.items()}
    out = {"runs": runs, "verdict": verdict}
    (HERE / "a163_summary.json").write_text(json.dumps(out, indent=1, default=float))
    for stem, st in runs.items():
        miss = [f"{k}:{','.join(v)}" for k, v in verdict[stem].items() if v]
        print(f"{stem:24s} V {st['vds']['whole']:5.1f} start {st['start_pk'] or 0:5.1f} post {st['peak_post']:5.1f} "
              f"late {st['late']:3d} ext {st['extreme_mv']:6.1f} back {st['back_within_1pct_us']:5.1f} "
              f"P {st['edge_w'] or 0:4.1f} W {'PASS' if not miss else 'miss ' + ' '.join(miss)}"[:150])


if __name__ == "__main__":
    main()
