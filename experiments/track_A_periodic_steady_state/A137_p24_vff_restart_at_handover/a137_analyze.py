"""A137 analysis against BOUNDARY Section 2 -> a137_summary.json: A136's statistics (a135_analyze.stats) on arm s and
on A136's matching q runs - late fires, start-up peak, post-step peak, lock."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("a135_analyze", HERE.parent / "A135_p24_relative_cap" / "a135_analyze.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
COS, Q = HERE / "cosim", HERE.parent / "A136_p24_relative_cap_lowpass" / "cosim"
IDENT = PROJECT / "tmp" / "identity_a137"
ROWS = ("m3n", "m1n", "n0", "l_p48_1us", "l_p48_5us", "s_p62")
STEPPED = ("l_p48_1us", "l_p48_5us", "s_p62")


def main():
    same = lambda a, b: all(a[k] == b[k] for k in ("sections", "turnons_last", "lowoffs_last", "highoffs_last"))
    c, R = {}, {}
    c["1_identity"] = same(A.load(Q / "run_q100_m3n.json"), A.load(IDENT / "run_q100_m3n.json"))
    ok2, ok3 = True, True
    for m in ("070", "100", "130"):
        for row in ROWS:
            s, q = A.stats(A.load(COS / f"run_s{m}_{row}.json"), row), A.stats(A.load(Q / f"run_q{m}_{row}.json"), row)
            su = lambda x: x["startup_peak_a"] or x["ipk_a"]
            if row in ("m3n", "m1n"):
                ok2 &= s["late"] <= 100 and s["late"] <= q["late"]
            ok2 &= su(s) <= su(q) and (m != "100" or su(s) <= 200.0)
            if row in STEPPED:
                ok3 &= abs(s["peak_after_a"] - q["peak_after_a"]) <= 7.0
            ok3 &= not s.get("locked_ph", False)
            R[f"{m}_{row}"] = {"s": s, "q": q}
    c["2_handover"], c["3_operating_unchanged"] = bool(ok2), bool(ok3)
    (HERE / "a137_summary.json").write_text(json.dumps({"criteria": c, "runs": R}, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in c.items()))
    for k, v in R.items():
        s, q = v["s"], v["q"]
        print(f"{k:12s} late {s['late']:3d} (A136 {q['late']:3d}) start-up {s['ipk_a']:5.1f} (A136 {q['ipk_a']:5.1f}) "
              f"post {s['peak_after_a']:5.1f} (A136 {q['peak_after_a']:5.1f}) lock {s.get('locked_ph')}")


if __name__ == "__main__":
    main()
