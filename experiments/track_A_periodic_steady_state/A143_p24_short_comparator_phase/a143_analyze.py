"""A143 analysis against BOUNDARY Section 2 -> a143_summary_<stage>.json. Per run: A142's oracle classes, peaks, end
state; the handover window [144, 244] us (peak from the event lists, max |Vo - 1|, rail 1); the 60 us after a step
(phase 2-4 low-offs >= 0 A, time outside 2 %); four modules: C10's rail-1 gate. Usage: a143_analyze.py 1 | 2 K"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
sys.path.insert(0, str(TA / "A142_p24_random_stimulus"))
import a142_oracles as O  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C10 = _load("c10_analyze", TA.parent / "track_C_multi_module" / "C10_seed_before_entry" / "c10_analyze.py")
MK = _load("a143_cfgs", HERE / "make_cfgs.py")
A142C, A141C = TA / "A142_p24_random_stimulus" / "cosim", TA / "A141_p24_floor_late_report" / "cosim"
C12C = TA.parent / "track_C_multi_module" / "C12_floor_late_four_modules" / "cosim"
H0, H1, NOISE_A = 144e-6, 244e-6, 7.0


def stats(path):
    r = O.check(path)
    d = json.loads(Path(path).read_text())
    mods = [d] + d.get("modules_rest", [])
    cls = Counter(e["cls"] for e in r["events"])
    x = {"file": Path(path).name, "status": d["status"], "src_modified": r["src_modified"],
         "overlaps": sum(m["overlaps"] for m in mods), "ff": sum(e["kind"] == "dup_floor_first" for e in r["events"]),
         "new": cls.get("NEW", 0) + cls.get("FF", 0), "classes": dict(cls), "late": r["late"],
         "ipk": max(m["ipk_a"] for m in mods), "peak_post": r["peak_post"], "vo_end": r["vo_end"],
         "ladder_end": r["ladder_dev_end"], "t_lo_timed_us": r["t_lo_timed_us"], "t0_oracle_us": r["t0_us"]}
    hi = [q["i_a"] for m in mods for q in m["highoffs_last"] if H0 <= q["t_s"] < H1]
    sw = [q for q in d["sections"] if H0 <= q["t_s"] < H1]
    x["hand_peak"] = max(hi) if hi else None
    x["hand_dvo_pct"] = max(abs(q["vo"] - 1) for q in sw) * 100
    x["hand_rail1"] = max(q["vin_v"] - q["vcs_v"][0] for q in sw)
    if r["t_dist_us"] is not None:
        ts = r["t_dist_us"] * 1e-6
        post = [q for q in d["sections"] if q["t_s"] >= ts]
        dt = (post[-1]["t_s"] - post[0]["t_s"]) / (len(post) - 1)
        lo = [q["i_a"] for m in mods for q in m["lowoffs_last"] if ts <= q["t_s"] < ts + 60e-6 and q["phase"] != 1]
        x.update(dvo_post_pct=max(abs(q["vo"] - 1) for q in post) * 100,
                 out2_us=sum(abs(q["vo"] - 1) > 0.02 for q in post) * dt * 1e6,
                 lo234_pos=sum(v >= 0 for v in lo), lo234_max=max(lo), lo234_min=min(lo))
    if len(mods) > 1:
        x["rails"] = C10.rails(d)
    return x


def same(a_path, b_path, n=6000):
    a, b = (json.loads(Path(p).read_text()) for p in (a_path, b_path))
    keys = [k for k in a if k.endswith("_last")]
    bad = [k for k in keys if a[k][-n:] != b[k][-n:]] + [k for k in ("sections", "ipk_a", "late_fires") if a[k] != b[k]]
    return {"identical": not bad, "differs": bad, "ipk": [a["ipk_a"], b["ipk_a"]]}


def run_all(paths):
    with Pool(10) as p:
        return {Path(f).stem[4:]: s for f, s in zip(paths, p.map(stats, paths, chunksize=2))}


def ok3(s):
    return (s["status"] == "COMPLETED" and s["overlaps"] == 0 and s["ff"] == 0 and s["new"] == 0
            and abs(s["vo_end"] - 1) <= 0.01 and s["ladder_end"] <= 0.03)


def stage1():
    names = (COS / "ORDER_1.txt").read_text().split()
    st = run_all([COS / f"run_{n}.json" for n in names])
    st |= {f"a142_{r}": s for r, s in run_all([A142C / f"run_{r}.json" for r in MK.G1_ROWS]).items()}
    crit = {}
    for k in MK.KS:
        c1 = {}
        for row in MK.G1_ROWS:
            s = st[f"g1_{row}_k{k}"]
            lim = 200.0 if row.startswith("R_") else 210.0
            c1[row] = s["peak_post"] <= lim and s["lo234_pos"] == 0 and s["out2_us"] <= 5.0
        c2 = {}
        for m in ("070", "100", "130"):
            for row in MK.G3_ROWS:
                s, b = st[f"g3_s{m}_{row}_k{k}"], st[f"g3_s{m}_{row}_k1024"]
                c2[f"s{m}_{row}"] = (s["ipk"] <= b["ipk"] + NOISE_A and s["hand_peak"] <= b["hand_peak"] + NOISE_A
                                     and s["late"] <= b["late"] + 5 and s["hand_dvo_pct"] <= b["hand_dvo_pct"] + 0.2
                                     and s["hand_rail1"] <= b["hand_rail1"] + 0.3)
        c3 = {n: ok3(st[n]) for n in names if n.startswith(("g1_", "g3_")) and (n.endswith(f"_k{k}") or n.endswith("_k1024"))}
        crit[k] = {"1": all(c1.values()), "2": all(c2.values()), "3": all(c3.values()),
                   "fails": [x for d_ in (c1, c2, c3) for x, v in d_.items() if not v]}
    ident = same(COS / "run_g3_s100_n0_k1024.json", A141C / "run_I1_s100_n0.json")
    choice = next((k for k in MK.KS if crit[k]["1"] and crit[k]["2"] and crit[k]["3"]), None)
    out = {"stats": st, "criteria": crit, "identity_n0": ident, "chosen_K": choice}
    (HERE / "a143_summary_1.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"identity n0 {ident['identical']} {ident['differs']}; chosen K {choice}")
    for k in MK.KS:
        print(f"K {k}: c1 {crit[k]['1']} c2 {crit[k]['2']} c3 {crit[k]['3']} fails {crit[k]['fails'][:6]}")
    for row in MK.G1_ROWS:
        print(f"g1 {row:16s} peak 1024/4/16/64 " + " ".join(f"{st[n]['peak_post']:5.0f}" for n in
              [f"a142_{row}"] + [f"g1_{row}_k{k}" for k in MK.KS]) + "  lo234>=0 " +
              " ".join(str(st[n]["lo234_pos"]) for n in [f"a142_{row}"] + [f"g1_{row}_k{k}" for k in MK.KS]))
    for t in ("146", "160"):
        for dv in ("4.8", "6.4"):
            print(f"g2 t{t} +{dv} V peak 1024/4/16/64 " + " ".join(
                f"{st[f'g2_t{t}_dv{dv}_k{k}']['peak_post']:5.0f}" for k in (1024,) + MK.KS))


def stage2(k):
    names = (COS / "ORDER_2.txt").read_text().split()
    st = run_all([COS / f"run_{n}.json" for n in names])
    st |= {f"c12_{r}": s for r, s in run_all([C12C / f"run_{r}.json" for r in MK.G5_ROWS]).items()}
    c5, c6 = {}, {}
    for m, row in MK.G4:
        n = f"g4_s{round(m * 100):03d}_{row}"
        s, b = st[f"{n}_k{k}"], st[f"{n}_k1024"]
        c5[n] = (s["peak_post"] <= b["peak_post"] + NOISE_A and (s["peak_post"] <= 200.0 or b["peak_post"] > 200.0)
                 and s["late"] <= b["late"] + 5)
    for row in MK.G5_ROWS:
        s, b = st[f"g5_{row}_k{k}"], st[f"c12_{row}"]
        pk = (s["peak_post"] or s["ipk"]), (b["peak_post"] or b["ipk"])
        c6[row] = (pk[0] <= pk[1] + NOISE_A and s["late"] <= b["late"] + 5 and s["ff"] == 0
                   and all(q["max_v"] <= C10.RAIL_MAX and q["hi_us"] <= C10.RAIL_HI_US for q in s["rails"]))
    c3 = {n: ok3(st[n]) for n in names}
    ident = same(COS / "run_g4_s100_l_p48_1us_k1024.json", A141C / "run_F_s100_l_p48_1us.json")
    crit = {"3": all(c3.values()), "4": ident["identical"], "5": all(c5.values()), "6": all(c6.values()),
            "fails": [x for d_ in (c3, c5, c6) for x, v in d_.items() if not v]}
    (HERE / f"a143_summary_2_k{k}.json").write_text(json.dumps({"stats": st, "criteria": crit, "identity_lp48": ident},
                                                                indent=1) + "\n")
    print(f"K {k}: c3 {crit['3']} c4 {crit['4']} {ident['differs']} c5 {crit['5']} c6 {crit['6']} fails {crit['fails'][:8]}")
    d5 = [st[f"g4_s{round(m * 100):03d}_{r}_k{k}"]["peak_post"] - st[f"g4_s{round(m * 100):03d}_{r}_k1024"]["peak_post"]
          for m, r in MK.G4]
    print(f"g4 peak K - 1024: min {min(d5):+.1f} max {max(d5):+.1f} A; max peak at K "
          f"{max(st[f'g4_s{round(m * 100):03d}_{r}_k{k}']['peak_post'] for m, r in MK.G4):.1f} A")
    for row in MK.G5_ROWS:
        s, b = st[f"g5_{row}_k{k}"], st[f"c12_{row}"]
        print(f"g5 {row:10s} peak {s['peak_post'] or s['ipk']:6.1f} (C12 {b['peak_post'] or b['ipk']:6.1f}) late {s['late']} "
              f"({b['late']}) ff {s['ff']} rail1 max {max(q['max_v'] for q in s['rails']):.2f} V")


if __name__ == "__main__":
    if sys.argv[1] == "1":
        stage1()
    else:
        stage2(int(sys.argv[2]))
