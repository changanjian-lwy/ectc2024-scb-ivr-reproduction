"""A149 D63 stage: the law family (gr, gt, rel_k, kv) on D63 with A148's V_DS block and A149's SH_k block, the grid and
criterion 2 (BOUNDARY sec. 2).
Family, on top of the frozen controller (scb_vff: A128 gate, A136 relative cap, RTL integers; A148's Vff):
- lo_add = (gr tlp (rail - rss) + gt (ton_1 - tlp) rail) / Vo on phase 1's timed edge (A148's law with split gains);
- rel_eff = clamp(rel - (rel_k max(vpred - lp20, 0)) >> 16, 64, 1023) for phase 1's relative cap (rail - rss = vpred -
  lp20 in Q8 codes);
- phases 2-4 Ton x (1 + kv lo_add_prev / T0), T0 = 504 ns.
Rows: l_p48_1us, l_p48_5us, s_p62, l_m48_1us at L0; l_p48_1us at L x 0.7 / 1.3 (A148's tables), 800 periods from A135's
warm state. SH from the block at 50 pH / 72 A/ns (rec "sh") and 100 pH / 72 A/ns (same formula).
Usage: a149_d63.py [--jobs 10]. Writes a149_grid.json; prints <= 15 lines."""
from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A148_rl_zvs_line_step"))
import a148_d63 as E  # noqa: E402

from scb_ivr.p24_valley_map import DIVERGED_A  # noqa: E402

TABLES = json.loads((HERE / "a149_sh_table.json").read_text())
T0 = 504e-9
N = 800
ROWS = (("l_p48_1us", 1.0), ("l_p48_5us", 1.0), ("s_p62", 1.0), ("l_m48_1us", 1.0), ("l_p48_1us", 0.7), ("l_p48_1us", 1.3))
GRID = {"gr": (0, .25, .5, .625, .75, .875, 1.0, 1.125, 1.25), "gt": (0, .25, .5, .75, 1.0, 1.25),
        "rel_k": (-68, -34, 0, 34, 68), "kv": (0, .25, .5, .75, 1.0)}
SH_LIM, PK_LIM, VO_TOL, T_VO, ROB = 40.5, 200.0, 5e-3, 27.6e-6, 1.25


def table(name):
    t = TABLES[name]
    return tuple(t["grid"]), tuple(t["x"])


def design(m):
    return replace(E.design(m=m), sh=table("L50_e72"))


class Vff(E.Vff):
    """A148's scb_vff model with the transient relative cap rel_eff (rel_k)."""

    def __init__(self, rel_k=0):
        super().__init__()
        self.rel_k = rel_k

    def __call__(self, vin, ton_s):
        if self.s is not None and self.rel_k:
            v8 = round(vin / E.VFF["vin_lsb_v"]) << 8
            lp20n = self.s["lp20"] + ((v8 - self.s["lp20"]) >> E.VFF["sh20"])
            dq = 2 * v8 - (self.s["vprev"] << 8) - lp20n           # rail - rss of this sample, Q8 codes
            base, self.rel = self.rel, min(max(E.REL - ((self.rel_k * max(dq, 0)) >> 16), 64), 1023)
            try:
                return super().__call__(vin, ton_s)
            finally:
                self.rel = base
        return super().__call__(vin, ton_s)


def run(d, warm, row, th, n=N):
    """One row from the warm state with th = (gr, gt, rel_k, kv). Returns the records."""
    gr, gt, rel_k, kv = th
    vm, s, vff0, ton = copy.deepcopy(warm)
    vff = Vff(rel_k)
    for k, v in vff0.__dict__.items():
        if k != "rel_k":
            setattr(vff, k, v)
    recs, prev = [], 0.0
    while len(recs) < n:
        vin, i_step = E.stim(row, s["t"])
        sc, cap = vff(vin, ton)
        tref, re, rs = (vff.tlp >> 8) * E.LSB, vff.volts(vff.rail), vff.volts(vff.rss)
        add = (lambda t1: (gr * tref * (re - rs) + gt * (t1 - tref) * re) / E.VO) if (gr or gt) else None
        if kv:
            f = 1.0 + kv * prev / T0
            sc = [sc[0]] + [x * f for x in sc[1:]]
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap, lo_add=add)
        ton = r["ton"]
        prev = r["lo_add"] = add(r["tons"][0]) if add else 0.0
        recs.append(r)
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"]):
            r["diverged"] = True
            break
    return recs


def metrics(recs):
    a = [r for r in recs if r["t"] >= E.T_STEP]
    g, x = table("L100_e72")
    vo = np.array([r["vo"] for r in a])
    t = np.array([r["t"] for r in a]) - E.T_STEP
    late_vo = np.abs(vo[t >= T_VO] - E.VO)
    bad = np.nonzero(np.abs(vo - E.VO) > 0.01)[0]
    return {"sh50": float(max(max(r["sh"]) for r in a)),
            "sh100": float(max(r["rails"][k - 1] + r["rails"][k] + np.interp(r["von"][k - 1], g, x) for r in a for k in (1, 2, 3))),
            "von": [float(max(r["von"][k] for r in a)) for k in range(4)],
            "peak": float(max(max(r["peak"]) for r in a)), "late": int(sum(sum(r["late"]) for r in a)),
            "rail1": float(max(r["rails"][0] for r in a)), "vo_mv": [float(1e3 * (vo.min() - E.VO)), float(1e3 * (vo.max() - E.VO))],
            "vo27_mv": float(1e3 * late_vo.max()) if len(late_vo) else 1e9,
            "back_us": float(t[bad[-1]] * 1e6) if len(bad) else 0.0, "diverged": bool(recs[-1].get("diverged"))}


_W = {}


def _init():
    for m in (1.0, 0.7, 1.3):
        d = design(m)
        _W[m] = (d, E.warm(d))


def evaluate(th):
    return {f"{row}@{m}": metrics(run(_W[m][0], _W[m][1], row, th)) for row, m in ROWS}


def robust(th):
    gr, gt, rel_k, kv = th
    t2 = (gr * ROB, gt * ROB, rel_k, kv * ROB)
    return {row: metrics(run(_W[1.0][0], _W[1.0][1], row, t2))["diverged"] for row in ("l_p48_1us", "l_p48_5us")}


def check(res, ref):
    """Criterion 2's parts (robustness added later)."""
    up = ("l_p48_1us@1.0", "l_p48_5us@1.0")
    return {"sh": max(res[k]["sh50"] for k in up) <= SH_LIM,
            "peak": all(v["peak"] <= PK_LIM and not v["diverged"] for v in res.values()),
            "late": all(res[k]["late"] <= ref[k]["late"] for k in res),
            "vo": res["l_p48_1us@1.0"]["vo27_mv"] <= 1e3 * VO_TOL}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    pts = list(itertools.product(*GRID.values()))
    with Pool(a.jobs, initializer=_init) as pool:
        res = pool.map(evaluate, pts, chunksize=4)
        ref = res[pts.index((0, 0, 0, 0))]
        chk = [check(r, ref) for r in res]
        cand = [i for i, c in enumerate(chk) if all(c.values())]
        rob = dict(zip(cand, pool.map(robust, [pts[i] for i in cand])))
    for i, r in rob.items():
        chk[i]["robust"] = not any(r.values())
    passing = [i for i in cand if chk[i]["robust"]]
    sh = [max(r[k]["sh50"] for k in ("l_p48_1us@1.0", "l_p48_5us@1.0")) for r in res]
    vo27 = [r["l_p48_1us@1.0"]["vo27_mv"] for r in res]
    ok_pk = [i for i, c in enumerate(chk) if c["peak"] and c["late"]]
    front = [i for i in ok_pk if not any(sh[j] <= sh[i] and vo27[j] <= vo27[i] and (sh[j], vo27[j]) != (sh[i], vo27[i]) for j in ok_pk)]
    front.sort(key=lambda i: sh[i])
    shok = [i for i, c in enumerate(chk) if c["sh"]]
    fail = {k: sum(not chk[i][k] for i in shok) for k in ("peak", "late", "vo")}
    out = {"grid": GRID, "points": [{"th": list(p), "rows": r, "check": c} for p, r, c in zip(pts, res, chk)],
           "criterion_2": {"pass": bool(passing), "passing": [list(pts[i]) for i in passing], "sh_ok": len(shok),
                           "sh_ok_fail_counts": fail, "front": [list(pts[i]) for i in front]}}
    (HERE / "a149_grid.json").write_text(json.dumps(out) + "\n")
    for th in ((0, 0, 0, 0), (0.75, 0.75, 0, 0), (1.0, 1.0, 0, 0)):
        r = res[pts.index(th)]["l_p48_1us@1.0"]
        print(f"{th}: SH50 {r['sh50']:.1f} SH100 {r['sh100']:.1f} von1 {r['von'][0]:.1f} peak {r['peak']:.0f} vo27 {r['vo27_mv']:.1f} mV")
    print(f"points {len(pts)}; SH50 <= {SH_LIM} on both rising rows: {len(shok)}; of those failing peak/late/vo: {fail}")
    print(f"criterion 2 candidates before robustness {len(cand)}, after {len(passing)} ->", "PASS" if passing else "FAIL")
    print("Pareto front (peak + late ok) th: SH50 / vo27 mV / peak max:")
    for i in front[:9]:
        print(f"  {tuple(pts[i])}: {sh[i]:.1f} / {vo27[i]:.1f} / {max(v['peak'] for v in res[i].values()):.0f}")


if __name__ == "__main__":
    main()
