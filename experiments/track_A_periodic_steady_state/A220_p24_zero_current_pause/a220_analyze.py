"""A220 analysis (BOUNDARY Section 2): A216's per-row function (a216_analyze.one: s1-s4) on A220's rows next to A217's
records of the same rows, and from the records: s3w (the board's band over the last 60 us), z1 (the idle phases'
largest current at a paused module's ticks, the first tick of each pause left out, last 60 us), the currents at
which each phase's low side turned off before the pauses of the edge log (zero-current turn-offs), and the first
rounds after each resume (a217_analyze.bursts).
  python3 a220_analyze.py -> a220_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A16 = _load("a216_analyze", "A216_p24_skipped_rounds/a216_analyze.py")
A17 = _load("a217_analyze", "A217_p24_resume_offset/a217_analyze.py")
COS = HERE / "cosim"
N, T_W = 4, 60e-6
RING_MAX_A = 1.5


def extra(path, band):
    """s3w, z1 and the pause-entry turn-off currents of one record."""
    r = json.loads(Path(path).read_text())
    sec = r["sections"]
    te = sec[-1]["t_s"]
    lo = [e for e in r["lowoffs_last"] if e["t_s"] >= te - T_W]
    va = [e["i_a"] for e in lo]
    ring, prev = [], False
    for q in sec:
        tk = bool(q.get("tick"))
        if tk and prev and q["t_s"] >= te - T_W:
            ring.append(max(abs(x) for x in q["i"][:N]))
        prev = tk
    E = r.get("edges_log") or []
    entry, last_off, last1 = [], {}, None
    for e in E:                                          # a pause starts where phase 1's low side turns off and its
        k = e["j"] % N                                   # next event is a low-side turn-on (no turn-on between)
        if e["j"] >= N and not e["level"]:
            last_off[k] = round(e["i"][k], 2)
        if e["j"] == N and e["level"] and last1 == ("L", 0):
            entry.append(dict(last_off))
        if e["j"] in (0, N):
            last1 = ("H" if e["j"] == 0 else "L", e["level"])
    lo_a, hi_a = band
    return {"s3w_valleys_a": [min(va), max(va)] if va else None, "s3w_n": len(va),
            "ring_a": max(ring) if ring else None, "ring_ticks": len(ring), "entry_offs_a": entry[:4],
            "zcd_fires": r.get("zcd_fires"),
            "crit": {"s3w": bool(va) and min(va) >= lo_a and max(va) <= hi_a, "z1": bool(ring) and max(ring) <= RING_MAX_A}}


def identity():
    logs = PROJECT / "tmp" / "logs"
    n = re.search(r"ALL PASSED (\d+) tests", (logs / "a220_unit.log").read_text())
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a220_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    return {"j1": bool(n and all(reg.values())), "unit_tests": int(n.group(1)) if n else None, "regression": reg}


def main():
    res = {"runs": {}, "a217": {}, "bursts": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        v = A16.one(f)
        x = extra(f, v["band_a"])
        v["criteria"] = dict(v["criteria"], **x.pop("crit"))
        v["s3_measured"] = bool(v["valley_end_a"])
        v.update(x)
        res["runs"][name] = v
        res["bursts"][name] = A17.bursts(f)[:4]
        ref = TA / "A217_p24_resume_offset" / "cosim" / f.name
        if ref.exists():
            w = A16.one(ref)
            w.update({k: y for k, y in extra(ref, w["band_a"]).items() if k != "crit"})
            res["a217"][name] = w
    res["criteria_identity"] = identity()
    (HERE / "a220_summary.json").write_text(json.dumps(A16.clean(res), indent=1) + "\n")
    for n, v in res["runs"].items():
        w = res["a217"].get(n, {})
        print(f"{n:15s} {v['status'][:4]} pk {v['peak_whole']:.1f} | Vo end {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} | "
              f"s3w {v['s3w_valleys_a']} (A217 {w.get('s3w_valleys_a')}) | ring {v['ring_a']} (A217 {w.get('ring_a')}) | "
              f"loss {v['loss_w']} (A217 {w.get('loss_w')}) | {v['criteria']}")
        for b in res["bursts"][n][:1]:
            print("    first burst:", b)
    print(res["criteria_identity"])


if __name__ == "__main__":
    main()
