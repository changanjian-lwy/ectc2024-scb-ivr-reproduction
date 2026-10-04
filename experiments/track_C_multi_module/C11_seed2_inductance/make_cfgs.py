"""C11 configurations: the four-module final design (C10: C06 + vff {rel_q8 320, rel_lp 1, seed 2}) with every module's L
scaled: L x 1.2 on s_p62, m3n, l_p48_1us and L x 1.3 on s_p62. Steps at 1000 us (end 1400 us; phase 1 is timed from
767 us at L x 1.2, 813 us at L x 1.3 on one module), m3n ends at 1200 us. Writes cosim/cfg_l<kkk>_<row>.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C10 = HERE.parent / "C10_seed_before_entry" / "cosim"
RUNS = ((1.2, "s_p62"), (1.2, "m3n"), (1.2, "l_p48_1us"), (1.3, "s_p62"))


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    order = []
    for k, row in RUNS:
        c = json.loads((C10 / f"cfg_{row}.json").read_text())
        c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * k)
        key = "load_step" if c.get("load_step") else "line_step" if c.get("line_step") else None
        if key:
            c[key] = dict(c[key], t_us=1000.0)
        c["t_end_us"] = 1400.0 if key else 1200.0
        name = f"l{round(k * 100):03d}_{row}"
        c["note"] = f"C11 {name}: C10's {row} (four-module final design, vff seed 2) with every module's L x {k}" + \
            (", step at 1000 us." if key else ".")
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
