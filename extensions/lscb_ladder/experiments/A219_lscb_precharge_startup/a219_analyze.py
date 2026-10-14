"""A219 analysis: the registered criteria on runs/*.json -> a219_summary.json. Run from anywhere."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = lambda n: json.loads((HERE / "runs" / f"{n}.json").read_text())


def main():
    pc = {f"{v}_{r}": R(f"{v}_{r}")["precharge"] for r in ("pre_fast", "pre_slow") for v in ("base", "rdiv_pc", "lad_pc")}
    st = {n: R(f"base_{n}")["startup"] for n in ("soft_rdiv", "soft_nominal", "su")}
    crit = {
        "1": dict(value=pc["base_pre_slow"]["sw_max"][0], bound=40.0),
        "2": dict(sw=max(pc["rdiv_pc_pre_slow"]["sw_max"]), sw_bound=16.0,
                  dev=max(abs(x) for x in pc["rdiv_pc_pre_slow"]["vcs_dev_end"]), dev_bound=1.0),
        "3": dict(value=pc["rdiv_pc_pre_fast"]["sw_max"][0], bound=40.0),
        "4": dict(value=max(pc["lad_pc_pre_fast"]["sw_max"]), bound=20.0),
        "5": dict(peak=max(st["soft_rdiv"]["il_peak"]), peak_bound=max(st["su"]["il_peak"]) + 10.0,
                  sw=max(st["soft_rdiv"]["sw_max"]), sw_bound=16.0),
    }
    crit["1"]["ok"] = crit["1"]["value"] >= 40.0
    crit["2"]["ok"] = crit["2"]["sw"] <= 16.0 and crit["2"]["dev"] <= 1.0
    crit["3"]["ok"] = crit["3"]["value"] >= 40.0
    crit["4"]["ok"] = crit["4"]["value"] <= 20.0
    crit["5"]["ok"] = crit["5"]["peak"] <= crit["5"]["peak_bound"] and crit["5"]["sw"] <= 16.0
    out = dict(criteria=crit, passed=sum(c["ok"] for c in crit.values()), precharge=pc, start=st)
    (HERE / "a219_summary.json").write_text(json.dumps(out, indent=1))
    for k, c in crit.items():
        print(k, "PASS" if c["ok"] else "FAIL", {a: round(b, 3) if isinstance(b, float) else b for a, b in c.items() if a != "ok"})
    for n, x in pc.items():
        print(f"{n:17s} sw_max {[round(v, 1) for v in x['sw_max']]}  SH1>40V {x['sh1_over_40v_s'] * 1e3:6.2f} ms  "
              f"Vcs dev end {[round(v, 2) for v in x['vcs_dev_end']]}")
    for n, x in st.items():
        print(f"{n:13s} peaks {[round(v) for v in x['il_peak']]}  sw_max {[round(v, 1) for v in x['sw_max']]}  "
              f"rail_dev_end {x['rail_dev_end']:.2f}  vo_end {x['vo_end']:.3f}  vo_max {x['vo_max']:.3f}")


if __name__ == "__main__":
    main()
