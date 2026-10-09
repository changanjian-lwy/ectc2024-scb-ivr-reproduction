"""A180 analysis: the BOUNDARY criteria from runs/*.json -> a180_summary.json and a table on stdout.

Run from the project root: python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_analyze.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load():
    runs = {}
    for f in sorted((HERE / "runs").glob("*.json")):
        r = json.loads(f.read_text())
        r.pop("trace", None)
        runs[f.stem] = r
    return runs


def row_line(name, r):
    pre, post = r["pre"], r.get("post") or r.get("startup")
    cl = pre.get("clamp_loss_w")
    s = (f"{name:16s} spread {pre['spread_pct']:5.2f} %  rails {[round(x, 2) for x in pre['rails']]}"
         f"  clamp {'-' if cl is None else round(cl, 3)} W")
    if "rail1_exc" in post:
        s += (f" | rail1_exc {post['rail1_exc']:+.2f} V  peak {max(post['il_peak']):.1f} A"
              f"  Vo {post['vo_min']:.3f}-{post['vo_max']:.3f}")
        if "clamp_peak_a" in post:
            s += f"  clamp peak {max(post['clamp_peak_a']):.1f} A  {post['clamp_energy_uj']:.1f} uJ"
    else:
        s += f" | start-up peak {max(post['il_peak']):.1f} A  rail dev end {post['rail_dev_end']:.2f} V"
    return s


def criteria(R):
    g = lambda v, row: R[f"{v}_{row}"]
    exc = lambda v, row: g(v, row)["post"]["rail1_exc"]
    peak = lambda v, row: max(g(v, row)["post"]["il_peak"])
    spread = lambda v: g(v, "up1")["pre"]["spread_pct"]
    loss = lambda v: g(v, "up1")["pre"].get("clamp_loss_w", 0.0)
    b1, bs = exc("base", "up1"), spread("base")
    out = {}
    out["1"] = dict(value=exc("d07_c20", "up1"), bound=0.5 * b1, ok=exc("d07_c20", "up1") <= 0.5 * b1)
    out["2"] = dict(spread=spread("d07_c20"), spread_bound=bs + 2, loss_w=loss("d07_c20"),
                    ok=spread("d07_c20") <= bs + 2 and loss("d07_c20") <= 0.5)
    out["3"] = dict(value=exc("act_c20", "up1"), bound=0.5 * b1, peak=peak("act_c20", "up1"),
                    peak_bound=peak("base", "up1") - 20,
                    ok=exc("act_c20", "up1") <= 0.5 * b1 and peak("act_c20", "up1") <= peak("base", "up1") - 20)
    bd = abs(exc("base", "dn1"))
    out["4"] = dict(value=abs(exc("act_c20", "dn1")), bound=0.5 * bd, ok=abs(exc("act_c20", "dn1")) <= 0.5 * bd)
    out["5"] = dict(loss_w=loss("actall_c20"), spread=spread("actall_c20"), spread_bound=bs + 2,
                    ok=loss("actall_c20") <= 0.5 and spread("actall_c20") <= bs + 2)
    e6, e20, e60 = exc("act_c06", "up1"), exc("act_c20", "up1"), exc("act_c60", "up1")
    out["6"] = dict(c06=e6, c20=e20, c60=e60, bound_c60=0.4 * b1, ok=e6 > e20 > e60 and e60 <= 0.4 * b1)
    return out


def main():
    R = load()
    for name, r in R.items():
        print(row_line(name, r))
    try:
        crit = criteria(R)
    except KeyError as e:
        print("missing run", e)
        crit = None
    if crit:
        print()
        for k, c in crit.items():
            print(k, "PASS" if c["ok"] else "FAIL", {a: (round(b, 3) if isinstance(b, float) else b) for a, b in c.items() if a != "ok"})
        print(f"{sum(c['ok'] for c in crit.values())}/{len(crit)}")
    (HERE / "a180_summary.json").write_text(json.dumps({"criteria": crit, "runs": R}, indent=1))


if __name__ == "__main__":
    main()
