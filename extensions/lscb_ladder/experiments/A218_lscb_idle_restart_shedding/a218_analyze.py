"""A218 analysis: the registered criteria on runs/*.json -> a218_summary.json. Run from anywhere."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = lambda n: json.loads((HERE / "runs" / f"{n}.json").read_text())
PK = lambda n: max(R(n)["il_peak"])


def main():
    names = ["base_shed4", "actall_c20_shed4", "base_rs0", "base_rsv", "base_rs2", "base_rs4", "d07_c20_rs4", "act_c20_rs4"]
    rows = {n: {k: R(n)[k] for k in ("rail_dev_max", "ladder_dev_max", "il_peak", "t_settle_us", "spread_end_pct",
                                     "vo_min", "vo_max", "rails_at", "ladder_at", "clamp_peak_a", "cs_ic") if k in R(n)}
            for n in names}
    crit = {
        "1": dict(value=R("base_shed4")["rail_dev_max"], bound=3.0),
        "2": dict(value=R("actall_c20_shed4")["ladder_dev_max"], bound=1.5),
        "3": dict(value=PK("base_rs2") - PK("base_rs0"), bound=15.0),
        "4": dict(dev=R("act_c20_rs4")["rail_dev_max"], dev_bound=R("base_rs0")["rail_dev_max"] + 0.5,
                  peak=PK("act_c20_rs4"), peak_bound=PK("base_rsv") + 5.0),
        "5": dict(value=PK("d07_c20_rs4"), bound=PK("base_rs4") - 15.0),
    }
    for k in ("1", "2", "3"):
        crit[k]["ok"] = crit[k]["value"] >= crit[k]["bound"]
    crit["4"]["ok"] = crit["4"]["dev"] <= crit["4"]["dev_bound"] and crit["4"]["peak"] <= crit["4"]["peak_bound"]
    crit["5"]["ok"] = crit["5"]["value"] <= crit["5"]["bound"]
    out = dict(criteria=crit, passed=sum(c["ok"] for c in crit.values()), rows=rows)
    (HERE / "a218_summary.json").write_text(json.dumps(out, indent=1))
    for k, c in crit.items():
        print(k, "PASS" if c["ok"] else "FAIL", {a: round(b, 3) if isinstance(b, float) else b for a, b in c.items() if a != "ok"})
    for n, r in rows.items():
        print(f"{n:17s} peak {max(r['il_peak']):6.1f}  rail_dev {r['rail_dev_max']:5.2f}  ladder_dev {r.get('ladder_dev_max', float('nan')):5.2f}"
              f"  settle {r['t_settle_us']:5.2f} us  spread_end {r['spread_end_pct']:6.1f} %  Vo {r['vo_min']:.3f}-{r['vo_max']:.3f}")


if __name__ == "__main__":
    main()
