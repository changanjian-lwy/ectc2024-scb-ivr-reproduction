"""A129 configurations. Stage 1: A128's eight rows (A124's seven step rows and n0) with the slope gate (vff "gth" 100
codes) -> cosim/cfg_g125_<row>.json. Identity reruns with the A129 code -> tmp/identity_a129/: A124's p125_l_p48_1us
(vff off) and A128's v125_l_m48_1us (gth absent = 0, the falling term active). Stage 2: the standard matrix's driver
and +-25 A rows (matrix.ROWS m1n m1p m3n m3p j30 j100 s_m25 s_p25) on A124's p125_n0 at A124's timing (no step:
1000 us; load step at 800 us, end 1200 us), without feed-forward (o125_*) and with the gated one (g125_*). Writes
ORDER.txt (stage 1) and ORDER_matrix.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim import matrix  # noqa: E402

A124 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A124_p24_two_point_five_mhz" / "cosim"
A128 = HERE.parent / "A128_cosim_vin_feedforward" / "cosim"
GTH = 100
STEP_ROWS = ("p125_l_p48_5us", "p125_l_p48_1us", "p125_l_m48_1us", "p125_l_m48_5us", "p125_l_m80_10us", "p125_s_p62",
             "p125_s_m62", "p125_n0")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")


def write(path: Path, c: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c, indent=1) + "\n")


def main():
    for name in STEP_ROWS:
        c = json.loads((A128 / f"cfg_v{name[1:]}.json").read_text())
        c["vff"]["gth"] = GTH
        c["note"] = f"A129 g{name[1:]}: A128's v{name[1:]} with the slope gate (gth {GTH} codes)"
        c["out"] = f"run_g{name[1:]}.json"
        write(HERE / "cosim" / f"cfg_g{name[1:]}.json", c)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(f"g{n[1:]}" for n in STEP_ROWS) + "\n")

    idd = PROJECT / "tmp" / "identity_a129"
    for src, name in ((A124, "p125_l_p48_1us"), (A128, "v125_l_m48_1us")):
        c = json.loads((src / f"cfg_{name}.json").read_text())
        c["out"] = f"run_{name}.json"
        write(idd / f"cfg_{name}.json", c)

    base = json.loads((A124 / "cfg_p125_n0.json").read_text())
    vff = dict(json.loads((HERE / "cosim" / "cfg_g125_n0.json").read_text())["vff"])
    order = []
    for row, c in matrix.configs(base, MATRIX_ROWS).items():
        c["t_end_us"] = 1000.0
        if "load_step" in c:
            c["load_step"]["t_us"] = 800.0; c["t_end_us"] = 1200.0
        for arm in ("o", "g"):
            x = json.loads(json.dumps(c))
            if arm == "g":
                x["vff"] = dict(vff)
            x["note"] = f"A129 {arm}125_{row}: A124's p125_n0 on the standard matrix row {row}" + \
                        (" with the gated Vin feed-forward" if arm == "g" else " (no feed-forward)")
            x["out"] = f"run_{arm}125_{row}.json"
            write(HERE / "cosim" / f"cfg_{arm}125_{row}.json", x)
            order.append(f"{arm}125_{row}")
    (HERE / "cosim" / "ORDER_matrix.txt").write_text("\n".join(order) + "\n")


if __name__ == "__main__":
    main()
