"""C10 configurations. Four modules: C06's 18 rows (A129's g125 + modules 4 + slave_floor 1) with vff {rel_q8 320,
rel_lp 1, seed 2} in every module (seed 2: ton's low-pass restarts from the Ton before mode P, scb_vff C10), C06's
timing; ORDER_gate.txt (n0, m1n, m3n) and ORDER_rest.txt (the other 15). Single module: A137's 18 cfgs with seed 2
(cfg_s<mmm>_<row>.json); ORDER_s100.txt and ORDER_s_rest.txt. `--contingency ROW...`: C06's row with its step moved to
C10's offset after the master's phase-1 turn-on (cfg_c06al10_<row>.json, ORDER_c06al10.txt); `--at-c06 ROW...`: C10's row
with its step at C06's offset (cfg_c10al6_<row>.json, ORDER_c10al6.txt)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
C06 = HERE.parent / "C06_slave_floor" / "cosim"
A137 = HERE.parents[1] / "track_A_periodic_steady_state" / "A137_p24_vff_restart_at_handover" / "cosim"
Q = {"rel_q8": 320, "rel_lp": 1, "seed": 2}
GATE = ("n0", "m1n", "m3n")


def write(name, c):
    c["out"] = f"run_{name}.json"
    (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    rows = (C06 / "ORDER.txt").read_text().split()
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        c["vff"] = dict(c["vff"], **Q)
        c["note"] = f"C10 {row}: C06's {row} with vff rel_q8 320, rel_lp 1, seed 2 (low-pass seeded with mode S's Ton)."
        write(row, c)
    single = (A137 / "ORDER.txt").read_text().split()
    for name in single:
        c = json.loads((A137 / f"cfg_{name}.json").read_text())
        c["vff"] = dict(c["vff"], seed=2)
        c["note"] = c["note"].replace("A137", "C10").replace("(seed 1)", "(seed 2)")
        write(name, c)
    lists = {"gate": GATE, "rest": [r for r in rows if r not in GATE],
             "s100": [n for n in single if n.startswith("s100_")], "s_rest": [n for n in single if not n.startswith("s100_")]}
    for k, v in lists.items():
        (HERE / "cosim" / f"ORDER_{k}.txt").write_text("\n".join(v) + "\n")
    print(len(rows), "four-module +", len(single), "single-module cfgs")


def ph1_on(d, t1, t2):
    return [q["t_s"] for q in d["turnons_last"] if q["phase"] == 1 and t1 <= q["t_s"] <= t2]


def contingency(rows):
    """C09's criterion 3 rerun: C06's row with its step at C10's offset after the master's phase-1 turn-on."""
    names = []
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        key = "load_step" if c.get("load_step") else "line_step"
        t0 = c[key]["t_us"] * 1e-6
        r10 = json.loads((HERE / "cosim" / f"run_{row}.json").read_text())
        r6 = json.loads((C06 / f"run_{row}.json").read_text())
        off = t0 - max(ph1_on(r10, 0.0, t0))
        t_al = min(ph1_on(r6, t0 - 1e-6, t0 + 1e-6), key=lambda t: abs(t + off - t0)) + off
        c[key] = dict(c[key], t_us=round(t_al * 1e6, 4))
        c["note"] = f"C10 c06al10_{row}: C06's {row} (no change to the design) with the step at C10's offset ({off * 1e9:.1f} ns)."
        names.append(f"c06al10_{row}")
        write(names[-1], c)
        print(names[-1], c[key]["t_us"], "us")
    (HERE / "cosim" / "ORDER_c06al10.txt").write_text("\n".join(names) + "\n")


def at_c06(rows):
    """Trace for a stepped-row miss: C10's row with its step at C06's offset after the master's phase-1 turn-on."""
    names = []
    for row in rows:
        c = json.loads((HERE / "cosim" / f"cfg_{row}.json").read_text())
        key = "load_step" if c.get("load_step") else "line_step"
        t0 = c[key]["t_us"] * 1e-6
        r10 = json.loads((HERE / "cosim" / f"run_{row}.json").read_text())
        r6 = json.loads((C06 / f"run_{row}.json").read_text())
        off = t0 - max(ph1_on(r6, 0.0, t0))
        t_al = min(ph1_on(r10, t0 - 1e-6, t0 + 1e-6), key=lambda t: abs(t + off - t0)) + off
        c[key] = dict(c[key], t_us=round(t_al * 1e6, 4))
        c["note"] = f"C10 c10al6_{row}: C10's {row} with the step at C06's offset ({off * 1e9:.1f} ns)."
        names.append(f"c10al6_{row}")
        write(names[-1], c)
        print(names[-1], c[key]["t_us"], "us")
    (HERE / "cosim" / "ORDER_c10al6.txt").write_text("\n".join(names) + "\n")


if __name__ == "__main__":
    arg = sys.argv[1:2]
    contingency(sys.argv[2:]) if arg == ["--contingency"] else at_c06(sys.argv[2:]) if arg == ["--at-c06"] else main()
