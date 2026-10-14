"""A216 analysis (BOUNDARY Section 2). Per row, A208's numbers (a208_analyze.one: r1 = s1, r2 = s2, the loss books)
and, from the section records (key "tick" = a paused module's sample): rounds run and skipped over the last 20 us,
the pauses after the release, Vo's mean, the low-side turn-off currents per phase against the board's band (s3; no
turn-off in the window passes), the ladder's largest deviation from k Vin / 4. Rows with a second load event: the
peak, Vo's extremes and the late fires after it (s4). i2: the identity row against A215's record.
  python3 a216_analyze.py -> a216_summary.json"""
from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
_s = importlib.util.spec_from_file_location("a208_analyze", TA / "A208_p24_ton_lower_limit" / "a208_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)
COS = HERE / "cosim"
BAND = {"N0": (-20.0, -12.0), "N75": (-20.0, -12.0), "S75": (-22.0, -8.0)}
T_WIN, BAND_ALL = 20e-6, 0.050
ID_REF = TA / "A215_p24_buildable_ton_path" / "cosim" / "run_m16_n_s_p62.json"
CRIT = ("z_", "u_")                                   # the criteria rows; w_, f_ are information, i_ is i2


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, (np.integer, np.bool_)):
        return x.item()
    return x


def one(path):
    name = Path(path).stem[4:]
    m = A8.one(path)
    r = json.loads(Path(path).read_text())
    sec = r["sections"]
    ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec]); tk = np.array([bool(q.get("tick")) for q in sec])
    te = float(ts[-1]); last = ts >= te - T_WIN
    t1 = r["cfg"]["load_step"]["t_us"] * 1e-6
    aft = ts >= t1
    pauses = int(np.sum(tk[1:] & ~tk[:-1] & aft[1:]))
    longest = 0; run = 0
    for x in tk[aft]:
        run = run + 1 if x else 0
        longest = max(longest, run)
    vin = np.array([q["vin_v"] for q in sec]); vc = np.array([q["vcs_v"] for q in sec])
    want = np.outer(vin, [0.75, 0.5, 0.25])
    board = "N0" if "_N0_" in name or name.startswith("i_") else "N75" if "_N75_" in name else "S75"
    lo, hi = BAND[board]
    va = [x for v in m["valley_end_a"].values() for x in v]
    idle = [abs(x) for q, k in zip(sec, tk & last) if k for x in q["i"]]
    out = {k: m.get(k) for k in ("status", "commit", "sources_modified", "wall_s", "shoot_on", "overlaps", "forced", "peak_whole", "vds_whole",
                                 "vo_end_v", "vo_end_min_v", "vo_end_max_v", "vo_after_min_v", "vo_after_max_v", "ton_reg_end_ns",
                                 "valley_end_a", "late_end", "loss_w", "books_w", "p_out_w", "eff_books", "i_out_a")}
    out.update(board=board, band_a=[lo, hi], skip_ticks=r.get("skip_ticks"), rounds_end=int((~tk & last).sum()), ticks_end=int((tk & last).sum()),
               active_share_end=float((~tk & last).sum() / max(1, last.sum())), pauses_after_release=pauses, longest_pause_ticks=int(longest),
               ladder_dev_end_v=float(np.abs(vc[last] - want[last]).max()), idle_current_max_a=max(idle) if idle else None,
               ton_min_ns=r["cfg"].get("ton_min_ns"), skip=r["cfg"].get("skip"), ton_lat=r["cfg"].get("ton_lat"))
    crit = {"s1": m["criteria"]["r1"], "s2": m["criteria"]["r2"],
            "s3": bool((not va or (min(va) >= lo and max(va) <= hi)) and not any(m["late_end"]))}
    ev2 = r["cfg"].get("load_step2")
    if ev2:
        t2 = ev2["t_us"] * 1e-6
        a2 = ts >= t2
        g = [e["i_max_a"] for e in r["gate_offs_last"] if e["t_s"] >= t2]
        k2 = int(np.searchsorted(ts, t2, side="right")) - 1
        out.update(step2_a=ev2["i_a"], post2_pk=max(g) if g else None, vo_after2_min_v=float(vo[a2].min()), vo_after2_max_v=float(vo[a2].max()),
                   late_after2=(np.array(sec[-1]["late"]) - np.array(sec[k2]["late"])).tolist())
        crit["s4"] = bool(abs(out["vo_after2_min_v"] - 1.0) <= BAND_ALL and abs(out["vo_after2_max_v"] - 1.0) <= BAND_ALL)
    out["criteria"] = crit
    return clean(out)


def identity():
    logs = PROJECT / "tmp" / "logs"
    n = re.search(r"ALL PASSED (\d+) tests", (logs / "a216_unit.log").read_text())
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a216_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    out = {"i1": bool(n and all(reg.values())), "unit_tests": int(n.group(1)) if n else None, "regression": reg}
    new = COS / "run_i_n_s_p62.json"
    if new.exists() and ID_REF.exists():
        a, b = json.loads(new.read_text()), json.loads(ID_REF.read_text())
        same = {k: bool(a[k] == b[k]) for k in ("sections", "edges_log", "gate_offs_last", "lowoffs_last", "highoffs_last")}
        out.update(i2=all(same.values()), i2_parts=same, i2_sections=len(a["sections"]), i2_ticks=a.get("skip_ticks"))
    return out


def main():
    res = {"runs": {}, "information": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        if name.startswith("i_"):
            continue
        res["runs" if name.startswith(CRIT) else "information"][name] = one(f)
    res["criteria_identity"] = identity()
    (HERE / "a216_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    f2 = lambda x: "-" if x is None else f"{x:.2f}"
    for grp in ("runs", "information"):
        for n, v in res[grp].items():
            va = {k: [round(x, 1) for x in w] for k, w in v["valley_end_a"].items()}
            print(f"{grp[:3]} {n:20s} {v['status'][:4]} pk {v['peak_whole']:.1f} V_DS {v['vds_whole']:.1f} | Vo end {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} "
                  f"(mean {v['vo_end_v']:.4f}) after {v['vo_after_min_v']:.4f}..{v['vo_after_max_v']:.4f} | rounds {v['rounds_end']} ticks {v['ticks_end']} "
                  f"pauses {v['pauses_after_release']} (longest {v['longest_pause_ticks']}) | valleys {va} late {v['late_end']} | ladder {v['ladder_dev_end_v']:.2f} V "
                  f"| loss {f2(v['loss_w'])} W | {v['criteria']}")
            if "step2_a" in v:
                print(f"      after {v['step2_a']:+g} A: peak {f2(v['post2_pk'])} A, Vo {v['vo_after2_min_v']:.4f}..{v['vo_after2_max_v']:.4f}, late {v['late_after2']}")
    print(res["criteria_identity"])


if __name__ == "__main__":
    main()
