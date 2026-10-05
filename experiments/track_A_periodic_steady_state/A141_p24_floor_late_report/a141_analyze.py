"""A141 analysis against BOUNDARY Section 2 -> a141_summary.json. Statistics as make_cfgs.stats; t_div = the first
master section whose (vo, ton_lsb) differs from the reference record, t_ff1 = the reference's first floor-first
duplicate (any module): a row replays its reference up to its first late report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_cfgs as M  # noqa: E402

COS = HERE / "cosim"
IDENT = {"I0_B_L070_p4.8_s10.0": M.A140 / "run_B_L070_p4.8_s10.0.json", "I1_s100_n0": M.C10 / "run_s100_n0.json"}


def load(p):
    return json.loads(Path(p).read_text())


def same(a, b):
    sa, sb = a["sections"], b["sections"]
    return (len(sa) == len(sb) and all(x["vo"] == y["vo"] and x["ton_lsb"] == y["ton_lsb"] for x, y in zip(sa, sb))
            and [o["t_s"] for o in a["turnons_last"]] == [o["t_s"] for o in b["turnons_last"]])


def t_div(a, b):
    for x, y in zip(a["sections"], b["sections"]):
        if x["vo"] != y["vo"] or x["ton_lsb"] != y["ton_lsb"]:
            return x["t_s"]
    return None


def main():
    pred = load(HERE / "a141_predictions.json")["runs"]
    out = {"criteria": {}, "runs": {}}
    out["criteria"]["1_identity"] = {n: bool(same(load(COS / f"run_{n}.json"), load(p))) for n, p in IDENT.items()}
    out["criteria"]["1_identity"]["pass"] = all(out["criteria"]["1_identity"].values())
    for n, p in pred.items():
        f = COS / f"run_{n}.json"
        if not f.exists():
            continue
        s = M.stats(f)
        ref = load(M.PROJECT / p["ref"])
        ff1 = [o["t_s"] for md in [ref] + ref.get("modules_rest", []) for o in M.floor_first(md)[0]]
        td = t_div(load(f), ref)
        out["runs"][n] = {"peak": s["peak"], "module": s["module"], "env3": s["env3"], "ref_peak": p["peak"],
                          "ref_nodup": p["nodup"], "d_nodup": s["peak"] - p["nodup"], "ff_all": s["ff_all"],
                          "other_dup": s["other_dup"], "late": s["late"], "overlaps": s["overlaps"],
                          "t_div_us": td * 1e6 if td else None, "t_ff1_us": min(ff1) * 1e6 if ff1 else None}
    R = out["runs"]
    out["criteria"]["2_no_floor_first"] = {"pass": all(r["ff_all"] == 0 for r in R.values()),
                                           "rows_with": {n: r["ff_all"] for n, r in R.items() if r["ff_all"]}}
    out["criteria"]["3_peak_le_nodup_2A"] = {"pass": all(r["d_nodup"] <= 2.0 for r in R.values()),
                                             "misses": {n: round(r["d_nodup"], 2) for n, r in R.items() if r["d_nodup"] > 2.0}}
    spec = {}
    for n, r in R.items():
        if n.startswith("F_L070_p"):
            key = n[:-3] if n.endswith(("_q1", "_q2", "_q3")) else n
            spec[key] = max(spec.get(key, 0.0), r["peak"])
    out["spec_L070_rising_max_a"] = spec
    (HERE / "a141_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    c = out["criteria"]
    print(f"runs {len(R)}/{len(pred)}; 1 identity {c['1_identity']}")
    print(f"2 no floor-first {c['2_no_floor_first']['pass']} {c['2_no_floor_first']['rows_with']}")
    print(f"3 peak <= nodup + 2 A {c['3_peak_le_nodup_2A']['pass']} misses {c['3_peak_le_nodup_2A']['misses']}")
    cells = [f"{n[2:]:20s} {r['peak']:5.1f} ({r['ref_peak']:5.1f}/{r['ref_nodup']:5.1f} {r['d_nodup']:+5.1f})"
             for n, r in R.items()]
    for i in range(0, len(cells), 2):
        print(" | ".join(cells[i:i + 2]))


if __name__ == "__main__":
    main()
