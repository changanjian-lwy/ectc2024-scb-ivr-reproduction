"""A181 analysis (BOUNDARY Section 2). Engineering criteria per run (c1 start-up / handover <= 200 A, c2 post-step
<= 200 A, c3 V_DS <= 40 V + COMPLETED + no shoot-through / overlap, c4 Vo(143.5 us) in 0.99-1.17 V); diagnostics
reported only: late fires before / after the step, NEW, Vo extreme / recovery, holds, the step's phase after phase 1's
last low-side turn-off, pre-step settling. Stage 1 (cosim_cal): the S75 start-ups. Stats are A179's (= A174 / A168
chain). Writes a181_summary.json."""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a179_analyze", TA / "A179_p24_interlock_release_threshold" / "a179_analyze.py")
A79 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A79)
WINDOW = (0.99, 1.17)


def event_phase(r, t0):
    """Step time after phase 1's last low-side turn-off, in units of the steady period (450-495 us)."""
    on = np.array([x["t_s"] for x in r["turnons_last"] if x["phase"] == 1 and 450e-6 <= x["t_s"] < 495e-6])
    per = float(np.median(np.diff(on))) if len(on) > 2 else None
    lo = [x["t_s"] for x in r["lowoffs_last"] if x["phase"] == 1 and x["t_s"] < t0]
    return {"period_ns": per and per * 1e9, "after_lo1_ns": lo and (t0 - lo[-1]) * 1e9,
            "phase": (per and lo) and (t0 - lo[-1]) / per}


def settling(r):
    def w(a, b):
        s = [q for q in r["sections"] if a <= q["t_s"] * 1e6 < b]
        return float(np.mean([q["vcs_v"][0] for q in s])), float(np.mean([q["vo"] for q in s]))
    (c1, v1), (c2, v2) = w(400, 450), w(450, 495)
    return {"vcs1_drift_mv": (c2 - c1) * 1e3, "vo_400_450": v1, "vo_450_495": v2}


def stats(path):
    st = A79.stats(path)
    r = json.loads(Path(path).read_text())
    t0 = st["t_step_us"] * 1e-6
    st.update(event=event_phase(r, t0), settle=settling(r), ton_ns=r["cfg"]["ton_ns"],
              temp=r["cfg"]["gate"].get("temp", 25.0), l_scale=r["cfg"]["circuit"]["L"] / 2.9333333199999997e-09)
    st["criteria"] = {
        "c1_startup": bool(st.get("start_pk") is not None and st["start_pk"] <= 200.0 and (st.get("hand_pk") or 0) <= 200.0),
        "c2_post": bool(st["peak_post"] <= 200.0),
        "c3_safe": bool(A79.ok({**st, "peak_post": 0.0})),
        "c4_vo": bool(WINDOW[0] <= st["vo_143_5"] <= WINDOW[1])}
    return st


def cal_rows():
    out = {}
    for f in sorted(glob.glob(str(HERE / "cosim_cal" / "run_*.json"))):
        r = json.loads(Path(f).read_text())
        go = [e for e in r.get("gate_offs_last", [])]
        vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
        out[Path(f).stem[4:]] = {"ton_ns": r["cfg"]["ton_ns"], "vo_143_5": vo, "status": r["status"],
                                 "start_pk": max((e["i_max_a"] for e in go if e["t_s"] < 140e-6), default=None),
                                 "pk_to_150us": max((e["i_max_a"] for e in go), default=None)}
    return out


KEYS = ("start_pk", "hand_pk", "peak_post", "vds_whole", "vo_143_5", "late_pre", "late_post", "oracle_new",
        "extreme_mv", "back_within_1pct_us", "il_holds", "shoot_on", "ton_ns", "temp", "l_scale", "t_step_us",
        "event", "settle", "criteria")


def main():
    runs = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        st = stats(f)
        runs[Path(f).stem[4:]] = {k: st.get(k) for k in KEYS}
    out = {"cal": cal_rows(), "runs": runs}
    (HERE / "a181_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for n, c in out["cal"].items():
        print(f"cal {n}: ton {c['ton_ns']} Vo143.5 {c['vo_143_5']:.4f} start {c['start_pk']} max to 150 us {c['pk_to_150us']}")
    for n, r in runs.items():
        e = r["event"]
        print(f"{n:11s} ton {r['ton_ns']:6.3f} {r['temp']:5.0f}C L{r['l_scale']:.2f} start {r['start_pk'] or 0:6.1f} hand "
              f"{r['hand_pk'] or 0:6.1f} post {r['peak_post']:6.1f} V {r['vds_whole']:4.1f} Vo143.5 {r['vo_143_5']:.4f} late "
              f"{r['late_pre']}+{r['late_post']} NEW {r['oracle_new']} ext {r['extreme_mv']:6.1f} phase "
              f"{(e['phase'] or 0):.2f} drift {r['settle']['vcs1_drift_mv']:+.1f} mV {r['criteria']}")


if __name__ == "__main__":
    main()
