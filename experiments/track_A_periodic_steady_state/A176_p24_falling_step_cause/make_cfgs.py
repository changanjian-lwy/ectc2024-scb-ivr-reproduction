"""A176 cosim cfgs: which part of the final plant turns A148's falling-step valley loss into restarts and spikes
(A173 ff -8 V / 10 us, A175 nom -4.8 V / 1 us). Two variants of each row:
- v2lead: ideal low sides, no interlock, A167's ramped 8 ns lead (A167's form: A164's cfg + lead_ramp_us 20);
- v5nolead: the final plant without the lead (driver hs_on_lead_ns / lead_ramp_us removed, as A164's lead0 rows).
Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
FINAL = {"nom_l_m48_1us": TA / "A175_p24_final_plant_a152_matrix" / "cosim" / "cfg_nom_l_m48_1us.json",
         "ff_l_m80_10us": TA / "A173_p24_final_plant_coverage" / "cosim" / "cfg_ff_l_m80_10us.json"}


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for row, f in FINAL.items():
        c = json.loads(f.read_text())
        g = {k: v for k, v in c["gate"].items() if k not in ("switches", "interlock", "t_il_ns")}
        v2 = dict(c, gate=g)                                   # driver keeps the 8 ns lead ramped over 20 us
        drv = {k: v for k, v in c["driver"].items() if k not in ("hs_on_lead_ns", "lead_ramp_us")}
        v5 = dict(c, driver=drv)
        for tag, cfg in (("v2lead", v2), ("v5nolead", v5)):
            name = f"{tag}_{row}"
            (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json",
                                                                  note=f"A176 {name}: {row}, variant {tag}"), indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
