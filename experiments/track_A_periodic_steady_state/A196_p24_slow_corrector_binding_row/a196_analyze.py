"""A196 analysis (BOUNDARY Section 2). Per run: a192_analyze.run (start-up, handover, post-step peak, V_DS, Vo over
0-300 us, late fires, oracle NEW events, Vo extreme and recovery), the largest physical peak of the whole run, and
a195_analyze.alt over 459-499 us (the valley's cycle-to-cycle change before the step). The same numbers for the
reference record (same cfg but for the two corrector registers). Criteria c1-c4 per run, c5 per temperature
(summary key criteria_c5, the form scripts/acceptance.py reads).
  python3 a196_analyze.py           the A196 runs -> a196_summary.json
  python3 a196_analyze.py refs      the reference records only (no file written)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A192 = _load("a192", "A192_p24_slow_lead_rows/a192_analyze.py")
A195 = _load("a195", "A195_p24_slow_corner_two_cycle_orbit/a195_analyze.py")
REF = {"c0": TA / "A193_p24_slow_lead_cold" / "cosim" / "run_S75_c0_l9p5_p{k}.json",
       "25": TA / "A192_p24_slow_lead_rows" / "cosim" / "run_S75_25_p48_1us_p{k}.json"}
PRE = (459e-6, 499e-6)
GAIN_A, RISE_A = 195.5, 1.0


def one(path):
    _, out = A192.run(str(path))
    r = json.loads(Path(path).read_text())
    a = A195.alt(path, *PRE)
    out.update(whole_pk=max(e["i_max_a"] for e in r["gate_offs_last"]), valley_alt=a["valley_alt"], peak_alt=a["peak_alt"],
               valley_mean=a["valley_mean"], steady_peak_max=max(a["peak_max"]), overlaps=len(r.get("overlaps") or []),
               commit=r["provenance"]["git_commit"][:7], sources_modified=r["provenance"]["cosim_sources_modified"])
    c = out.pop("criteria")
    out["criteria"] = {"c1": c["c3"], "c2": out["whole_pk"] <= 200.0, "c3": c["c7"], "c4": max(a["valley_alt"]) <= 1.0}
    return out


def main(refs_only=False):
    res = {"runs": {}, "reference": {}, "criteria_c5": {}}
    for temp, pat in REF.items():
        for k in (0, 1, 2):
            name = f"S75_{temp}_p{k}"
            res["reference"][name] = one(Path(str(pat).format(k=k)))
            f = HERE / "cosim" / f"run_{name}.json"
            if f.exists() and not refs_only:
                res["runs"][name] = one(f)
        new = [res["runs"].get(f"S75_{temp}_p{k}") for k in (0, 1, 2)]
        ref = [res["reference"][f"S75_{temp}_p{k}"] for k in (0, 1, 2)]
        if all(new):
            d = [n["peak_post"] - r["peak_post"] for n, r in zip(new, ref)]
            res["criteria_c5"][temp] = {"worst": max(n["peak_post"] for n in new), "worst_ref": max(r["peak_post"] for r in ref), "delta": d,
                               "pass": max(n["peak_post"] for n in new) <= GAIN_A and max(d) <= RISE_A}
    if not refs_only:
        (HERE / "a196_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for lab in ("reference", "runs"):
        for k, s in res[lab].items():
            print(f"{lab[:3]} {k:11s} start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} post {s['peak_post']:5.1f} whole {s['whole_pk']:5.1f} "
                  f"V {s['vds_whole']:.1f} Vo300 {s['vo_max_300us']:.4f} | valley change {' '.join(f'{x:4.2f}' for x in s['valley_alt'])} A "
                  f"steady pk {s['steady_peak_max']:5.1f} | late {s['late_post']} NEW {s['oracle_new']} ext {s['extreme_mv']:+.1f} mV "
                  f"back {s['back_within_1pct_us']} | {s['criteria']} {s['commit']} mod {s['sources_modified']}")
    for t, c in res["criteria_c5"].items():
        print(f"c5 {t}: worst {c['worst']:.1f} A (reference {c['worst_ref']:.1f}), per position {' '.join(f'{x:+.1f}' for x in c['delta'])} A -> {c['pass']}")


if __name__ == "__main__":
    main(sys.argv[1:] == ["refs"])
