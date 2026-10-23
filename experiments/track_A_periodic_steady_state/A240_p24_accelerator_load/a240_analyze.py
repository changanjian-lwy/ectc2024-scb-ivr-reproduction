"""A240 analysis (BOUNDARY Section 2): per row the limits, Vo's extremes and its excursions above 1.05 V after the
train starts, the peak against the board's single re-application (A237) with its phase and the events above 200 A, the
last train periods' Vo swing, rail 1, late fires (whole run and after 300 us, per re-application) and the end.
  python3 a240_analyze.py -> a240_summary.json
Vo is the record's section samples (each phase-1 turn-on, about 0.5 us at full load; skip ticks, about 0.2 us)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a240_make_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(MC)
T0, T_STOP = MC.T0 * 1e-6, MC.T_STOP * 1e-6
I_LIM, V_LIM, V_HI, V_LO, T_HI_US, BAND, Q4_TOL = 200.0, 40.0, 1.05, 0.95, 25.0, 0.01, 10.0
REF_PK = {"N0": 161.48, "N75": 171.08, "S75h": 152.64}       # A237 cw5_N0 / cw5_N75 / c30_S75h post-step peaks


def runs_above(ts, vo, m, v):
    """Longest contiguous stretch (us) of samples above v within mask m, counted to the next sample."""
    best = cur = 0.0
    idx = np.where(m)[0]
    for a, b in zip(idx, np.append(idx[1:], idx[-1])):
        if vo[a] > v:
            cur += ts[min(a + 1, len(ts) - 1)] - ts[a]
            best = max(best, cur)
        else:
            cur = 0.0
    return float(1e6 * best)


def per_reapp(r, ts, vo, per):
    """Per re-application (end of each low half, the last at T_STOP): Vo's dip in the high half after it, the late fires
    in that half, and phase 1's crossing-report error (ns; None = early) over the 5 us before it."""
    sec = r["sections"]
    late = np.array([sum(q.get("late", [0])) for q in sec])
    lr = r["lo_reports_last"]
    out = []
    for k in range(round((T_STOP - T0) / per)):
        tr = T0 + per * (k + 1)
        b = (ts >= tr) & (ts < tr + min(per / 2, 50e-6))
        e = [x["err_s"] for x in lr if tr - 5e-6 <= x["t_s"] < tr]
        es = [x for x in e if x is not None]
        out.append({"t_us": 1e6 * tr, "dip_mv": 1e3 * (float(vo[b].min()) - 1),
                    "late": int(late[b][-1] - late[ts < tr][-1]) if b.any() else 0,
                    "lo_err_ns": [1e9 * min(es), 1e9 * max(es)] if es else None, "lo_early": len(e) - len(es)})
    return out


def one(f, board, f_khz):
    r = json.loads(Path(f).read_text())
    sec = r["sections"]
    ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    rail1 = np.array([q["vin_v"] - q["vcs_v"][0] for q in sec])
    g = r["gate_offs_last"]
    m = ts >= T0
    per = 1e-3 / f_khz
    w = (ts >= max(T0, T_STOP - 3 * per)) & (ts < T_STOP)
    last = ts >= ts[-1] - 20e-6
    ga = [e for e in g if e["t_s"] >= T0]
    top = max(ga, key=lambda e: e["i_max_a"])
    pk_after = top["i_max_a"]
    late_t0 = sum(next((q for q in reversed(sec) if q["t_s"] <= T0), sec[0]).get("late", [0]))
    v = {"status": r["status"], "sources_modified": r["provenance"]["cosim_sources_modified"],
         "peak_whole": max(e["i_max_a"] for e in g), "records_from_us": 1e6 * min(e["t_s"] for e in g),
         "peak_after_t0": pk_after, "vds_v": max(r["vds_max_v"]), "overlaps": r["overlaps"],
         "shoot_on": sum(r["gate_stats"]["shoot_on"]), "late_end": sum(sec[-1].get("late", [0])),
         "late_after_t0": sum(sec[-1].get("late", [0])) - late_t0, "n_reapp": round((T_STOP - T0) / per),
         "peak_phase": top["phase"], "events_over_lim": sum(e["i_max_a"] > I_LIM for e in ga),
         "vo_max_v": float(vo[m].max()), "vo_min_v": float(vo[m].min()), "t_above_max_us": runs_above(ts, vo, m, V_HI),
         "swing_last3_mv": 1e3 * float(vo[w].max() - vo[w].min()) if w.any() else None,
         "vo_end_v": [float(vo[last].min()), float(vo[last].max())], "rail1_max_v": float(rail1[m].max()),
         "skip_ticks": r.get("skip_ticks"), "reapp": per_reapp(r, ts, vo, per)}
    c = {"q0": not v["sources_modified"],
         "q1": bool(v["status"] == "COMPLETED" and v["peak_whole"] <= I_LIM and v["vds_v"] <= V_LIM
                    and not v["overlaps"] and not v["shoot_on"]),
         "q2": bool(v["t_above_max_us"] < T_HI_US), "q3": bool(v["vo_min_v"] >= V_LO),
         "q4": bool(pk_after <= REF_PK[board] + Q4_TOL),
         "q5": all(abs(x - 1) <= BAND for x in v["vo_end_v"])}
    return v, c


def main():
    res = {"rows": {}}
    for b in MC.BOARDS:
        for fk in MC.F_KHZ:
            row = f"p_{b}_{fk:g}k"
            f = COS / f"run_{row}.json"
            if not f.exists():
                res["rows"][row] = None
                continue
            v, c = one(f, b, fk)
            res["rows"][row] = {"board": b, "f_khz": fk, "m": v, "criteria": c}
    done = [x for x in res["rows"].values() if x]
    res["criteria_main"] = {k: all(x["criteria"][k] for x in done) for k in ("q0", "q1", "q2", "q3", "q4", "q5")}
    res["complete"] = len(done) == len(res["rows"])
    (HERE / "a240_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if not x:
            print(f"{row:12s} missing"); continue
        v = x["m"]
        print(f"{row:12s} Vo {v['vo_min_v']:.4f}..{v['vo_max_v']:.4f} (>1.05 {v['t_above_max_us']:.1f} us, last swing "
              f"{v['swing_last3_mv']:.1f} mV) pk {v['peak_after_t0']:.1f} A (whole {v['peak_whole']:.1f}) V_DS {v['vds_v']:.1f} "
              f"rail1 {v['rail1_max_v']:.2f} late {v['late_end']} | " + "".join(k for k, ok in x["criteria"].items() if not ok))
    print("main", res["criteria_main"], "complete", res["complete"])


if __name__ == "__main__":
    main()
