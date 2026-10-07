"""A162 analysis against BOUNDARY Section 2 -> a162_summary.json; prints <= 12 lines.
1. Identity: every record field of the late_log run equals the original run, except wall time, provenance, cfg / note /
   out and the sections' new "late" field.
2. Location: the per-section increments of the cumulative late-fire counters, by time and phase."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
ORIG = {"r150": TA / "A161_p24_150ph_faster_turn_on/cosim/run_s150_l_m80_10us.json",
        "r100": TA / "A152_p24_drive_spec_robustness/cosim/run_s100_l_m80_10us.json"}
SKIP = {"wall_s", "provenance", "cfg"}
T0, T1 = 1000e-6, 1030e-6                     # ramp start, ramp end (1010 us) + 20 us


def identical(a, b):
    diffs = []
    for k in sorted(set(a) | set(b)):
        if k in SKIP:
            continue
        x, y = a.get(k), b.get(k)
        if k == "sections":
            x = [{q: v for q, v in s.items() if q != "late"} for s in x]
        if x != y:
            diffs.append(k)
    return diffs


def main():
    out, c1, c2 = {}, {}, {}
    for n, f in ORIG.items():
        new, old = json.loads((COS / f"run_{n}.json").read_text()), json.loads(f.read_text())
        diffs = identical(new, old)
        secs = [s for s in new["sections"] if "late" in s]
        inc, prev = [], [0] * 4
        for s in secs:
            d = [a - b for a, b in zip(s["late"], prev)]
            if any(d):
                inc.append({"t_us": round(s["t_s"] * 1e6, 2), "per_phase": d})
            prev = s["late"]
        tot = sum(sum(e["per_phase"]) for e in inc)
        inside = sum(sum(e["per_phase"]) for e in inc if T0 * 1e6 <= e["t_us"] <= T1 * 1e6)
        per_phase = [sum(e["per_phase"][k] for e in inc) for k in range(4)]
        out[n] = {"diffs": diffs, "total": tot, "final": new["late_fires"], "inside_ramp_20us": inside, "per_phase": per_phase,
                  "increments": inc}
        c1[n] = not diffs
        c2[n] = tot == 0 or inside / tot >= 0.8
    out["criteria"] = {"1_identity": c1, "2_location": c2}
    (HERE / "a162_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for n in ORIG:
        r = out[n]
        print(f"{n}: diffs {r['diffs'] or 'none'}; late {r['total']} (final {r['final']}), in 1000-1030 us {r['inside_ramp_20us']}, "
              f"per phase {r['per_phase']}")
        print("   times: " + " ".join(f"{e['t_us']}:{sum(e['per_phase'])}" for e in r["increments"][:14]))
    for k, v in out["criteria"].items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(x for x, ok in v.items() if not ok)}")


if __name__ == "__main__":
    main()
