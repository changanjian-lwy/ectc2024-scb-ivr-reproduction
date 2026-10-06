"""A160 scan: A142's oracles on every local cosim record with a line or load step, K4 window 1.0 us (current) and 2.0 us
(proposed); per run the NEW counts and every event the wider window reclassifies (time after the ramp's end, kind,
current, the run's post-step peak). Writes a160_scan.json; prints <= 15 lines. Uses 8 processes."""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "A142_p24_random_stimulus"))
import a142_oracles as O  # noqa: E402

DIRS = sorted([p for p in (ROOT / "experiments").glob("track_*/A1[4-5][0-9]_*/cosim")] +
              [p for p in (ROOT / "experiments" / "track_C_multi_module").glob("C1[34]_*/cosim")] +
              [p for p in (ROOT / "extensions" / "ml_design_assist" / "experiments").glob("A1[45][0-9]_*/cosim")])


def one(path):
    d = json.loads(Path(path).read_text())
    cfg = d["cfg"]
    if not (cfg.get("line_step") or cfg.get("load_step")):
        return None
    out = {}
    for w in (1.0, 2.0):
        O.K4_US = w
        out[w] = [e for e in O.check_dict(d, path.name)["events"] if e["cls"] == "NEW"]
    ls, ld = cfg.get("line_step"), cfg.get("load_step")
    t_end = (ls["t_us"] + ls["slew_us"]) if ls else ld["t_us"]
    k2 = {(e["t_s"], e["kind"], e["phase"], e["module"]) for e in out[2.0]}
    moved = [e for e in out[1.0] if (e["t_s"], e["kind"], e["phase"], e["module"]) not in k2]
    post = max((q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= t_end * 1e-6 - (ls["slew_us"] * 1e-6 if ls else 0.0)), default=None)
    return {"run": f"{path.parent.parent.name.split('_')[0]}/{path.stem[4:]}", "new_1": len(out[1.0]), "new_2": len(out[2.0]),
            "moved": [{"dt_after_us": round(e["t_s"] * 1e6 - t_end, 3), "kind": e["kind"], "i_a": round(e.get("i_a", 0.0), 1),
                       "excess_a": round(e.get("excess_a", 0.0), 1)} for e in moved], "post_peak_a": post}


def main():
    files = [f for d in DIRS for f in sorted(d.glob("run_*.json"))]
    with Pool(8) as p:
        rs = [r for r in p.map(one, files) if r]
    (HERE / "a160_scan.json").write_text(json.dumps(rs, indent=1) + "\n")
    moved = [(r["run"], m) for r in rs for m in r["moved"]]
    cleared = [r["run"] for r in rs if r["new_1"] and not r["new_2"]]
    still = [r["run"] for r in rs if r["new_2"]]
    print(f"{len(files)} records, {len(rs)} with a step; NEW runs {sum(1 for r in rs if r['new_1'])} -> {len(still)}; "
          f"events reclassified {len(moved)}")
    print("cleared:", " ".join(cleared))
    print("non-spike or > post-step peak among reclassified:",
          [(n, m) for n, m in moved if m["kind"] != "spike"] or "none")
    print("still NEW (first 20):", " ".join(still[:20]))


if __name__ == "__main__":
    main()
