"""A94 gates 2-3 (BOUNDARY Section 3): the FastPlant co-simulation replays against the stored runs, bit for bit
(A89's gate(): sections, registers, steps, peaks; plus every recorded edge list on the reference's fields; fields
and keys that only the newer bridge writes are listed as format additions), and their wall times.

Writes a94_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
sys.path.insert(0, str(TA / "A89_verilog_predicted_low_side"))
from a89_analyze import gate  # noqa: E402

LISTS = ("turnons_last", "lowoffs_last", "lowons_last", "late_fires", "trim_final", "dt_pred_final_ns", "dtl_final_ns",
         "async_fires", "t_mode_p_s", "ton_final_lsb", "t_end_s", "first_overlap", "overlaps", "status")


def main():
    out = {"replays": {}, "speed": {}}
    for p in sorted((HERE / "cosim").glob("run_r_*.json")):
        d = json.loads(p.read_text())
        ref = (TA / d["cfg"]["replay_of"]).resolve()
        r = json.loads(ref.read_text())
        g = gate(ref, p.resolve())
        extra, added = {}, sorted(set(d) - set(r))       # keys only in the newer bridge's output: format additions
        for k in LISTS:
            if k not in r:
                continue
            a, b = r[k], d.get(k)
            if isinstance(a, list) and a and isinstance(a[0], dict):     # record lists: compare the reference's fields
                keys = set(a[0])
                extra[k] = len(a) == len(b) and all({q: x[q] for q in keys} == {q: y[q] for q in keys} for x, y in zip(a, b))
                more = sorted(set(b[0]) - keys) if b else []
                if more:
                    added.append(f"{k}: " + ", ".join(more))
            else:
                extra[k] = a == b
        row = {"reference": d["cfg"]["replay_of"], "gate": g, "equal_records": extra, "format_additions": added,
               "bit_identical": bool(g["pass"] and all(extra.values())),
               "wall_s": d["wall_s"], "reference_wall_s": r["wall_s"], "sim_us": d["t_end_s"] * 1e6}
        out["replays"][p.stem[6:]] = row
        print(p.stem, "BIT-IDENTICAL" if row["bit_identical"] else "DIFFERENT", {k: v for k, v in extra.items() if not v},
              "format additions:", added,
              f"wall {row['wall_s']:.0f} s (reference {row['reference_wall_s']:.0f} s)")
    for p in sorted(list((HERE / "cosim").glob("speed_*.json")) + list((HERE / "cosim_orig").glob("speed_*.json"))):
        d = json.loads(p.read_text())
        out["speed"][p.stem] = {"wall_s": d["wall_s"], "sim_us": d["t_end_s"] * 1e6, "us_per_s": d["t_end_s"] * 1e6 / d["wall_s"],
                                "steps": d["steps"]}
        print(p.stem, out["speed"][p.stem])
    out["all_bit_identical"] = bool(out["replays"]) and all(r["bit_identical"] for r in out["replays"].values())
    (HERE / "a94_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
