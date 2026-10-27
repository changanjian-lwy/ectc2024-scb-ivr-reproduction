"""A256 (BOUNDARY Section 1): the up/down count of limited pulses (+1 limited, -1 clean, floor 0) per phase, replayed on
A254's records (cosim/run_l_*.json): its largest value and the longest run of limited pulses, per row with fires.
A fire is a high-side turn-off at the same instant as an entry of ocp_fires.
  python3 a256_counts.py -> a256_counts.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A54 = HERE.parent / "A254_p24_peak_limit_measured_level" / "cosim"


def counts(md):
    fires = {(round(x["t_s"] * 1e12), x["phase"]) for x in md.get("ocp_fires", [])}
    out = {}
    for k in range(1, 5):
        c = cmax = run = rmax = 0
        t_max = None
        for t in sorted(x["t_s"] for x in md["highoffs_last"] if x["phase"] == k):
            hit = (round(t * 1e12), k) in fires
            c = c + 1 if hit else max(c - 1, 0)
            run = run + 1 if hit else 0
            rmax = max(rmax, run)
            if c > cmax:
                cmax, t_max = c, t
        out[k] = {"max": cmax, "run": rmax, "t_us": None if t_max is None else 1e6 * t_max}
    return out


def main():
    res = {}
    for f in sorted(A54.glob("run_l_*.json")):
        d = json.loads(f.read_text())
        mods = [d] + d.get("modules_rest", [])
        if not any(md.get("ocp_fires") for md in mods):
            continue
        per = [counts(md) for md in mods]
        res[f.stem[6:]] = {"fires": sum(len(md.get("ocp_fires", [])) for md in mods),
                           "max": max(v["max"] for p in per for v in p.values()),
                           "run": max(v["run"] for p in per for v in p.values())}
    (HERE / "a256_counts.json").write_text(json.dumps(res, indent=1) + "\n")
    for r, x in sorted(res.items(), key=lambda kv: -kv[1]["max"]):
        print(f"{r:16s} fires {x['fires']:5d} count max {x['max']:4d} run {x['run']:4d}")


if __name__ == "__main__":
    main()
