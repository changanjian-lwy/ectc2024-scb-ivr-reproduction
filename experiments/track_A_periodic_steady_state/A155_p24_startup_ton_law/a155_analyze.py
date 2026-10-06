"""A155 analysis against BOUNDARY Section 2 -> a155_summary.json; prints <= 10 lines. Per run: Vo at the section nearest
143.5 us, start-up peak (high-side turn-off current, t < 300 us), start-up V_DS (vds_win, t < 300 us), status."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"


def stats(path):
    d = json.loads(Path(path).read_text())
    return dict(status=d["status"], src_modified=d["provenance"].get("cosim_sources_modified"),
                vo=min(d["sections"], key=lambda q: abs(q["t_s"] - 143.5e-6))["vo"],
                full=d["highoffs_last"][0]["t_s"] < 1e-6,
                start_pk=max(e["i_a"] for e in d["highoffs_last"] if e["t_s"] < 300e-6),
                vds_start=max(max(q["vds_win_v"]) for q in d["sections"] if q.get("vds_win_v") and q["t_s"] < 300e-6))


def main():
    pred = json.loads((HERE / "a155_predictions.json").read_text())
    runs = {n: dict(stats(COS / f"run_{n}.json"), pred=p) for n, p in pred.items()}
    law = [n for n in runs if n.startswith("s")]
    ok = lambda r: r["status"] == "COMPLETED" and r["src_modified"] is False and r["full"]
    crit = {"1_vo": {n: ok(runs[n]) and abs(runs[n]["vo"] - 1.015) <= 0.010 for n in law},
            "2_start_peak": {n: runs[n]["start_pk"] <= 165.0 for n in law},
            "3_control": {"c300": ok(runs["c300"]) and abs(runs["c300"]["vo"] - pred["c300"]["vo"]) <= 0.010
                          and runs["c300"]["vo"] < 1.005},
            "4_vds_start": {n: r["vds_start"] <= 40.0 for n, r in runs.items()}}
    (HERE / "a155_summary.json").write_text(json.dumps({"runs": runs, "criteria": crit}, indent=1, default=float) + "\n")
    for n, r in runs.items():
        print(f"{n}: ton {r['pred']['ton']} Vo {r['vo']:.4f} (pred {r['pred']['vo']:.4f}) start {r['start_pk']:.0f} A, "
              f"V_DS {r['vds_start']:.1f} V, {r['status']}")
    for k, v in crit.items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(n for n, x in v.items() if not x)}")


if __name__ == "__main__":
    main()
