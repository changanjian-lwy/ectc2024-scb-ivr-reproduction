"""A228 analysis (BOUNDARY Section 2).
Part S: every skipping run (t1-t3 here, t0 from A224 / A226 / A227 / here) through a221_analyze.skip_row on a copy that
carries A221's circuit snapshot of the same row (a224_analyze.with_snap's reason) - q1 per run, q2 per row and arm
against d0. Part R: a224_analyze.pair / h_row on arm h (and A227's three w records) - q3; arm h against A224's k
record of the row bit for bit (information).
  python3 a228_analyze.py -> a228_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A24 = _load("a224_analyze", "A224_p24_damped_loop/a224_analyze.py")
A23, A21 = A24.A23, A24.A21
COS = HERE / "cosim"
C24, C26, C27 = (TA / d / "cosim" for d in ("A224_p24_damped_loop", "A226_p24_noload_valley_reference", "A227_p24_kd_held_at_the_limit"))
ROWS, ARMS, TS = ("z_N0_10", "z_N75_10", "z_N0_0"), ("d0", "k", "h"), ("t0", "t1", "t2", "t3")
T0 = {("z_N0_0", "d0"): C26 / "run_z_N0_0_d0.json", ("z_N0_10", "d0"): C27 / "run_z_N0_10_d0.json",
      ("z_N75_10", "d0"): COS / "run_z_N75_10_t0_d0.json"}
T0.update({(z, "k"): C24 / f"run_{z}_d355.json" for z in ROWS})
T0.update({(z, "h"): C27 / f"run_{z}_h.json" for z in ROWS})
TOL_A = 1.0                                             # q2: one-sided, on the mean over the four instants
R_ROWS = ("w20_N0", "w30_S75h", "u_N0", "k_N0", "l_N0_p48", "l_N0_m80", "k_S75h")
W27 = ("w0_N0", "w5_N0", "w5_N75")


def path(z, t, a):
    return T0[(z, a)] if t == "t0" else COS / f"run_{z}_{t}_{a}.json"


def with_snap(f, z):
    r = json.loads(Path(f).read_text())
    src = json.loads((TA / "A221_p24_core_loss_and_pause" / "cosim" / f"run_{A24.Z_SRC[z]}.json").read_text())
    assert src["cfg"]["circuit"] == r["cfg"]["circuit"] and src["cfg"]["gate"] == r["cfg"]["gate"]
    r["snap_circuit"] = src["snap_circuit"]
    out = PROJECT / "tmp" / "a228_skip" / f"{Path(f).parent.parent.name}_{Path(f).name}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r))
    return out


def skip_run(z, t, a):
    f = path(z, t, a)
    v = A21.skip_row(with_snap(f, z))
    va = [y for p in v["true_valleys_a"].values() for y in p]
    c = v["criteria"]
    ok = bool(v["status"] == "COMPLETED" and c["s1"] and c["s2"] and not any(v["late_end"]) and va
              and (z == "z_N0_0" or c["z1r"]))
    lo, hi = v["band_a"]
    return {"record": str(f.relative_to(TA)), "load_step_us": json.loads(f.read_text())["cfg"]["load_step"]["t_us"],
            "vmin_a": min(va) if va else None, "vmax_a": max(va) if va else None, "window_us": v["true_valleys_window_us"],
            "vo_end_v": [v["vo_end_min_v"], v["vo_end_max_v"]], "resume_i0_max_a": v["resume_i0_max_a"],
            "in_band": bool(va and min(va) >= lo and max(va) <= hi), "s": c, "q1_run": ok}


def mean(x):
    return sum(x) / len(x)


def part_s():
    runs = {z: {a: {t: skip_run(z, t, a) for t in TS} for a in ARMS} for z in ROWS}
    rows = {}
    for z in ROWS:
        st = {}
        for a in ARMS:
            rr = list(runs[z][a].values())
            st[a] = {"vmin_mean_a": mean([r["vmin_a"] for r in rr]), "vmax_mean_a": mean([r["vmax_a"] for r in rr]),
                     "vmin_range_a": [min(r["vmin_a"] for r in rr), max(r["vmin_a"] for r in rr)],
                     "vmax_range_a": [min(r["vmax_a"] for r in rr), max(r["vmax_a"] for r in rr)],
                     "q1_fails": sum(not r["q1_run"] for r in rr), "in_band": sum(r["in_band"] for r in rr)}
        for a in ("k", "h"):
            st[a]["q1"] = bool(st[a]["q1_fails"] <= st["d0"]["q1_fails"])
            st[a]["q2"] = bool(st[a]["vmin_mean_a"] >= st["d0"]["vmin_mean_a"] - TOL_A
                               and st[a]["vmax_mean_a"] <= st["d0"]["vmax_mean_a"] + TOL_A)
        rows[z] = st
    return runs, rows


def same(f, g):
    x, y = json.loads(Path(f).read_text()), json.loads(Path(g).read_text())
    return all(x.get(k) == y.get(k) for k in A23.ID_KEYS)


def part_r():
    out = {}
    for r in R_ROWS:
        f = COS / f"run_{r}_h.json"
        out[r] = A24.pair(r, f)
        out[r]["same_as_k"] = same(f, C24 / f"run_{r}_d355.json")
    f = COS / "run_h_S75_25_h.json"
    out["h_S75_25"] = A24.h_row("h_S75_25", f)
    out["h_S75_25"]["same_as_k"] = same(f, C24 / "run_h_S75_25_d355.json")
    for r in W27:
        out[r] = A24.pair(r, C27 / f"run_{r}_h.json")
    for v in out.values():
        v["q3"] = bool(all(v["criteria"].values()))
    return out


def main():
    runs, rows = part_s()
    r = part_r()
    q = {a: {"q1": all(rows[z][a]["q1"] for z in ROWS), "q2": all(rows[z][a]["q2"] for z in ROWS)} for a in ("k", "h")}
    q["h"]["q3"] = all(v["q3"] for v in r.values())
    adopt = "h" if all(q["h"].values()) else "k" if all(q["k"].values()) else None
    res = {"skip_runs": runs, "skip_rows": rows, "part_r": r, "arms": q, "adopt": adopt}
    (HERE / "a228_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    for z in ROWS:
        for a in ARMS:
            s = rows[z][a]
            mm = " ".join(f"{runs[z][a][t]['vmin_a']:.1f}..{runs[z][a][t]['vmax_a']:.1f}" for t in TS)
            print(f"{z:9s} {a:2s} {mm} | mean {s['vmin_mean_a']:.2f}..{s['vmax_mean_a']:.2f} | q1 fails {s['q1_fails']} "
                  f"in band {s['in_band']}/4 | {({k: s[k] for k in ('q1', 'q2') if k in s})}")
    for n, v in r.items():
        m = v["kd"]
        pk = f"post {m['post_pk']:.1f}" if "post_pk" in m else f"hand {m['hand_pk']:.1f}"
        print(f"{n:9s} {pk} A | {v['criteria']} | same as k {v.get('same_as_k')}")
    print("arms", q, "adopt", adopt)


if __name__ == "__main__":
    main()
