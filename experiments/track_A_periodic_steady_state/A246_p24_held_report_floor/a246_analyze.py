"""A246 analysis (BOUNDARY Section 2), arm h against its registered references and against A244's run_w_ (the final
configuration; rev_n 16 never acts on those rows). Stage 1 = A240's 18 rows (a240_analyze.one, A244's g1-g4), stage 2 =
A236's 25 rows and A237's 3 (a236_analyze.row, A244's g5-g7). g8: a row where the floor never acts equals A244's record
bit for bit; the floor acts where a learned report with the low-side current positive on phases 2-4, 20 us or more
after mode P's entry (the holds act from then), is followed by a longer delay on that phase (by > 0.01 ns, to >= 8 ns:
held and flat reports leave the delay, and shorter delays pair ambiguously with the low-side edges). g9: no row worse than A244's record. g10: CTRL_ROW at
k 0 / 2 / 4 of T / 6 within A240's q4 in arm h; c1 (A243's): a g9 row's worst over k 0 / 2 / 4 in arm h against arm w's.
1 MHz rows are excepted from g1 / g2. g0: unit tests and regression logs (tmp/logs/a246_*.log). Post hoc, not criteria:
divergence() (each row that leaves A244's record: is its first change the floor's lift?) and g6_inherited (g6 misses on
rows equal to A244's record).
  python3 a246_analyze.py -> a246_summary.json"""
from __future__ import annotations

import bisect
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"
W = TA / "A244_p24_holds_after_handover" / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a246_make_cfgs", HERE / "make_cfgs.py")
A44 = _load("a244_analyze", TA / "A244_p24_holds_after_handover" / "a244_analyze.py")
A40, A36, delay_min, held = A44.A40, A44.A36, A44.delay_min, A44.held
PK_TOL, VO_TOL_MV, WIDE, UNIT_N, LEAD = A44.PK_TOL, A44.VO_TOL_MV, A44.WIDE, 137, 8.0
KEYS = ("sections", "highoffs_last", "lowoffs_last", "turnons_last", "late_fires", "overlaps", "ipk_a")


def same(fa, fb):
    a, b = json.loads(Path(fa).read_text()), json.loads(Path(fb).read_text())
    return all(a.get(k) == b.get(k) for k in KEYS) and all(
        all(x.get(k) == y.get(k) for k in KEYS) for x, y in zip(a.get("modules_rest", []), b.get("modules_rest", [])))


def _seq(md, ph):
    """[(delay ns, turn-on)] of a phase's learned turn-ons, each paired with the nearest low-side turn-off (+ LEAD)."""
    lo = sorted(x["t_s"] for x in md["lowoffs_last"] if x["phase"] == ph)
    seq = []
    for x in md["turnons_last"]:
        if x["phase"] != ph or x["how"] != 0 or not lo:
            continue
        k = bisect.bisect_left(lo, x["t_s"])
        j = min((j for j in (k - 1, k) if 0 <= j < len(lo)), key=lambda j: abs(lo[j] - x["t_s"]))
        seq.append(((x["t_s"] - lo[j]) * 1e9 + LEAD, x))
    return seq


def floor_acts(f):
    """Times (us) of the floor's acts (module docstring)."""
    d = json.loads(Path(f).read_text())
    out, t_on = [], d["t_mode_p_s"] + 20e-6
    for md in [d] + d.get("modules_rest", []):
        for ph in (2, 3, 4):
            seq = _seq(md, ph)
            out += [round(x["t_s"] * 1e6, 2) for (a, x), (b, _) in zip(seq, seq[1:])
                    if "early" in x and x.get("lo_pos") and x["t_s"] > t_on and b - a > 0.01 and b >= 8.0]
    return sorted(out)


def divergence(fa, fb):
    """Post hoc: the earliest turn-on where record fa leaves fb, over all modules. The floor explains it when that is a
    later turn-on of phases 2-4 whose delay is the floor: the smallest delay of the module's other phases 2-4 at their
    first learned turn-on after this phase's previous one (dt_pred when this phase's report came), minus MC.BAND."""
    a, b = json.loads(Path(fa).read_text()), json.loads(Path(fb).read_text())
    best = None
    for m, (ma, mb) in enumerate(zip([a] + a.get("modules_rest", []), [b] + b.get("modules_rest", []))):
        n = next((i for i, (x, y) in enumerate(zip(ma["turnons_last"], mb["turnons_last"])) if x != y), None)
        if n is not None and (best is None or ma["turnons_last"][n]["t_s"] < best[2]["t_s"]):
            best = (m, ma, ma["turnons_last"][n], mb["turnons_last"][n])
    if best is None:
        return None
    m, md, x, y = best
    out = {"module": m, "t_us": round(x["t_s"] * 1e6, 3), "phase": x["phase"], "later_ns": round((x["t_s"] - y["t_s"]) * 1e9, 3)}
    if x["phase"] in (2, 3, 4) and x["how"] == 0:
        seq = _seq(md, x["phase"])
        i = next(i for i, (_, z) in enumerate(seq) if z is x)
        prev = seq[i - 1][1]["t_s"] if i else 0.0
        oth = [next((dl for dl, z in _seq(md, ph) if z["t_s"] > prev), None) for ph in (2, 3, 4) if ph != x["phase"]]
        floor = min(o for o in oth if o is not None) - MC.BAND
        out |= {"delay_ns": round(seq[i][0], 3), "floor_ns": round(floor, 3)}
    out["floor_explains"] = bool(out["later_ns"] > 0 and "floor_ns" in out and abs(out["delay_ns"] - out["floor_ns"]) <= 0.05)
    return out


def one1(f, row):
    b, fk = row.split("_")[1], float(row.split("_")[2][:-1])
    v, q = A40.one(f, b, fk)
    v["delay_min_ns"] = delay_min(f, A40.T0)
    return {k: v[k] for k in v if k != "reapp"}, q


def stage1():
    rows = {}
    for row in MC.STAGE1:
        f = COS / f"run_h_{row}.json"
        if not f.exists():
            rows[row] = None; continue
        (h, q), (w, _), (rv, _) = one1(f, row), one1(W / f"run_w_{row}.json", row), one1(A44.MC.ref(row), row)
        acts = floor_acts(f)
        c = {"g1": q["q1"], "g2": q["q4"], "g3": bool(q["q2"] and q["q5"]),
             "g4": bool(h["vo_min_v"] >= rv["vo_min_v"] - VO_TOL_MV * 1e-3),
             "g8": True if acts else same(f, W / f"run_w_{row}.json"),
             "g9": bool(h["peak_after_t0"] <= w["peak_after_t0"] + PK_TOL and h["vo_min_v"] >= w["vo_min_v"] - 1e-3)}
        if row.endswith("_1000k"):
            c["g1_g2_excepted"] = True
        rows[row] = {"h": h, "w": w, "ref": rv, "acts": len(acts), "first_act_us": acts[0] if acts else None,
                     "equal_to_a244": same(f, W / f"run_w_{row}.json"), "criteria": c}
    return rows


def stage2():
    rows = {}
    for name in MC.STAGE2:
        f = COS / f"run_h_{name}.json"
        if not f.exists():
            rows[name] = None; continue
        h, w, ref = A36.row(name, f), A36.row(name, W / f"run_w_{name}.json"), A36.row(name, A44.MC.ref(name))
        acts = floor_acts(f)
        c = {"g8": True if acts else same(f, W / f"run_w_{name}.json")}
        if name in A36.SKIP:
            c["g7"] = bool(h["q1_run"] and abs(h["vmin_a"] - ref["vmin_a"]) <= 1.0 and abs(h["vmax_a"] - ref["vmax_a"]) <= 1.0)
            c["g9"] = bool(abs(h["vmin_a"] - w["vmin_a"]) <= 1.0 and abs(h["vmax_a"] - w["vmax_a"]) <= 1.0)
        else:
            i_lim = ref["peak_whole"] + 2.0 if name in A36.ITEM2 else A36.A34.I_LIM
            c["g5"] = bool(A36.A34_limits(h, i_lim) and (h["n_mod"] == 1 or h["f3"]))
            tol = 10.0 if name in WIDE else PK_TOL
            c["g6"] = bool(h["post_pk"] <= ref["post_pk"] + tol and h["new_after"] <= ref["new_after"]
                           and (name in WIDE or abs(h["vo_ext_mv"]) <= abs(ref["vo_ext_mv"]) + 1.0))
            c["g9"] = bool(h["post_pk"] <= w["post_pk"] + tol and h["new_after"] <= w["new_after"]
                           and (name in WIDE or abs(h["vo_ext_mv"]) <= abs(w["vo_ext_mv"]) + 1.0))
        rows[name] = {"h": h, "w": w, "ref_record": str(A44.MC.ref(name).relative_to(TA)), "acts": len(acts),
                      "first_act_us": acts[0] if acts else None, "equal_to_a244": same(f, W / f"run_w_{name}.json"),
                      "criteria": c}
    return rows


def positions(row):
    """Stage 1 row at k 0 / 2 / 4 of T / 6 in arm h and arm w (k 0: run_h_ and A244's run_w_), or None."""
    fs = {"h": {0: COS / f"run_h_{row}.json"} | {k: COS / f"run_ch_{row}_k{k}.json" for k in MC.KS},
          "w": {0: W / f"run_w_{row}.json"} | {k: COS / f"run_cw_{row}_k{k}.json" for k in MC.KS}}
    if not all(f.exists() for arm in fs.values() for f in arm.values()):
        return None
    res = {arm: {k: one1(f, row) for k, f in arm_fs.items()} for arm, arm_fs in fs.items()}
    return {arm: {k: {"peak_after_t0": v["peak_after_t0"], "q4": q["q4"], "vo_min_v": v["vo_min_v"]}
                  for k, (v, q) in r.items()} for arm, r in res.items()}


def control():
    out = positions(MC.CTRL_ROW)
    return out and {"positions": out, "criteria": {"g10": all(x["q4"] for x in out["h"].values())}}


def c1(rows):
    """A243's c1 on the g9 rows: arm h's worst over k 0 / 2 / 4 against arm w's (peak + PK_TOL, Vo minimum - 1 mV)."""
    out = {}
    for row in rows:
        p = positions(row)
        if p is None:
            out[row] = None; continue
        pk = {a: max(x["peak_after_t0"] for x in p[a].values()) for a in p}
        vo = {a: min(x["vo_min_v"] for x in p[a].values()) for a in p}
        out[row] = {"positions": p, "worst_peak": pk, "worst_vo_min": vo,
                    "c1": bool(pk["h"] <= pk["w"] + PK_TOL and vo["h"] >= vo["w"] - 1e-3)}
    return out


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a246_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a246_reg_{k}.log").read_text())) for k in ("quick", "full")}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg,
            "g0": bool(n_pass == UNIT_N and n_fail == 0 and all(reg.values()))}


def main():
    res = {"identity": identity(), "stage1": stage1(), "stage2": stage2(), "control": control()}
    main_c = {"g0": res["identity"]["g0"]}
    for st, keys in (("stage1", ("g1", "g2", "g3", "g4", "g8", "g9")), ("stage2", ("g5", "g6", "g7", "g8", "g9"))):
        done = [x for x in res[st].values() if x]
        for k in keys:
            have = [x["criteria"][k] for x in done if k in x["criteria"]
                    and not (k in ("g1", "g2") and x["criteria"].get("g1_g2_excepted"))]
            if have:
                main_c[k] = all(have) and main_c.get(k, True)
        res[f"{st}_complete"] = len(done) == len(res[st])
    if res["control"]:
        main_c["g10"] = res["control"]["criteria"]["g10"]
    g9 = [r for st in ("stage1", "stage2") for r, x in res[st].items() if x and not x["criteria"].get("g9", True)]
    res["c1"] = c1([r for r in g9 if r in MC.STAGE1])
    if res["c1"] and all(res["c1"].values()):
        main_c["c1"] = all(x["c1"] for x in res["c1"].values())
    res["criteria_main"] = main_c
    res["post_hoc"] = {
        "divergence": {r: divergence(COS / f"run_h_{r}.json", W / f"run_w_{r}.json")
                       for st in ("stage1", "stage2") for r, x in res[st].items() if x and not x["equal_to_a244"]},
        "g6_inherited": [r for r, x in res["stage2"].items() if x and not x["criteria"].get("g6", True) and x["equal_to_a244"]]}
    (HERE / "a246_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["stage1"].items():
        if x:
            h, w = x["h"], x["w"]
            print(f"{row:14s} pk {h['peak_after_t0']:6.1f} (A244 {w['peak_after_t0']:6.1f}) Vo min {h['vo_min_v']:.4f} "
                  f"({w['vo_min_v']:.4f}) acts {x['acts']:4d} | " + " ".join(k for k, ok in x["criteria"].items() if not ok))
    for n, x in res["stage2"].items():
        if x:
            h, w = x["h"], x["w"]
            pk = (h.get("post_pk"), w.get("post_pk"))
            print(f"{n:14s} post {pk[0] if pk[0] is None else round(pk[0], 1)} (A244 {pk[1] if pk[1] is None else round(pk[1], 1)}) "
                  f"acts {x['acts']:4d} | " + " ".join(k for k, ok in x["criteria"].items() if not ok))
    print("control", res["control"] and res["control"]["positions"])
    for r, x in res["c1"].items():
        print("c1", r, x and {k: x[k] for k in ("worst_peak", "worst_vo_min", "c1")})
    for r, x in res["post_hoc"]["divergence"].items():
        print("div", r, x)
    print("g6 inherited", res["post_hoc"]["g6_inherited"])
    print("main", main_c)


if __name__ == "__main__":
    main()
