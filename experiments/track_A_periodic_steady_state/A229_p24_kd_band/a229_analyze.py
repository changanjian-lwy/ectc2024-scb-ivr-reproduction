"""A229 analysis (BOUNDARY Section 2). Part S: arm b's skipping runs through a228_analyze's skip_row path, against
A228's d0 runs at the same instants - q1, q2. Part W: a224_analyze.pair against A223's g25 records - q3. Part I:
arm b against A228's arm h bit for bit - q4. j1 from the unit and regression logs.
  python3 a229_analyze.py -> a229_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
_s = importlib.util.spec_from_file_location("a228_analyze", TA / "A228_p24_damped_loop_adoption" / "a228_analyze.py")
A28 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A28)
A24, A23, A21 = A28.A24, A28.A23, A28.A21
COS, C28 = HERE / "cosim", TA / "A228_p24_damped_loop_adoption" / "cosim"
W_ROWS, I_ROWS = ("w0_N0", "w5_N0", "w20_N0", "w5_N75", "u_N0", "w30_S75h"), ("k_N0", "k_S75h")


def skip_file(f, z):
    v = A21.skip_row(A28.with_snap(f, z))
    va = [y for p in v["true_valleys_a"].values() for y in p]
    c = v["criteria"]
    ok = bool(v["status"] == "COMPLETED" and c["s1"] and c["s2"] and not any(v["late_end"]) and va
              and (z == "z_N0_0" or c["z1r"]))
    lo, hi = v["band_a"]
    return {"record": str(Path(f).relative_to(TA)), "vmin_a": min(va) if va else None, "vmax_a": max(va) if va else None,
            "window_us": v["true_valleys_window_us"], "vo_end_v": [v["vo_end_min_v"], v["vo_end_max_v"]],
            "resume_i0_max_a": v["resume_i0_max_a"], "in_band": bool(va and min(va) >= lo and max(va) <= hi),
            "s": c, "q1_run": ok}


def ton_max_end(f, us=20e-6):
    s = json.loads(Path(f).read_text())["sections"]
    return max(q["ton_lsb"] for q in s if q["t_s"] >= s[-1]["t_s"] - us) * 0.03125


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a229_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a229_reg_{k}.log").read_text())) for k in ("quick", "full")}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "j1": bool(n_pass == 109 and n_fail == 0 and all(reg.values()))}


def main():
    res = {"identity": identity(), "skip_runs": {}, "skip_rows": {}, "part_w": {}, "part_i": {}}
    for z in A28.ROWS:
        b = {t: skip_file(COS / f"run_{z}_{t}_b.json", z) for t in A28.TS}
        d0 = {t: A28.skip_run(z, t, "d0") for t in A28.TS}
        for t in A28.TS:
            b[t]["ton_max_end_ns"] = ton_max_end(COS / f"run_{z}_{t}_b.json")
        res["skip_runs"][z] = {"b": b, "d0": d0}
        st = {}
        for a, rr in (("b", list(b.values())), ("d0", list(d0.values()))):
            st[a] = {"vmin_mean_a": A28.mean([r["vmin_a"] for r in rr]), "vmax_mean_a": A28.mean([r["vmax_a"] for r in rr]),
                     "q1_fails": sum(not r["q1_run"] for r in rr), "in_band": sum(r["in_band"] for r in rr)}
        st["b"]["q1"] = bool(st["b"]["q1_fails"] <= st["d0"]["q1_fails"])
        st["b"]["q2"] = bool(st["b"]["vmin_mean_a"] >= st["d0"]["vmin_mean_a"] - A28.TOL_A
                             and st["b"]["vmax_mean_a"] <= st["d0"]["vmax_mean_a"] + A28.TOL_A)
        res["skip_rows"][z] = st
    for r in W_ROWS:
        v = A24.pair(r, COS / f"run_{r}_b.json")
        h = C28 / f"run_{r}_h.json" if (C28 / f"run_{r}_h.json").exists() else TA / "A227_p24_kd_held_at_the_limit" / "cosim" / f"run_{r}_h.json"
        v["h_post_pk"] = A23.one(h)["post_pk"]
        v["q3"] = bool(all(v["criteria"].values()))
        res["part_w"][r] = v
    for r in I_ROWS:
        res["part_i"][r] = {"q4": A28.same(COS / f"run_{r}_b.json", C28 / f"run_{r}_h.json")}
    q = {"j1": res["identity"]["j1"], "q1": all(v["b"]["q1"] for v in res["skip_rows"].values()),
         "q2": all(v["b"]["q2"] for v in res["skip_rows"].values()), "q3": all(v["q3"] for v in res["part_w"].values()),
         "q4": all(v["q4"] for v in res["part_i"].values())}
    res["criteria_main"], res["adopt"] = q, bool(all(q.values()))
    (HERE / "a229_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    print("j1", res["identity"])
    for z in A28.ROWS:
        rr = res["skip_runs"][z]["b"]
        s = res["skip_rows"][z]
        print(f"{z:9s} b " + " ".join(f"{rr[t]['vmin_a']:.1f}..{rr[t]['vmax_a']:.1f}" for t in A28.TS)
              + f" | mean {s['b']['vmin_mean_a']:.2f}..{s['b']['vmax_mean_a']:.2f} (d0 {s['d0']['vmin_mean_a']:.2f}.."
              f"{s['d0']['vmax_mean_a']:.2f}) | in band {s['b']['in_band']}/4 | Ton max "
              + " ".join(f"{rr[t]['ton_max_end_ns']:.2f}" for t in A28.TS) + f" | q1 {s['b']['q1']} q2 {s['b']['q2']}")
    for r, v in res["part_w"].items():
        m = v["kd"]
        print(f"{r:9s} post {m['post_pk']:6.1f} A (h {v['h_post_pk']:.1f}, g25 {v['d0']['post_pk']:.1f}) whole {m['peak_whole']:.1f} | "
              f"Vo {m['vo_ext_mv']:+.1f} mV | {v['criteria']}")
    print("part I", res["part_i"], "| main", q, "adopt", res["adopt"])


if __name__ == "__main__":
    main()
