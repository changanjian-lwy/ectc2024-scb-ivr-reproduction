"""A182 analysis: BOUNDARY criteria from runs/*.json (+ A180's base runs) -> a182_summary.json and a table on stdout.

Run from the project root: python3 extensions/lscb_ladder/experiments/A182_lscb_detector_clamp/a182_analyze.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A180 = HERE.parent / "A180_lscb_ladder_open_loop" / "runs"
VTH = (0.75, 1.5)


def load(folder, pattern="*.json"):
    out = {}
    for f in sorted(folder.glob(pattern)):
        r = json.loads(f.read_text())
        r.pop("trace", None)
        out[f.stem] = r
    return out


def tag(vth, td):
    return f"v{int(round(vth * 100)):03d}_t{int(round(td * 1e9)):04d}"


def row(r):
    po = r["post"]
    return dict(rail1_exc=po["rail1_exc"], peak=max(po["il_peak"]), clamp_peak=max(po["clamp_peak_a"]),
                ls_peak=max(po["ls_peak_a"]), clamp_energy_uj=po["clamp_energy_uj"], win=r.get("win"),
                t_det_us=(r["t_det"] - r["params"]["t_step"]) * 1e6 if r.get("t_det") else None)


def criteria(R, B):
    out = {}
    pre = {f"{n}/{v}": d["pre_dev_max"] for n, r in R.items() if n.startswith("nowin_")
           for v, d in r["detect"].items()}
    ok1 = {v: all(x < v for k, x in pre.items() if k.endswith(f"/{v}")) for v in VTH}
    out["1"] = dict(pre_dev_max=pre, ok_by_vth=ok1, ok=all(ok1.values()))
    vth = 0.75 if ok1[0.75] else 1.5
    s = tag(vth, 0.3e-6)
    up, dn = row(R[f"det_c20_{s}_up1"]), row(R[f"det_c20_{s}_dn1"])
    ideal_up, ideal_dn = row(R["ideal_c20_up1"]), row(R["ideal_c20_dn1"])
    b_up, b_dn = B["base_up1"]["post"], B["base_dn1"]["post"]
    b1, bp = 0.5 * b_up["rail1_exc"], max(b_up["il_peak"]) - 20
    out["2"] = dict(setting=s, value=up["rail1_exc"], bound=b1, peak=up["peak"], peak_bound=bp,
                    ok=up["rail1_exc"] <= b1 and up["peak"] <= bp)
    db, dp = abs(ideal_dn["rail1_exc"]) + 0.30, max(b_dn["il_peak"]) - 20
    out["3"] = dict(setting=s, value=abs(dn["rail1_exc"]), bound=db, peak=dn["peak"], peak_bound=dp,
                    ok=abs(dn["rail1_exc"]) <= db and dn["peak"] <= dp)
    cb = 1.5 * ideal_up["clamp_peak"]
    out["4"] = dict(setting=s, value=up["clamp_peak"], bound=cb, ideal=ideal_up["clamp_peak"], ok=up["clamp_peak"] <= cb)
    return out


def main():
    R, B = load(HERE / "runs"), load(A180, "base_*.json")
    table = {n: row(r) for n, r in R.items() if not n.startswith("nowin_")}
    for n, r in sorted(R.items()):
        if n.startswith("nowin_"):
            print(f"{n:24s} detect {{vth: (t_det - t_step us, pre max |dev| V)}}",
                  {v: (round((d['t_det'] - 40e-6) * 1e6, 3) if d['t_det'] else None, round(d['pre_dev_max'], 3))
                   for v, d in r["detect"].items()})
    print()
    for n, x in sorted(table.items()):
        print(f"{n:28s} t_det {'-' if x['t_det_us'] is None else round(x['t_det_us'], 3):>6}  "
              f"rail1_exc {x['rail1_exc']:+.2f}  peak {x['peak']:6.1f}  clamp {x['clamp_peak']:6.1f}  "
              f"ls {x['ls_peak']:6.1f}  E {x['clamp_energy_uj']:6.1f} uJ")
    try:
        crit = criteria(R, B)
    except KeyError as e:
        print("missing run", e)
        crit = None
    if crit:
        print()
        for k, c in crit.items():
            print(k, "PASS" if c["ok"] else "FAIL", {a: (round(b, 3) if isinstance(b, float) else b)
                                                    for a, b in c.items() if a not in ("ok", "pre_dev_max")})
        print(f"{sum(c['ok'] for c in crit.values())}/{len(crit)}")
    (HERE / "a182_summary.json").write_text(json.dumps({"criteria": crit, "table": table}, indent=1))


if __name__ == "__main__":
    main()
