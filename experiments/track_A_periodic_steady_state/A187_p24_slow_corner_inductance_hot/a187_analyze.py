"""A187 analysis (BOUNDARY Section 2): per run c1 start-up / handover (entry .. + 25 us) <= 200 A, c2 post-step <= 200 A,
c3 V_DS <= 40 V + COMPLETED + 0 shoot-throughs / overlaps, c7 Vo <= 1.05 V over 0-300 us; diagnostics: the step's
phase after phase 1's last low-side turn-off (a181_analyze.event_phase), the post-step peak's phase and time, late
fires on phases 3-4 in step .. step + 30 us, the Vo minimum after the step. Writes a187_summary.json.
  python3 a187_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a181", HERE.parent / "A181_p24_locked_trim_joint_corner" / "a181_analyze.py")
A181 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A181)


def late_at(r, t):
    s = [q for q in r["sections"] if q["t_s"] <= t]
    return s[-1]["late"] if s else [0, 0, 0, 0]


def run(path):
    r = json.loads(Path(path).read_text())
    t = r["cfg"]["line_step"]["t_us"] * 1e-6
    tp, g = r["t_mode_p_s"], r["gate_offs_last"]
    post = max((e for e in g if e["t_s"] >= t), key=lambda e: e["i_max_a"])
    ov = r["overlaps"] if isinstance(r["overlaps"], int) else len(r["overlaps"] or [])
    l0, l1 = late_at(r, t), late_at(r, t + 30e-6)
    st = {"step_us": t * 1e6, "step_phase": A181.event_phase(r, t)["phase"],
          "start_pk": max(e["i_max_a"] for e in g if e["t_s"] < tp),
          "hand_pk": max(e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6),
          "post_pk": post["i_max_a"], "post_phase": post["phase"], "post_after_us": (post["t_s"] - t) * 1e6,
          "late_ph34_30us": (l1[2] - l0[2]) + (l1[3] - l0[3]),
          "vo_min_post": min(q["vo"] for q in r["sections"] if t <= q["t_s"] < t + 60e-6),
          "vds_max_v": max(r["vds_max_v"]), "vo_max_300us": max(q["vo"] for q in r["sections"] if q["t_s"] < 300e-6)}
    st["criteria"] = {"c1": st["start_pk"] <= 200.0 and st["hand_pk"] <= 200.0, "c2": st["post_pk"] <= 200.0,
                      "c3": st["vds_max_v"] <= 40.0 and r["status"] == "COMPLETED" and ov == 0
                      and sum(r["gate_stats"].get("shoot_on", [0])) == 0,
                      "c7": st["vo_max_300us"] <= 1.05}
    return Path(path).stem[4:], st


def main():
    res = dict(run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    (HERE / "a187_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        print(f"{k:11s} phase {s['step_phase']:.2f} post {s['post_pk']:5.1f} A ph{s['post_phase']} +{s['post_after_us']:4.1f} us "
              f"late3-4 {s['late_ph34_30us']:3d} Vo min {s['vo_min_post']:.3f} | start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} "
              f"V {s['vds_max_v']:.1f} {s['criteria']}")


if __name__ == "__main__":
    main()
