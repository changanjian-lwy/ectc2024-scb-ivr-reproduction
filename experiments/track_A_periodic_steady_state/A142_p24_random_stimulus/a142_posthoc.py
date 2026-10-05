"""A142 post hoc (not registered; RESULTS Section 3): one-factor variations of z104 (S stratum: +7.89 V over 3.95 us at
295.2 us, in the mode-P comparator phase, L x 1.10, Cs x 0.89, driver -2.09 ns / 62 ps), to trace its 50 us
oscillation (351 A, Vo 0.93-1.08 V). Writes cosim/cfg_P*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
BASE = json.loads((COS / "cfg_z104.json").read_text())
T_AFTER_US = 150.0


def variant(name, note, **ch):
    t = json.loads(json.dumps(BASE))
    for k, v in ch.items():
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v
    ls = t["line_step"]
    t["t_end_us"] = round(ls["t_us"] + ls["slew_us"] + T_AFTER_US, 1)
    t["note"] = f"A142 post hoc {name}: z104 with {note}."
    t["out"] = f"run_{name}.json"
    (COS / f"cfg_{name}.json").write_text(json.dumps(t, indent=1) + "\n")


def main():
    ls, c, drv = BASE["line_step"], BASE["circuit"], BASE["driver"]
    L0, cs0 = c["L"] / 1.1006, c["cs"] / 0.8877
    variant("P1_novff", "no Vin feed-forward (vff removed)", vff=None)
    variant("P2_t1000", "the step at 1000 us (timed mode)", line_step=dict(ls, t_us=1000.0))
    variant("P3_t600", "the step at 600 us (late comparator phase)", line_step=dict(ls, t_us=600.0))
    variant("P4_drv0", "a nominal driver (no mismatch, no jitter)", driver=dict(drv, m_ns=0.0, sigma_ps=0.0))
    variant("P5_lc0", "nominal L and Cs", circuit=dict(c, L=L0, cs=cs0))
    variant("P6_dv48", "dv +4.8 V at the same slope (2.4 us)", line_step=dict(ls, dv=4.8, slew_us=round(4.8 / 7.8894 * 3.9536, 4)))
    variant("P7_s10", "slew 10 us", line_step=dict(ls, slew_us=10.0))
    variant("P8_dv48_s1", "dv +4.8 V over 1 us (A130 spec corner)", line_step=dict(ls, dv=4.8, slew_us=1.0))


if __name__ == "__main__":
    main()
