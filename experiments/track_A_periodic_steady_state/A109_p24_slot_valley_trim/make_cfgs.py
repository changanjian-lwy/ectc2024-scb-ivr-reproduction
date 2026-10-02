"""A109 configurations: one factor, the slots' valley trim (cfg slot_trim = 1, st_smax = 64 LSB = 2 ns per cycle), on
the adopted design. One module: C02's s1 rows (n0, j30, load steps) and A108's line rows (1 / 10 / 50 us). Four
modules: C03's n0, ls_p10 and l_m48_10us. Writes cosim/cfg_*.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
C = TA.parent / "track_C_multi_module"
SOURCES = {
    "s1_n0": C / "C02_uniform_interleave" / "cosim" / "cfg_s1_n0.json",
    "s1_j30": C / "C02_uniform_interleave" / "cosim" / "cfg_s1_j30.json",
    "s1_s_m62": C / "C02_uniform_interleave" / "cosim" / "cfg_s1_s_m62.json",
    "s1_s_p62": C / "C02_uniform_interleave" / "cosim" / "cfg_s1_s_p62.json",
    **{f"s1_{r}": TA / "A108_p24_line_slew_tolerance" / "cosim" / f"cfg_{r}.json"
       for r in ("m48_1us", "m48_10us", "m48_50us", "p48_1us", "p48_10us")},
    "m4_n0": C / "C03_four_module_standard_matrix" / "cosim" / "cfg_n0.json",
    "m4_ls_p10": C / "C03_four_module_standard_matrix" / "cosim" / "cfg_ls_p10.json",
    "m4_l_m48_10us": C / "C03_four_module_standard_matrix" / "cosim" / "cfg_l_m48_10us.json",
}
ST_SMAX = 64

if __name__ == "__main__":
    for name, src in SOURCES.items():
        c = json.loads(src.read_text())
        c["slot_trim"] = 1
        c["st_smax"] = ST_SMAX
        c["note"] = f"A109 {name}: {src.parent.parent.name}'s {src.stem[4:]} with the slots' valley trim (st_smax {ST_SMAX}). " + c["note"]
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(SOURCES), "configurations:", ", ".join(SOURCES))
