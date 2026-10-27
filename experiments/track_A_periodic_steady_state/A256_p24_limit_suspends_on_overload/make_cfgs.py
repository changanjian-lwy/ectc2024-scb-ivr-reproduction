"""A256 cfgs (BOUNDARY Section 1): A254's limit + "n_susp" N_SUSP, cfg_s_<row>.json -> run_s_<row>.json.
- CHANGE: A254's rows whose up/down count of limited pulses reached N_SUSP (A254 records; a256_counts.json);
- O125: A255's 125 % steps on the 2.2 nH boards, arm l;
- IDENT: three rows whose count stayed under N_SUSP, which must equal A254's records bit for bit.
  python3 make_cfgs.py -> cosim/cfg_s_*.json, cosim/queue.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A54, A55 = TA / "A254_p24_peak_limit_measured_level" / "cosim", TA / "A255_p24_overload_on_2p2nh" / "cosim"
N_SUSP = 6
CHANGE = ("m4_s_p250", "k_N0", "k_S75h", "a_S75h_d2", "a_S75h_d20", "a_S75_d20")
O125 = ("o125_N75", "o125_S75h")
IDENT = ("p_N75_1000k", "p_S75h_1000k", "p_S75h_10k")


def src(row):
    return (A55 / f"cfg_l_{row}.json") if row in O125 else (A54 / f"cfg_l_{row}.json")


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    names = []
    for row in CHANGE + O125 + IDENT:
        c = json.loads(src(row).read_text())
        c["ocp"] = c["ocp"] | {"n_susp": N_SUSP}
        c.update(out=f"run_s_{row}.json", note=f"A256: {src(row).relative_to(TA)} + ocp n_susp {N_SUSP}")
        (HERE / "cosim" / f"cfg_s_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        names.append(f"cfg_s_{row}.json")
    (HERE / "cosim" / "queue.txt").write_text("".join(n + "\n" for n in names))
    print(len(names), "cfgs")


if __name__ == "__main__":
    main()
