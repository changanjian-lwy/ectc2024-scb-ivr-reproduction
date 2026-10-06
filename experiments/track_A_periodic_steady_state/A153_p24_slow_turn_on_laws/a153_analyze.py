"""A153 analysis against BOUNDARY Section 2 -> a153_summary.json; prints <= 15 lines.
u rows: Vo at the section nearest 143.5 us (A152's convention) against a153_predictions.json.
v rows: A152's run_stats (A148 oracles, start-up / handover / post-step peaks, V_DS windows, Vo at 143.5 us)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_spec = importlib.util.spec_from_file_location("a152_analyze", HERE.parent / "A152_p24_drive_spec_robustness" / "a152_analyze.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


def vo_hand(path):
    d = json.loads(Path(path).read_text())
    return min(d["sections"], key=lambda q: abs(q["t_s"] - 143.5e-6))["vo"], d["status"]


def main():
    pred = json.loads((HERE / "a153_predictions.json").read_text())
    runs, crit = {}, {}
    c1 = {}
    for n, p in pred["start"].items():
        vo, st = vo_hand(COS / f"run_{n}.json")
        inside = p["band"][0] - 0.005 <= vo <= p["band"][1] + 0.005
        closer = abs(vo - p["vo"]) < abs(vo - p["vo_a152_rule"])
        runs[n] = dict(vo=vo, status=st, pred=p["vo"], band=p["band"], rule=p["vo_a152_rule"], inside=inside, d68_closer=closer)
        c1[n] = inside and st == "COMPLETED" and (closer if n in ("u24_l100", "u06_l100") else True)
    crit["1_startup_law"] = c1
    c2, c3, c4, c5 = {}, {}, {}, {}
    for n, p in pred["line"].items():
        r = B.run_stats(COS / f"run_{n}.json")
        v = r["vds"]["whole"]
        runs[n] = dict(r, pred_vds=p["vds_max_v"], x_v=p["x_v"], pred_vo_hand=p["vo_hand"])
        c2[n] = abs(v - p["vds_max_v"]) <= 1.0
        c3[n] = (v <= 40.0) == p["le_40"]
        c4[n] = r["start_pk"] is not None and r["start_pk"] <= 165.0 and abs(r["vo_hand"] - p["vo_hand"]) <= 0.015
        c5[n] = bool(r["ok_status"]) and r["peak_post"] <= 190.0 and not r["oracle_new"]
    crit.update({"2_overshoot_band": c2, "3_40v_side": c3, "4_startup_ton": c4, "5_controller": c5})
    out = {"runs": runs, "criteria": crit}
    (HERE / "a153_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for n, r in runs.items():
        if n.startswith("u"):
            print(f"{n}: Vo {r['vo']:.4f} pred {r['pred']:.4f} [{r['band'][0]:.4f}, {r['band'][1]:.4f}] rule {r['rule']:.4f}"
                  f" -> {'in' if r['inside'] else 'OUT'}, D68 closer {r['d68_closer']}")
        else:
            print(f"{n} (x {r['x_v']:.1f} V): V_DS {r['vds']['whole']:.1f} (pred {r['pred_vds']:.1f}; start {r['vds']['start']:.1f}, "
                  f"post {r['vds']['post']:.1f}), start pk {r['start_pk']:.0f} A, Vo hand {r['vo_hand']:.4f} "
                  f"(pred {r['pred_vo_hand']:.4f}), post {r['peak_post']:.1f} A, NEW {r['oracle_new']}, late {r['late']}")
    for k, v in crit.items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(n for n, ok in v.items() if not ok)}")


if __name__ == "__main__":
    main()
