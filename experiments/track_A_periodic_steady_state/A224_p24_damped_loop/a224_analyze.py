"""A224 analysis (BOUNDARY Section 2). Pair rows: a223_analyze.one on the kd run and on its reference d0 (A223's g25
record of the same row), plus Vo's maximum before 300 us; e1-e4 per run. Skipping rows: a221_analyze.skip_row (s1,
s2, s3t, z1r, true valleys; the skipping cfgs carry no snapshot, so the circuit parameters that a206 / a207_analyze
read from "snap_circuit" come from A221's record of the same row - same board, plant V7, same r_core - in a copy
under tmp/a224_skip/). Start-up rows (h_, Section 5): start-up and handover peaks, Vo's maximum, late fires to 40 us
after mode P's entry, against A223's g25 record (S75 125 C) or A222's (S75 25 C). j1 from the unit and regression logs and i_u_N0_g25 against A223's record.
  python3 a224_analyze.py -> a224_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A23 = _load("a223_analyze", "A223_p24_cap_on_rising_vin/a223_analyze.py")
A21 = _load("a221_analyze", "A221_p24_core_loss_and_pause/a221_analyze.py")
COS, REF = HERE / "cosim", TA / "A223_p24_cap_on_rising_vin" / "cosim"
NOLOAD_MIN_A, TOL_HAND = -21.2 - 1.0, 2.0


def vo_max_300(path):
    sec = json.loads(Path(path).read_text())["sections"]
    return float(max(q["vo"] for q in sec if q["t_s"] <= 300e-6))


def pair(row, f):
    m, d0 = A23.one(f), A23.one(REF / f"run_{row}_g25.json")
    m["vo_max_300_v"], d0["vo_max_300_v"] = vo_max_300(f), vo_max_300(REF / f"run_{row}_g25.json")
    c = {"e4": bool(m["start_pk"] <= d0["start_pk"] + TOL_HAND and m["hand_pk"] <= d0["hand_pk"] + TOL_HAND
                    and m["vo_max_300_v"] <= 1.05)}
    if row in A23.W_ROWS:
        c["e1"] = bool(m["status"] == "COMPLETED" and m["peak_whole"] <= A23.I_LIM and not m["overlaps"] and not m["shoot_on"]
                       and m["vds_whole"] <= A23.V_LIM and abs(m["vo_last_min_v"] - 1) <= A23.VO_BAND
                       and abs(m["vo_last_max_v"] - 1) <= A23.VO_BAND)
    else:
        ok = m["post_pk"] <= d0["post_pk"] + A23.TOL_A and abs(m["vo_ext_mv"]) <= abs(d0["vo_ext_mv"]) + A23.TOL_MV
        c["e2" if row in A23.LOAD_ROWS else "e3"] = bool(ok and (row in A23.LOAD_ROWS or m["post_pk"] <= A23.I_LIM))
    return {"kd": m, "d0": d0, "d_post_pk_a": m["post_pk"] - d0["post_pk"], "d_vo_ext_mv": m["vo_ext_mv"] - d0["vo_ext_mv"],
            "criteria": c}


H_REF = {"h_S75h": REF / "run_k_S75h_g25.json",
         "h_S75_25": TA / "A222_p24_v7_startup_trim" / "cosim" / "run_s_S75_25_r2.json"}


def startup(path):
    r = json.loads(Path(path).read_text())
    tp, g, sec = r["t_mode_p_s"], r["gate_offs_last"], r["sections"]
    pk = lambda a, b: max((e["i_max_a"] for e in g if a <= e["t_s"] < b), default=None)
    late = [sum(q["late"]) for q in sec if q["t_s"] <= tp + 40e-6]
    return {"t_mode_p_us": tp * 1e6, "start_pk": pk(0.0, tp), "hand_pk": pk(tp, tp + 40e-6), "to_200us_pk": pk(0.0, 200e-6),
            "vo_max_v": float(max(q["vo"] for q in sec if q["t_s"] <= 200e-6)), "late_40us": late[-1] if late else 0,
            "vds_v": max(r["vds_max_v"]), "overlaps": r["overlaps"]}


def h_row(row, f):
    m, d0 = startup(f), startup(H_REF[row])
    return {"kd": m, "d0": d0, "criteria": {"e4": bool(m["start_pk"] <= d0["start_pk"] + TOL_HAND and m["hand_pk"] <= d0["hand_pk"] + TOL_HAND
                                                 and m["vo_max_v"] <= 1.05 and not m["overlaps"])}}


Z_SRC = {"z_N0_10": "z_N0_25_10", "z_N75_10": "z_N75_25_10", "z_N0_0": "z_N0_25_0"}


def with_snap(f):
    """A copy of record f with A221's "snap_circuit" for the same row (the circuit, not the state)."""
    r = json.loads(Path(f).read_text())
    if "snap_circuit" in r:
        return f
    src = TA / "A221_p24_core_loss_and_pause" / "cosim" / f"run_{Z_SRC[Path(f).stem[4:].rsplit('_d', 1)[0]]}.json"
    s21 = json.loads(src.read_text())
    assert s21["cfg"]["circuit"] == r["cfg"]["circuit"] and s21["cfg"]["gate"] == r["cfg"]["gate"]
    r["snap_circuit"] = s21["snap_circuit"]
    out = PROJECT / "tmp" / "a224_skip" / Path(f).name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r))
    return out


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a224_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a224_reg_{k}.log").read_text())) for k in ("quick", "full")}
    f = COS / "run_i_u_N0_g25.json"
    same = None
    if f.exists():
        x, y = json.loads(f.read_text()), json.loads((REF / "run_u_N0_g25.json").read_text())
        same = {k: x.get(k) == y.get(k) for k in A23.ID_KEYS}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "i_u_N0_g25_vs_A223": same,
            "j1": bool(n_pass == 107 and n_fail == 0 and all(reg.values()) and same and all(same.values()))}


def main():
    res = {"identity": identity(), "pairs": {}, "skip": {}, "startup": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        if name.startswith("i_"):
            continue
        row, kd = name.rsplit("_d", 1)
        if name.startswith("h_"):
            res["startup"][name] = h_row(row, f)
            continue
        if name.startswith("z_"):
            v = A21.skip_row(with_snap(f))
            va = [y for p in v["true_valleys_a"].values() for y in p]
            if row == "z_N0_0":
                v["criteria"]["s3t_vs_A221"] = bool(va) and min(va) >= NOLOAD_MIN_A
            res["skip"][name] = v
        else:
            res["pairs"][name] = pair(row, f)
    (HERE / "a224_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    print("j1", res["identity"])
    for n, p in res["pairs"].items():
        m, d0 = p["kd"], p["d0"]
        print(f"{n:13s} whole {d0['peak_whole']:6.1f} -> {m['peak_whole']:6.1f} | post {d0['post_pk']:6.1f} -> {m['post_pk']:6.1f} A | "
              f"Vo {d0['vo_ext_mv']:+6.1f} -> {m['vo_ext_mv']:+6.1f} mV | last {m['vo_last_min_v']:.4f}..{m['vo_last_max_v']:.4f} | "
              f"hand {d0['hand_pk']:.1f} -> {m['hand_pk']:.1f} | late {sum(d0['late_after'])} -> {sum(m['late_after'])} | {p['criteria']}")
    for n, v in res["startup"].items():
        print(f"{n:13s} start {v['d0']['start_pk']:.1f} -> {v['kd']['start_pk']:.1f} hand {v['d0']['hand_pk']:.1f} -> {v['kd']['hand_pk']:.1f} "
              f"Vo max {v['d0']['vo_max_v']:.4f} -> {v['kd']['vo_max_v']:.4f} late {v['d0']['late_40us']} -> {v['kd']['late_40us']} | {v['criteria']}")
    for n, v in res["skip"].items():
        va = [y for p in v["true_valleys_a"].values() for y in p]
        print(f"{n:13s} Vo {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} valleys {min(va):.1f}..{max(va):.1f} resume "
              f"{v['resume_i0_max_a']} | {v['criteria']}")


if __name__ == "__main__":
    main()
