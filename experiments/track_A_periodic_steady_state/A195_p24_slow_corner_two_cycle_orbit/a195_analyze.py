"""A195 analysis. alt(path, a, b): per phase, the mean cycle-to-cycle change of the low-side turn-off current (valley),
of the physical peak, of the high-side gate delay and of the turn-on V_DS in the window [a, b) s, plus the share of
phase 1's timed-edge reports that are early, mean Vo, late fires in the window and the status.
  python3 a195_analyze.py records   the alternation in existing V2 / V5 records (the window is the 40 us before each
                                    record's event) -> a195_records.json
  python3 a195_analyze.py           the A195 runs, window 290-330 us, against the reference record -> a195_summary.json
whole(path): outside the criteria, the run up to 330 us: largest physical peak at the handover (144-200 us) and after
it (200-330 us), the valley's range in the window, Vo's extremes over 150-330 us and the late fires up to 330 us."""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
WIN = (290e-6, 330e-6)
REF = {"S0": TA / "A192_p24_slow_lead_rows" / "cosim" / "run_S0_25_p48_1us_p0.json",
       "S75": TA / "A192_p24_slow_lead_rows" / "cosim" / "run_S75_25_p48_1us_p0.json"}
RECORDS = ["A164_p24_gate_drive_spread/cosim/run_nom_l_p48_1us.json", "A164_p24_gate_drive_spread/cosim/run_ss_l_p48_1us.json",
           "A171_p24_gate_interlock_threshold/cosim/run_S50_ss_l_p48_1us.json",
           *[f"A186_p24_vo_triggered_handover/cosim/run_{b}_p0.json" for b in
             ("F0_25", "F0_hot", "N07_25", "N0_25", "N0_hot", "N13_25", "N75_25", "S0_25", "S0_hot", "S75_25", "S75_hot")],
           "A191_p24_slow_corner_lead/cosim/run_S75_hot_p0.json", "A191_p24_slow_corner_lead/cosim/run_S80_hot_p0.json",
           "A192_p24_slow_lead_rows/cosim/run_S0_25_p48_1us_p0.json", "A192_p24_slow_lead_rows/cosim/run_S0_hot_p48_1us_p0.json",
           "A192_p24_slow_lead_rows/cosim/run_S75_25_p48_1us_p0.json", "A193_p24_slow_lead_cold/cosim/run_S75_c0_l9p5_p0.json",
           "A193_p24_slow_lead_cold/cosim/run_S75_m40_l8_p0.json", "A193_p24_slow_lead_cold/cosim/run_S75_m40_l9p5_p0.json"]


def alt(path, a, b):
    r = json.loads(Path(path).read_text())
    d = lambda x: float(np.mean(np.abs(np.diff(x)))) if len(x) > 2 else None
    m = lambda x: float(np.mean(x)) if len(x) else None
    out = {"valley_mean": [], "valley_alt": [], "peak_mean": [], "peak_alt": [], "peak_max": [], "delay_ns": [], "von_alt": []}
    for ph in (1, 2, 3, 4):
        lo = [e["i_a"] for e in r["lowoffs_last"] if e["phase"] == ph and a <= e["t_s"] < b]
        pk = [e["i_max_a"] for e in r.get("gate_offs_last", []) if e["phase"] == ph and a <= e["t_s"] < b]
        on = [e for e in r["turnons_last"] if e["phase"] == ph and a <= e["t_s"] < b and e.get("t_act_s")]
        out["valley_mean"].append(m(lo)); out["valley_alt"].append(d(lo))
        out["peak_mean"].append(m(pk)); out["peak_alt"].append(d(pk)); out["peak_max"].append(max(pk) if pk else None)
        out["delay_ns"].append(m([1e9 * (e["t_act_s"] - e["t_s"]) for e in on])); out["von_alt"].append(d([e["vds_act_v"] for e in on]))
    lr = [e for e in r.get("lo_reports_last", []) if a <= e["t_s"] < b]
    sec = [q for q in r["sections"] if a <= q["t_s"] < b]
    late = lambda t: sum(([q for q in r["sections"] if q["t_s"] < t and "late" in q] or [{"late": [0]}])[-1]["late"])
    out.update(early_share=m([e["early"] for e in lr]), vo_mv=1e3 * (m([q["vo"] for q in sec]) - 1.0), late_in_window=late(b) - late(a),
               status=r["status"], shoot_on=(r.get("gate_stats") or {}).get("shoot_on"),
               lead_ns=r["cfg"]["driver"].get("hs_on_lead_ns", 0.0), temp=r["cfg"]["gate"].get("temp", 25.0),
               dt_pred_final_ns=r.get("dt_pred_final_ns"))
    return out


def whole(path, end=330e-6):
    r = json.loads(Path(path).read_text())
    pk = lambda a, b: max(e["i_max_a"] for e in r["gate_offs_last"] if a <= e["t_s"] < b)
    lo = lambda ph: [e["i_a"] for e in r["lowoffs_last"] if e["phase"] == ph and WIN[0] <= e["t_s"] < WIN[1]]
    vo = [q["vo"] for q in r["sections"] if 150e-6 <= q["t_s"] < end]
    late = [q for q in r["sections"] if q["t_s"] < end and "late" in q]
    return {"hand_pk": pk(144e-6, 200e-6), "after_pk": pk(200e-6, end), "valley_range": [max(lo(ph)) - min(lo(ph)) for ph in (1, 2, 3, 4)],
            "vo_min_mv": 1e3 * (min(vo) - 1.0), "vo_max_mv": 1e3 * (max(vo) - 1.0), "late_to_330": sum(late[-1]["late"]) if late else 0}


def line(name, s):
    f = lambda v: " ".join("  -  " if x is None else f"{x:5.2f}" for x in v)
    return (f"{name:44s} {s['temp']:6.1f} C lead {s['lead_ns']:4.1f} delay {s['delay_ns'][0]:5.2f} ns | valley alt {f(s['valley_alt'])} A | "
            f"peak alt {f(s['peak_alt'])} | early {s['early_share']:.2f} Vo {s['vo_mv']:+.2f} mV late {s['late_in_window']}")


def records():
    res = {}
    for rel in RECORDS:
        p = TA / rel
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        ev = r["cfg"].get("line_step") or r["cfg"].get("load_step")
        b = ev["t_us"] * 1e-6 - 1e-6
        res[rel.replace("/cosim/run_", ":")[:-5]] = alt(p, b - 40e-6, b)
    (HERE / "a195_records.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        print(line(k, s))


def main():
    res = {"reference": {b: {"290-330us": {**alt(p, *WIN), "whole": whole(p)}, "459-499us": alt(p, 459e-6, 499e-6)}
                         for b, p in REF.items() if p.exists()}}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        res[Path(f).stem[4:]] = {**alt(f, *WIN), "whole": whole(f)}
    for b, s in res["reference"].items():
        for w, x in s.items():
            print(line(f"reference {b} {w}", x))
    for k, s in res.items():
        if k != "reference":
            ref = res["reference"][k.split("_")[0]]["290-330us"]
            c1 = max(s["valley_alt"]) <= 1.0
            c2 = (s["status"] == "COMPLETED" and not any(s["shoot_on"]) and abs(s["vo_mv"] - ref["vo_mv"]) <= 1.0
                  and all(abs(v + 15.625) <= 1.5 for v in s["valley_mean"]) and s["late_in_window"] <= ref["late_in_window"])
            s["criteria"] = {"c1": c1, "c2": c2}
            w, wr = s["whole"], ref["whole"]
            print(line(k, s), "| c1", c1, "c2", c2)
            print(f"    hand {w['hand_pk']:.1f} ({wr['hand_pk']:.1f}) after {w['after_pk']:.1f} ({wr['after_pk']:.1f}) A | Vo {w['vo_min_mv']:+.1f} / {w['vo_max_mv']:+.1f} "
                  f"({wr['vo_min_mv']:+.1f} / {wr['vo_max_mv']:+.1f}) mV | late to 330 us {w['late_to_330']} ({wr['late_to_330']}) | steady peak max "
                  f"{max(s['peak_max']):.1f} ({max(ref['peak_max']):.1f}) | valley range {max(w['valley_range']):.1f} ({max(wr['valley_range']):.1f}) A")
    (HERE / "a195_summary.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    records() if sys.argv[1:] == ["records"] else main()
