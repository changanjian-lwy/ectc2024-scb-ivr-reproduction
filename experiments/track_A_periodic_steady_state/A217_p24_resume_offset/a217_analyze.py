"""A217 analysis (BOUNDARY Section 2): A216's per-row function (a216_analyze.one) on A217's rows, next to A216's
records of the same rows, and the valleys of the rounds after each resume (edge log of the last 13 us).
  python3 a217_analyze.py -> a217_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
_s = importlib.util.spec_from_file_location("a216_analyze", TA / "A216_p24_skipped_rounds" / "a216_analyze.py")
A16 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A16)
COS = HERE / "cosim"
N = 4


def bursts(path):
    """Per phase, the low-side turn-off currents of the rounds after each resume in the edge log (resume = phase 1's
    low side turning on after its own turn-off, with no high-side turn-on between)."""
    r = json.loads(Path(path).read_text()); E = r.get("edges_log") or []
    marks, last1, seq = [], None, defaultdict(list)
    for e in E:
        k = e["j"] % N
        if e["j"] == N and e["level"] and last1 == ("L", 0):
            marks.append(e["t_s"])
        if e["j"] in (0, N):
            last1 = ("H" if e["j"] == 0 else "L", e["level"])
        if e["j"] >= N and not e["level"]:
            seq[k + 1].append((e["t_s"], round(e["i"][k], 2)))
    out = []
    for b, t0 in enumerate(marks):
        t1 = marks[b + 1] if b + 1 < len(marks) else 1.0
        out.append({str(k): [v for t, v in seq[k] if t0 <= t < t1][:6] for k in range(1, N + 1)})
    return out


def identity():
    logs = PROJECT / "tmp" / "logs"
    n = re.search(r"ALL PASSED (\d+) tests", (logs / "a217_unit.log").read_text())
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a217_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    return {"j1": bool(n and all(reg.values())), "unit_tests": int(n.group(1)) if n else None, "regression": reg}


def main():
    res = {"runs": {}, "a216": {}, "bursts": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        res["runs"][name] = A16.one(f)
        res["bursts"][name] = bursts(f)[:3]
        ref = TA / "A216_p24_skipped_rounds" / "cosim" / f.name
        if ref.exists():
            res["a216"][name] = A16.one(ref)
    res["criteria_identity"] = identity()
    (HERE / "a217_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for n, v in res["runs"].items():
        va = {k: [round(x, 1) for x in w] for k, w in v["valley_end_a"].items()}
        w = res["a216"].get(n, {})
        wa = {k: [round(x, 1) for x in y] for k, y in (w.get("valley_end_a") or {}).items()}
        print(f"{n:16s} {v['status'][:4]} pk {v['peak_whole']:.1f} | Vo end {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} | valleys {va} (A216 {wa}) "
              f"| loss {v['loss_w']} (A216 {w.get('loss_w')}) | {v['criteria']}")
        for b in res["bursts"][n][:1]:
            print("    first burst:", b)
    print(res["criteria_identity"])


if __name__ == "__main__":
    main()
