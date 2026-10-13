"""A214 analysis (BOUNDARY Section 2). Per row: c6 (a206_analyze.whole) and the start-up's numbers: when the handover
is requested and mode P entered, Vin there, Vo's maximum and its time, Vo's minimum after the entry, the start-up and
handover peaks, and at the end Vo, the Ton register and the late fires since 20 us after the entry.
  python3 a214_analyze.py -> a214_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a206_analyze", HERE.parent / "A206_p24_low_side_zvs_turn_on" / "a206_analyze.py")
A6 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A6)
COS = HERE / "cosim"
R_FULL = 4e-3


def one(path):
    w = A6.whole(path)
    r = json.loads(Path(path).read_text())
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    vin = np.array([q["vin_v"] for q in r["sections"]]); tl = np.array([q["ton_lsb"] for q in r["sections"]], float) * r["lsb_s"] * 1e9
    tp = r["t_mode_p_s"]
    aft = ts >= tp
    last = ts >= ts[-1] - 20e-6
    k20 = int(np.searchsorted(ts, tp + 20e-6))
    r_load = r["snap_circuit"]["r_load"] if "snap_circuit" in r else (r["cfg"].get("circuit") or {}).get("r_load", R_FULL)
    out = {k: w[k] for k in ("status", "commit", "sources_modified", "wall_s", "shoot_on", "overlaps", "forced", "il_holds", "start_pk", "hand_pk",
                             "after_pk", "peak_whole", "vds_whole", "vo_max_to_300us", "vo_dev_max_mv", "t_mode_p_us", "t_hand_req_us")}
    out.update(share=R_FULL / (r["cfg"].get("circuit") or {}).get("r_load", R_FULL), vin_at_entry_v=float(np.interp(tp, ts, vin)),
               vo_at_entry_v=float(np.interp(tp, ts, vo)), vo_max_v=float(vo.max()), t_vo_max_us=1e6 * float(ts[np.argmax(vo)]),
               vo_min_after_entry_v=float(vo[aft].min()), t_vo_min_us=1e6 * float(ts[aft][np.argmin(vo[aft])]),
               vo_end_v=[float(vo[last].min()), float(vo[last].max())], ton_reg_end_ns=[float(tl[last].min()), float(tl[last].max())],
               ton_reg_min_ns=float(tl[aft].min()), late_fires=r["late_fires"],
               late_after_20us=(np.array(r["sections"][-1]["late"]) - np.array(r["sections"][min(k20, len(ts) - 1)]["late"])).tolist(),
               ton_s_ns=r["cfg"].get("ton_s_ns"), ton_min_ns=r["cfg"].get("ton_min_ns"))
    out["criteria"] = {"c6": w["criteria"]["c6"]}
    return out


def main():
    res = {"runs": {f.stem[4:]: one(f) for f in sorted(COS.glob("run_u_*.json"))}}
    (HERE / "a214_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for n, m in res["runs"].items():
        print(f"{n:14s} {m['status'][:4]} {100 * m['share']:.0f} % | request {m['t_hand_req_us']} us, mode P at {m['t_mode_p_us']:.1f} us (Vin {m['vin_at_entry_v']:.1f} V, Vo {m['vo_at_entry_v']:.4f}) | "
              f"Vo max {m['vo_max_v']:.4f} at {m['t_vo_max_us']:.1f} us, min after entry {m['vo_min_after_entry_v']:.4f} at {m['t_vo_min_us']:.1f} us, end "
              f"{m['vo_end_v'][0]:.4f}..{m['vo_end_v'][1]:.4f} | peaks start {m['start_pk']:.1f} hand {m['hand_pk']:.1f} after {m['after_pk']} whole {m['peak_whole']:.1f} | "
              f"V_DS {m['vds_whole']:.1f} | register end {m['ton_reg_end_ns'][0]:.2f}..{m['ton_reg_end_ns'][1]:.2f} ns (lowest {m['ton_reg_min_ns']:.2f}) | "
              f"late {m['late_fires']} (after +20 us {m['late_after_20us']}) holds {m['il_holds']} shoot {m['shoot_on']} | {m['criteria']}")


if __name__ == "__main__":
    main()
