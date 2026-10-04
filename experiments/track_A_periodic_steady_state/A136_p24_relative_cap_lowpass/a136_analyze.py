"""A136 analysis against BOUNDARY Section 2 -> a136_summary.json, with A135's per-run statistics (a135_analyze.stats:
post-step peak at t >= 1000 us, lock vs the same row of A129's g125 + 0.5 points, recovery, per-phase end Ton) and
matrix rule. `1`: identity and the stage-1 gate; `2` (default): everything."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("a135_analyze", HERE.parent / "A135_p24_relative_cap" / "a135_analyze.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
COS, A135_COS, IDENT = HERE / "cosim", HERE.parent / "A135_p24_relative_cap" / "cosim", PROJECT / "tmp" / "identity_a136"
load, A133, A129 = A.load, A.A133, A.A129
RISING = ("l_p48_1us", "l_p48_5us")
STEP7 = A.A124_ROWS                                                  # the seven step rows


def main(stage):
    same = lambda a, b: all(a[k] == b[k] for k in ("sections", "turnons_last", "lowoffs_last", "highoffs_last"))
    c, R = {}, {}
    c["1_identity"] = same(load(A135_COS / "run_r100_l_p48_1us.json"), load(IDENT / "run_r100_l_p48_1us.json"))
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        R[name] = A.stats(load(f), name.split("_", 1)[1])
    F = {r: A.stats(load(A135_COS / f"run_f100_{r}.json"), r) for r in STEP7 + ("x_l_p80_10us",)}
    s1 = [f"q{m}_{r}" for m in ("070", "100", "130") for r in ("l_p48_1us", "l_p48_5us", "x_l_p80_10us", "s_p62", "n0")]
    c["2_stage1_gate"] = bool(all(abs(R[f"q100_{r}"]["peak_after_a"] - F[r]["peak_after_a"]) <= 7.0 for r in RISING)
                              and all(not R[k].get("locked_ph", False) for k in s1)
                              and all(R[f"q{m}_{r}"]["peak_after_a"] <= 200.0 for m in ("070", "100", "130") for r in RISING))
    out = {"criteria": c, "f100": {r: x["peak_after_a"] for r, x in F.items()}}
    if stage == "2":
        for m in A.MS:
            tag = f"q{round(m * 100):03d}"
            w0 = A.window_stats(load(COS / f"run_{tag}_n0.json"))
            for row in A.MATRIX_ROWS:
                R[f"{tag}_{row}"]["matrix_ok"] = A.matrix_ok(load(COS / f"run_{tag}_{row}.json"), R[f"{tag}_{row}"], w0, row)
        ok = True
        for row in ("n0", "s_p62", "s_m62") + A.MATRIX_ROWS:
            a, b = A133.tail(load(A129 / f"run_g125_{row}.json")), A133.tail(load(COS / f"run_q100_{row}.json"))
            ra = A.A134.lock(load(A129 / f"run_g125_{row}.json"))["rails_end_v"]
            ok &= max(abs(p - q) for p, q in zip(a["valley_mean_a"] + a["peak_a"], b["valley_mean_a"] + b["peak_a"])) <= 0.2
            ok &= max(abs(p - q) for p, q in zip(ra, R[f"q100_{row}"]["rails_end_v"])) <= 0.02
        d = {r: R[f"q100_{r}"]["peak_after_a"] - F[r]["peak_after_a"] for r in STEP7}
        q = lambda m, r: R[f"q{round(m * 100):03d}_{r}"]
        c["3a_l0_unchanged"] = bool(ok and all(abs(v) <= 7.0 for v in d.values()))
        c["3b_no_lock"] = all(not v.get("locked_ph", False) for v in R.values())
        c["3c_peaks"] = all(q(m, r)["peak_after_a"] <= 200.0 for m in A.MS for r in STEP7) and all(q(m, r)["matrix_ok"] for m in A.MS for r in A.MATRIX_ROWS)
        c["3d_recovery"] = all(np.isfinite(q(m, r)["back_us"]) and q(m, r)["late"] <= 100 and q(m, r)["overlaps"] == 0 for m in A.MS for r in STEP7)
        out["l0_delta_vs_f100_a"] = d
        out["per_l"] = {str(m): {"a124_pk_max_a": max(q(m, r)["peak_after_a"] for r in STEP7),
                                 "fail_peak": [r for r in STEP7 if q(m, r)["peak_after_a"] > 200.0],
                                 "fail_matrix": [r for r in A.MATRIX_ROWS if not q(m, r)["matrix_ok"]],
                                 "back_max_us": max(q(m, r)["back_us"] for r in STEP7),
                                 "late_max": max(q(m, r)["late"] for r in STEP7 + A.MATRIX_ROWS + ("n0",)),
                                 "startup_max_a": max((q(m, r)["startup_peak_a"] or 0) for r in STEP7 + A.MATRIX_ROWS + ("n0",)),
                                 "ton_n0_ns": q(m, "n0")["ton_end_ns"]} for m in A.MS}
    out["runs"] = R
    (HERE / f"a136_summary{'_stage1' if stage == '1' else ''}.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in c.items()))
    print("f100:", " ".join(f"{r}:{x['peak_after_a']:.1f}" for r, x in F.items()))
    for k in sorted(R):
        x = R[k]
        if stage == "1" and k not in s1:
            continue
        print(f"{k:18s} pk {x['peak_after_a']:5.1f} late {x['late']:3d} back {x['back_us']:6.1f} ext {x['extreme_mv']:6.1f} "
              f"lock {x.get('locked_ph')} start-up {x['startup_peak_a'] or 0:.0f} Ton {'/'.join(f'{t:.1f}' for t in x['ton_end_ns'])}")
    if stage == "2":
        for m, p in out["per_l"].items():
            print(f"q L x{m}: A124 pk {p['a124_pk_max_a']:.1f} >200 {','.join(p['fail_peak']) or '-'} matrix fail {','.join(p['fail_matrix']) or '-'} "
                  f"back max {p['back_max_us']:.1f} late max {p['late_max']} start-up {p['startup_max_a']:.0f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2")
