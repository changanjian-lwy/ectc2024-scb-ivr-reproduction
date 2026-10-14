"""A221 analysis (BOUNDARY Section 2).
- k rows (plant V7, no skipping): A215's per-row function (A212's c6 + c7 / A206's c6) next to A215's V6 records
  (k1: those criteria, the post-step peak within 3 A, Vo before 300 us within 2 mV);
- skipping rows: A216's s1, s2, s4; s3t = the true valleys (low-side turn-offs that the phase's own turn-on follows
  within 100 ns) over the last 20 us (60 us if none) inside the board's band; z1r = every phase's current at its
  resume low-side turn-on (edge log) <= 1.5 A; A220's z1 (the ring at the pauses' ticks) as information; the ladder
  at the end; the slots of the first rounds after each resume in the edge log.
- core loss, both kinds: sum over the edge log of (rail_k - Vo)^2 over high-side intervals and Vo^2 over low-side
  intervals, divided by r_core and the log's span (dead times and idle intervals left out); a record without an edge
  log (k rows): the high-side duty of the last 20 us from the turn-on / turn-off records (added after the runs).
  python3 a221_analyze.py -> a221_summary.json"""
from __future__ import annotations

import bisect
import importlib.util
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A15 = _load("a215_analyze", "A215_p24_buildable_ton_path/a215_analyze.py")
A20 = _load("a220_analyze", "A220_p24_zero_current_pause/a220_analyze.py")
A16, A17 = A20.A16, A20.A17
COS = HERE / "cosim"
N, TOL_A, TOL_V = 4, 3.0, 2e-3
MAIN = ("z_N0_25_10", "z_N75_25_10", "z_N0_25_0")


def true_valleys(r, win):
    te = r["sections"][-1]["t_s"]
    on = {}
    for h in r["turnons_last"]:
        on.setdefault(h["phase"], []).append(h["t_s"])
    for k in on:
        on[k].sort()
    out = {}
    for e in r["lowoffs_last"]:
        if e["t_s"] < te - win:
            continue
        ts = on.get(e["phase"], [])
        i = bisect.bisect_right(ts, e["t_s"])
        if i < len(ts) and ts[i] - e["t_s"] < 100e-9:
            out.setdefault(str(e["phase"]), []).append(e["i_a"])
    return {k: [min(v), max(v)] for k, v in sorted(out.items())}


def core_loss(r):
    """Watts in the core resistors over the edge log's span (high-side intervals at rail - Vo, low-side at Vo)."""
    rc = r["cfg"]["circuit"].get("r_core", 0.0)
    E = r.get("edges_log") or []
    if not rc:
        return None
    if len(E) < 2:                                       # no edge log: high-side duty from the turn-on / turn-off records
        return core_loss_duty(r, rc)
    t0, t1 = E[0]["t_s"], E[-1]["t_s"]
    sec = [q for q in r["sections"] if t0 <= q["t_s"] <= t1] or r["sections"][-1:]
    vin = np.mean([q["vin_v"] for q in sec]); vc = np.mean([q["vcs_v"] for q in sec], axis=0); vo = np.mean([q["vo"] for q in sec])
    rails = [vin - vc[0], vc[0] - vc[1], vc[1] - vc[2], vc[2]]
    e, last = 0.0, {}
    for x in E:
        j = x["j"]
        if x["level"]:
            last[j] = x["t_s"]
        elif j in last:
            dt = x["t_s"] - last.pop(j)
            e += dt * ((rails[j] - vo) ** 2 if j < N else vo ** 2)
    return e / rc / (t1 - t0)


def resume_i0(r):
    """Per resume in the edge log: each phase's current at its first low-side turn-on from phase 1's on (within 1 us)."""
    E = r.get("edges_log") or []
    last, out = None, []
    for i, e in enumerate(E):
        if e["j"] == N and e["level"] and last == ("L", 0):
            t0, got = e["t_s"], {}
            for x in E[i:]:
                if x["t_s"] - t0 > 1e-6:
                    break
                k = x["j"] - N
                if k >= 0 and x["level"] and k not in got:
                    got[k] = x["i"][k]
            if len(got) == N:
                out.append([got[k] for k in range(N)])
        if e["j"] in (0, N):
            last = ("H" if e["j"] == 0 else "L", e["level"])
    return out


def core_loss_duty(r, rc, win=20e-6):
    """Without an edge log: each phase's high-side duty over the record's last 20 us (turn-ons paired with the next
    turn-off of that phase), the low side taken as the rest of the time (dead times left out)."""
    te = r["sections"][-1]["t_s"]
    sec = [q for q in r["sections"] if q["t_s"] >= te - win]
    vin = np.mean([q["vin_v"] for q in sec]); vc = np.mean([q["vcs_v"] for q in sec], axis=0); vo = np.mean([q["vo"] for q in sec])
    rails = [vin - vc[0], vc[0] - vc[1], vc[1] - vc[2], vc[2]]
    offs = {}
    for g in r["gate_offs_last"]:
        offs.setdefault(g["phase"], []).append(g["t_s"])
    p = 0.0
    for k in range(1, N + 1):
        ts = sorted(offs.get(k, []))
        on = sum((ts[i] - h["t_s"]) for h in r["turnons_last"] if h["phase"] == k and h["t_s"] >= te - win
                 for i in [bisect.bisect_right(ts, h["t_s"])] if i < len(ts) and ts[i] - h["t_s"] < 200e-9)
        d = on / win
        p += ((rails[k - 1] - vo) ** 2 * d + vo ** 2 * (1 - d)) / rc
    return p


def ladder_end(r, win=20e-6):
    sec = r["sections"]; te = sec[-1]["t_s"]
    s = [q for q in sec if q["t_s"] >= te - win]
    vin = np.array([q["vin_v"] for q in s]); vc = np.array([q["vcs_v"] for q in s])
    rails = np.column_stack([vin - vc[:, 0], vc[:, 0] - vc[:, 1], vc[:, 1] - vc[:, 2], vc[:, 2]])
    return [float(x) for x in rails.mean(0)], float(np.abs(rails - vin[:, None] / N).max())


def slots(r, nb=3):
    E = r.get("edges_log") or []
    last, starts = None, []
    for i, e in enumerate(E):
        if e["j"] == N and e["level"] and last == ("L", 0):
            starts.append(i)
        if e["j"] in (0, N):
            last = ("H" if e["j"] == 0 else "L", e["level"])
    out = []
    for i0 in starts[:nb]:
        t0 = E[i0]["t_s"]; rows = [e for e in E[i0:] if e["t_s"] - t0 < 1.4e-6]
        p1 = [e["t_s"] for e in rows if e["j"] == N and not e["level"]]
        s = {}
        for k in (1, 2, 3):
            lo = [e["t_s"] for e in rows if e["j"] == N + k and not e["level"]]
            s[str(k + 1)] = [round((a - max(t for t in p1 if t <= a + 1e-12)) * 1e9, 1) for a in lo[:4] if any(t <= a + 1e-12 for t in p1)]
        out.append({"t_us": round(t0 * 1e6, 3), "period_ns": [round((b - a) * 1e9, 1) for a, b in zip(p1, p1[1:])][:4], "slots_ns": s})
    return out


def skip_row(f):
    v = A16.one(f)
    x = A20.extra(f, v["band_a"])
    r = json.loads(Path(f).read_text())
    tv, win = true_valleys(r, 20e-6), 20e-6
    if not tv:
        tv, win = true_valleys(r, 60e-6), 60e-6
    va = [y for p in tv.values() for y in p]
    lo, hi = v["band_a"]
    rails, dev = ladder_end(r)
    crit = {k: v["criteria"][k] for k in ("s1", "s2", "s4") if k in v["criteria"]}
    crit["s3t"] = bool(va) and min(va) >= lo and max(va) <= hi and not any(v["late_end"])
    i0 = resume_i0(r)
    crit["z1r"] = bool(i0) and max(abs(y) for q in i0 for y in q) <= A20.RING_MAX_A
    out = {k: v.get(k) for k in ("status", "sources_modified", "peak_whole", "vds_whole", "vo_end_min_v", "vo_end_max_v",
                                  "late_end", "loss_w", "books_w", "p_out_w", "rounds_end", "ticks_end", "band_a")}
    out.update(resume_i0_a=i0, resume_i0_max_a=max((abs(y) for q in i0 for y in q), default=None), z1_ring=x["crit"]["z1"],
               true_valleys_a=tv, true_valleys_window_us=win * 1e6, ring_a=x["ring_a"], entry_offs_a=x["entry_offs_a"][:2],
               rails_end_v=rails, ladder_dev_end_v=dev, slots=slots(r), core_w=core_loss(r), r_core=r["cfg"]["circuit"].get("r_core"),
               bursts=A17.bursts(f)[:2], criteria=crit)
    return out


def check_row(f, name):
    src = name[2:]
    m = A15.one(f, src)
    ref = A15.one(TA / "A215_p24_buildable_ton_path" / "cosim" / f"run_m16_{src}.json", src)
    r = json.loads(Path(f).read_text())
    k1 = bool(all(m["criteria"].values()) and abs(m["post_pk"] - ref["post_pk"]) <= TOL_A
              and abs(m["vo_max_to_300us"] - ref["vo_max_to_300us"]) <= TOL_V)
    return {"v7": m, "v6": ref, "d_post_pk_a": m["post_pk"] - ref["post_pk"], "d_hand_pk_a": m["hand_pk"] - ref["hand_pk"],
            "d_vo_300us_mv": 1e3 * (m["vo_max_to_300us"] - ref["vo_max_to_300us"]), "core_w": core_loss(r),
            "r_core": r["cfg"]["circuit"].get("r_core"), "criteria": {"k1": k1}}


def identity():
    logs = PROJECT / "tmp" / "logs"
    n = re.search(r"ALL PASSED (\d+) tests", (logs / "a221_unit.log").read_text())
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a221_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    py = re.search(r"(\d+) passed", (logs / "a221_pytest.log").read_text())
    return {"j1": bool(n and all(reg.values()) and py), "unit_tests": int(n.group(1)) if n else None, "regression": reg,
            "core_loss_tests": int(py.group(1)) if py else None}


def main():
    res = {"skip": {}, "check": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        if name.startswith("k_"):
            res["check"][name] = check_row(f, name)
        else:
            res["skip"][name] = skip_row(f)
    res["criteria_identity"] = identity()
    res["criteria_main"] = {n: res["skip"][n]["criteria"] for n in MAIN if n in res["skip"]}
    (HERE / "a221_summary.json").write_text(json.dumps(A16.clean(res), indent=1) + "\n")
    for n, v in res["check"].items():
        print(f"{n:24s} post {v['v7']['post_pk']:.2f} (V6 {v['v6']['post_pk']:.2f}) hand {v['v7']['hand_pk']:.1f} "
              f"(V6 {v['v6']['hand_pk']:.1f}) Vo<=300us {v['d_vo_300us_mv']:+.2f} mV | core {v['core_w']} W | {v['v7']['criteria']} {v['criteria']}")
    for n, v in res["skip"].items():
        print(f"{n:24s} Vo {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} | valleys {v['true_valleys_a']} ({v['true_valleys_window_us']:.0f} us) | "
              f"ring {v['ring_a']} | ladder {v['ladder_dev_end_v']:.2f} V | loss {v['loss_w']} + core {v['core_w']} | {v['criteria']}")
    print(res["criteria_identity"])


if __name__ == "__main__":
    main()
