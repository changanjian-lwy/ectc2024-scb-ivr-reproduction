"""A240 cfgs (BOUNDARY Section 1): a 1 kW, 1 V accelerator's repeated load steps on one module (a quarter of the
system: P24 Fig. 6's processor on four 250 A modules), final configuration.
  python3 make_cfgs.py
At 300 us the 4 mOhm load disconnects and a constant-current trapezoid takes over at 250 A (cfg load_pulse): 50 %
duty between 100 % and LO of the module's load, 1250 A/us per module (5000 A/us for the system), at F_KHZ, to 600 us;
then 250 A to 700 us. Boards: N0 and N75 at 25 C between 10 % and 100 %, S75 at 125 C between 30 % (its minimum)
and 100 %, from A237's cfgs (nominal boards with A231's handover lead, the slow board with the plain request)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A37 = TA / "A237_p24_true_light_load" / "cosim"
F_KHZ = (10.0, 30.0, 60.0, 100.0, 200.0, 1000.0)
BOARDS = {"N0": ("c2_N0", 25.0, 0.7), "N75": ("c0_N75", 25.0, 0.7), "S75h": ("c30_S75h", 75.0, None)}  # cfg, low A, lead
I_HI, SLEW, T0, T_STOP, T_END = 250.0, 1250.0, 300.0, 600.0, 700.0


def main():
    COS.mkdir(exist_ok=True)
    n = 0
    for b, (stem, lo, lead) in BOARDS.items():
        for f in F_KHZ:
            c = json.loads((A37 / f"cfg_{stem}.json").read_text())
            for k in ("load_step", "load_step2", "debug_edges_us"):
                c.pop(k, None)
            row = f"p_{b}_{f:g}k"
            c.update(out=f"run_{row}.json", t_end_us=T_END, t_load_off_us=T0,
                     load_pulse={"t_us": T0, "t_stop_us": T_STOP, "i_lo_a": lo, "i_hi_a": I_HI, "f_khz": f, "duty": 0.5,
                                 "slew_a_us": SLEW},
                     note=f"A240 {row}: A237 {stem}; from {T0:g} us a constant-current load {I_HI:g} <-> {lo:g} A at "
                          f"{f:g} kHz, 50 % duty, {SLEW:g} A/us, to {T_STOP:g} us, then {I_HI:g} A to {T_END:g} us")
            if lead is not None:
                c["hand_lead_us"] = lead
            else:
                c.pop("hand_lead_us", None)
            (COS / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
            n += 1
    print(n, "cfgs")


if __name__ == "__main__":
    main()
