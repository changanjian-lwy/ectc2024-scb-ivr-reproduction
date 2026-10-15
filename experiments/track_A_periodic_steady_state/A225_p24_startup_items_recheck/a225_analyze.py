"""A225 analysis (BOUNDARY Section 2). a rows: a223_analyze.one (whole-run and post-step peaks, Vo, rail 1, late
fires) - f2: whole-run peak <= 200 A, no overlap or shoot-through, V_DS <= 40 V, Vo within 1 % over the last 20 us.
u rows: the start-up (Vo's maximum over the run, start-up / handover / whole-run peaks, mode P's entry, Vo at the
end) - f6: A206's c6 terms (Vo <= 1.05 V, peaks <= 200 A, no overlap, V_DS <= 40 V) and Vo within 1 % at the end.
s rows: a195_analyze.alt over the last 40 us - f5: every phase's mean |valley change| from one period to the next
<= 1 A. Also A198's / A214's / A211's records for the same rows, for comparison.
  python3 a225_analyze.py -> a225_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A23 = _load("a223_analyze", "A223_p24_cap_on_rising_vin/a223_analyze.py")
A95 = _load("a195_analyze", "A195_p24_slow_corner_two_cycle_orbit/a195_analyze.py")
COS = HERE / "cosim"
ALT_MAX_A = 1.0
REF_A = {"a_S75h_d2": "S75_hot_d2", "a_S75h_d10": "S75_hot_d10", "a_S75h_d20": "S75_hot_d20", "a_S75_d2": "S75_25_d2",
         "a_S75_d10": "S75_25_d10", "a_S75_d20": "S75_25_d20", "a_N0_d2": "N0_25_d2"}
REF_U = {"u_N0_30": "A214_p24_startup_light_load/cosim/run_u_N0_25_30.json"}
REF_S = {"s_S75_100": "A211_p24_loss_against_load/cosim/run_e_S75_25_100.json",
         "s_S75_50": "A211_p24_loss_against_load/cosim/run_e_S75_25_50.json"}
REF_S |= {k + "_rc2": v for k, v in REF_S.items()}


def ref_peak(name):
    f = TA / "A198_p24_step_right_after_handover" / "cosim" / f"run_{REF_A[name]}.json"
    if not f.exists():
        return None
    return max(e["i_max_a"] for e in json.loads(f.read_text())["gate_offs_last"])


def startup(path):
    r = json.loads(Path(path).read_text())
    tp, g, sec = r["t_mode_p_s"], r["gate_offs_last"], r["sections"]
    pk = lambda a, b: max((e["i_max_a"] for e in g if a <= e["t_s"] < b), default=None)
    vo = np.array([q["vo"] for q in sec]); ts = np.array([q["t_s"] for q in sec])
    last = ts >= ts[-1] - 20e-6
    return {"status": r["status"], "t_mode_p_us": tp * 1e6, "t_hand_req_us": None if r.get("t_hand_req_s") is None else r["t_hand_req_s"] * 1e6,
            "vin_at_entry_v": float(np.interp(tp, ts, [q["vin_v"] for q in sec])), "start_pk": pk(0.0, tp),
            "hand_pk": pk(tp, tp + 40e-6), "peak_whole": pk(0.0, 1.0), "vo_max_v": float(vo.max()),
            "vo_min_after_entry_v": float(vo[ts >= tp].min()), "vo_last": [float(vo[last].min()), float(vo[last].max())],
            "vds_v": max(r["vds_max_v"]), "overlaps": r["overlaps"], "shoot_on": sum(r["gate_stats"]["shoot_on"]),
            "late": sum(sec[-1]["late"])}


def main():
    res = {"a": {}, "u": {}, "s": {}}
    for f in sorted(COS.glob("run_*.json")):
        n = f.stem[4:]
        if n.startswith("a_"):
            m = A23.one(f)
            m["f2"] = bool(m["status"] == "COMPLETED" and m["peak_whole"] <= A23.I_LIM and not m["overlaps"] and not m["shoot_on"]
                           and m["vds_whole"] <= A23.V_LIM and abs(m["vo_last_min_v"] - 1) <= A23.VO_BAND
                           and abs(m["vo_last_max_v"] - 1) <= A23.VO_BAND)
            m["a198_v5_peak"] = ref_peak(n)
            res["a"][n] = m
        elif n.startswith("u_"):
            m = startup(f)
            m["f6"] = bool(m["status"] == "COMPLETED" and m["vo_max_v"] <= 1.05 and m["peak_whole"] <= A23.I_LIM and not m["overlaps"]
                           and not m["shoot_on"] and m["vds_v"] <= A23.V_LIM and all(abs(v - 1) <= A23.VO_BAND for v in m["vo_last"]))
            if n in REF_U and (TA / REF_U[n]).exists():
                m["a214_v6"] = startup(TA / REF_U[n])
            res["u"][n] = m
        elif n.startswith("s_"):
            r = json.loads(f.read_text())
            o = A95.alt(f, r["t_end_s"] - 40e-6, r["t_end_s"])
            o["f5"] = bool(max(o["valley_alt"]) <= ALT_MAX_A)
            if (TA / REF_S[n]).exists():
                rr = json.loads((TA / REF_S[n]).read_text())
                o["a211_v6"] = A95.alt(TA / REF_S[n], rr["t_end_s"] - 40e-6, rr["t_end_s"])
            res["s"][n] = o
    (HERE / "a225_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    for n, m in res["a"].items():
        print(f"{n:11s} whole {m['peak_whole']:6.1f} A (A198 V5 {m['a198_v5_peak'] or float('nan'):6.1f}) hand {m['hand_pk']:.1f} "
              f"post {m['post_pk']:.1f} | Vo {m['vo_ext_mv']:+.1f} mV | late {sum(m['late_after'])} | f2 {m['f2']}")
    for n, m in res["u"].items():
        print(f"{n:11s} entry {m['t_mode_p_us']:.1f} us Vin {m['vin_at_entry_v']:.1f} V | Vo max {m['vo_max_v']:.4f} min {m['vo_min_after_entry_v']:.4f} | "
              f"start {m['start_pk']:.1f} hand {m['hand_pk']:.1f} | f6 {m['f6']}" + (f" | A214 V6 Vo max {m['a214_v6']['vo_max_v']:.4f}" if "a214_v6" in m else ""))
    for n, o in res["s"].items():
        print(f"{n:11s} valley_alt {[round(x, 2) for x in o['valley_alt']]} mean {[round(x, 1) for x in o['valley_mean']]} | f5 {o['f5']}"
              + (f" | A211 V6 {[round(x, 2) for x in o['a211_v6']['valley_alt']]}" if "a211_v6" in o else ""))


if __name__ == "__main__":
    main()
