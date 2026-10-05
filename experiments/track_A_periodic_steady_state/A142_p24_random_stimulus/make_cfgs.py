"""A142 cosim cfgs: random stimuli on the adopted single-module design (A141 arm F: C10 template g125 + vff rel_q8 320,
rel_lp 1, seed 2 + floor_late 1; template A141 cfg_F_s100_l_p48_1us). Per run, seeded (numpy default_rng(142)):
L x U(0.7, 1.3), Cs x U(0.7, 1.3), driver mismatch U(-3.4, 3.4) ns, low-side jitter U(0, 100) ps (seed per run;
high-side jitter would move turn-ons off the LSB grid the duplicate classes rest on), and one of
four strata: L = line step only, B = line + load step, D = load step only (all at U(1000, 1010) us, after the latest
timed-mode entry 814 us over A138 / A139's L / Cs corners), S = a line or load step at U(160, 900) us (the mode-P
comparator phase and the switch to timed). Line step: dv U(+-1, +-8) V, slew log-U(1, 50) us; load step U(+-10,
+-62.5) A, in B at t_line + U(-10, 60) us. t_end = last event end + 150 us. I0 = the template verbatim (identity
against A141's record). Writes cosim/cfg_*.json and a142_inputs.json."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"
A141 = PROJECT / "experiments/track_A_periodic_steady_state/A141_p24_floor_late_report/cosim"
TEMPLATE = A141 / "cfg_F_s100_l_p48_1us.json"
STRATA = ["L"] * 48 + ["B"] * 24 + ["D"] * 24 + ["S"] * 24
T_AFTER_US = 150.0


def line(rng):
    return {"dv": round(float(rng.choice([-1, 1]) * rng.uniform(1.0, 8.0)), 4),
            "slew_us": round(float(np.exp(rng.uniform(np.log(1.0), np.log(50.0)))), 4)}


def load(rng):
    return round(float(rng.choice([-1, 1]) * rng.uniform(10.0, 62.5)), 4)


def draw(rng, st):
    x = {"stratum": st, "L_x": round(float(rng.uniform(0.7, 1.3)), 4), "cs_x": round(float(rng.uniform(0.7, 1.3)), 4),
         "m_ns": round(float(rng.uniform(-3.4, 3.4)), 4), "sigma_ps": round(float(rng.uniform(0.0, 100.0)), 2),
         "seed": int(rng.integers(1, 2 ** 31 - 1))}
    t1 = round(float(rng.uniform(160.0, 900.0) if st == "S" else rng.uniform(1000.0, 1010.0)), 4)
    kind = st if st != "S" else ("L" if rng.uniform() < 0.5 else "D")
    ends = []
    if kind in ("L", "B"):
        x["line_step"] = {"t_us": t1, **line(rng)}
        ends.append(t1 + x["line_step"]["slew_us"])
    if kind in ("B", "D"):
        t2 = t1 if kind == "D" else round(t1 + float(rng.uniform(-10.0, 60.0)), 4)
        x["load_step"] = {"t_us": t2, "i_a": load(rng)}
        ends.append(t2)
    x["t_end_us"] = round(max(ends) + T_AFTER_US, 1)
    return x


def cfg(tpl, name, x):
    t = json.loads(json.dumps(tpl))
    t["circuit"] = dict(t["circuit"], L=t["circuit"]["L"] * x["L_x"], cs=t["circuit"]["cs"] * x["cs_x"])
    t["driver"] = {"m_ns": x["m_ns"], "sigma_ps": x["sigma_ps"], "seed": x["seed"], "jitter_edges": "low"}
    t.pop("line_step", None)
    for k in ("line_step", "load_step"):
        if k in x:
            t[k] = x[k]
    t["t_end_us"] = x["t_end_us"]
    t["note"] = (f"A142 {name} ({x['stratum']}): adopted single-module design + floor_late 1, L x {x['L_x']}, Cs x "
                 f"{x['cs_x']}, driver {x['m_ns']} ns / {x['sigma_ps']} ps, line {x.get('line_step')}, load {x.get('load_step')}.")
    t["out"] = f"run_{name}.json"
    (COS / f"cfg_{name}.json").write_text(json.dumps(t, indent=1) + "\n")


def main():
    COS.mkdir(exist_ok=True)
    tpl = json.loads(TEMPLATE.read_text())
    rng = np.random.default_rng(142)
    runs = {f"z{i + 1:03d}": draw(rng, st) for i, st in enumerate(STRATA)}
    for n, x in runs.items():
        cfg(tpl, n, x)
    t = json.loads(TEMPLATE.read_text())
    t["note"] = "A142 I0: A141 F_s100_l_p48_1us verbatim (identity replay)."
    t["out"] = "run_I0.json"
    (COS / "cfg_I0.json").write_text(json.dumps(t, indent=1) + "\n")
    order = sorted(runs, key=lambda n: -runs[n]["t_end_us"])          # longest first
    (COS / "ORDER.txt").write_text("\n".join(["cfg_I0.json"] + [f"cfg_{n}.json" for n in order]) + "\n")
    (HERE / "a142_inputs.json").write_text(json.dumps({"seed": 142, "template": str(TEMPLATE.relative_to(PROJECT)),
                                                       "runs": runs}, indent=1) + "\n")
    te = np.array([x["t_end_us"] for x in runs.values()])
    print(f"{len(runs)} runs + I0; t_end mean {te.mean():.0f} us, total {te.sum() / 1e3:.1f} ms simulated")
    for st in "LBDS":
        xs = [x for x in runs.values() if x["stratum"] == st]
        print(st, len(xs), "dv", sorted(round(x["line_step"]["dv"], 1) for x in xs if "line_step" in x)[:3], "...")


if __name__ == "__main__":
    main()
