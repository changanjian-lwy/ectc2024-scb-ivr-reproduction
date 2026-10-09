"""A189 analysis (BOUNDARY Section 2): per start-up run c1 start-up (before mode P) and handover (entry .. + 25 us)
physical peaks <= 200 A; c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps; c4 Vo at the mode-P entry >= 0.99 V
(A163's cliff); diagnostics: Vo(143.5 us), request time, handover Vo minimum, ladder max/min at entry, loop Ton
after entry. Writes a189_summary.json.
  python3 a189_analyze.py"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def run(path):
    r = json.loads(Path(path).read_text())
    tp, S, g, lsb = r["t_mode_p_s"], r["sections"], r["gate_offs_last"], r["lsb_s"]
    pre = [q for q in S if q["t_s"] <= tp][-1]
    ent = next(q for q in S if q["t_s"] > tp)
    vin, c = pre["vin_v"], pre["vcs_v"]
    rails = [vin - c[0], c[0] - c[1], c[1] - c[2], c[2]]
    post = [q for q in S if tp < q["t_s"] < tp + 50e-6]
    ov = r["overlaps"] if isinstance(r["overlaps"], int) else len(r["overlaps"] or [])
    st = {"temp": r["cfg"]["gate"].get("temp"), "vo_143_5": float(np.mean([q["vo"] for q in S if 143e-6 < q["t_s"] < 144e-6])),
          "t_hand_req_us": (r.get("t_hand_req_s") or 0) * 1e6 or None, "t_entry_us": tp * 1e6, "vo_entry": ent["vo"],
          "ladder": max(rails) / min(rails), "start_pk": max(e["i_max_a"] for e in g if e["t_s"] < tp),
          "hand_pk": max(e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6),
          "vo_min_entry": min(q["vo"] for q in post), "vo_max": max(q["vo"] for q in S),
          "ton_max_ns": max(q["ton_lsb"] for q in post) * lsb * 1e9, "vds_max_v": max(r["vds_max_v"])}
    st["criteria"] = {"c1": st["start_pk"] <= 200.0 and st["hand_pk"] <= 200.0,
                      "c3": st["vds_max_v"] <= 40.0 and r["status"] == "COMPLETED" and ov == 0
                      and sum(r["gate_stats"].get("shoot_on", [0])) == 0,
                      "c4": st["vo_entry"] >= 0.99}
    return Path(path).stem[4:], st


def main():
    res = dict(run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    (HERE / "a189_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        print(f"{k:10s} {s['temp']:5.0f} C Vo(143.5) {s['vo_143_5']:.3f} req {s['t_hand_req_us'] or 0:6.1f} entry Vo {s['vo_entry']:.3f} "
              f"ladder {s['ladder']:.3f} start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} Vo min {s['vo_min_entry']:.3f} "
              f"Ton max {s['ton_max_ns']:.1f} V {s['vds_max_v']:.1f} {s['criteria']}")


if __name__ == "__main__":
    main()
