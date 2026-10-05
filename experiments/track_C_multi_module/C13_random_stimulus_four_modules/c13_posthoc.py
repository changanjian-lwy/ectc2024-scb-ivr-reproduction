"""C13 post hoc (RESULTS 2) -> c13_posthoc.json: (a) y08's floor-first duplicate in LSB command times (low-off edges minus
t_drv and the low-side mismatch; the clocked one is on the integer grid); (b) every duplicate turn-on in the C12, C13, A142
and A143 records with its spacing in LSB and class (current oracles, K5 included); (c) the >200 A rows replayed on one
module (cfg_s1_*: modules / slave_floor removed) against four, with the post-step peak's phase and time."""
from __future__ import annotations

import glob
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
TA = PROJECT / "experiments/track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A142_p24_random_stimulus"))
import a142_oracles as O  # noqa: E402

COS = HERE / "cosim"


def dups(path):
    r = O.check(path)
    return [{"file": Path(path).parent.parent.name[:3] + "/" + r["file"], "cls": e["cls"], "module": e["module"],
             "t_us": round(e["t_s"] * 1e6, 4), "dt_lsb": round(e["dt_ns"] / 0.03125, 3)}
            for e in r["events"] if e["kind"].startswith("dup")]


def tie(name="y08", module=2, t0=1012.0e-6, t1=1012.03e-6):
    d = json.loads((COS / f"run_{name}.json").read_text())
    md = ([d] + d["modules_rest"])[module - 1]
    lsb, tdrv, m = d["lsb_s"], d["cfg"]["t_drv_ns"] * 1e-9, d["cfg"]["driver"]["m_ns"] * 1e-9
    lo = [round((x["t_s"] - tdrv - m) / lsb, 3) for x in md["lowoffs_last"] if x["phase"] == 1 and t0 < x["t_s"] < t1]
    on = [round((x["t_s"] - tdrv) / lsb, 3) for x in md["turnons_last"] if x["phase"] == 1 and t0 < x["t_s"] < t1 + 20e-9]
    return {"lowoff_cmd_lsb": lo, "turnon_cmd_lsb": on, "a_tlo_round": round(lo[0]), "t_lo": round(lo[1])}


def peak(path):
    d = json.loads(Path(path).read_text())
    ts = d["cfg"]["line_step"]["t_us"]
    a, m, q = max(((q["i_a"], i + 1, q) for i, r in enumerate([d] + d.get("modules_rest", [])) for q in r["highoffs_last"]
                   if q["t_s"] >= ts * 1e-6), key=lambda x: x[0])
    return {"peak_a": round(a, 1), "module": m, "phase": q["phase"], "t_after_us": round(q["t_s"] * 1e6 - ts, 2)}


def main():
    files = sorted(glob.glob(str(HERE / "cosim/run_y*.json")) + glob.glob(str(HERE / "cosim/run_I0.json"))
                   + glob.glob(str(HERE.parent / "C12_floor_late_four_modules/cosim/run_*.json"))
                   + glob.glob(str(TA / "A142_p24_random_stimulus/cosim/run_z*.json"))
                   + glob.glob(str(TA / "A143_p24_short_comparator_phase/cosim/run_*.json")))
    with Pool(8) as p:
        dl = [x for r in p.map(dups, files) for x in r]
    rows = {n: {"cfg": json.loads((COS / f"cfg_{n}.json").read_text())["line_step"],
                "four": peak(COS / f"run_{n}.json"), "one": peak(COS / f"run_s1_{n}.json")} for n in ("y02", "y08", "y10")}
    out = {"tie_y08": tie(), "records_scanned": len(files), "duplicates": dl, "single_vs_four": rows}
    (HERE / "c13_posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print("y08 tie", out["tie_y08"])
    print(len(files), "records,", len(dl), "duplicates:", {c: sorted(x["dt_lsb"] for x in dl if x["cls"] == c)
                                                           for c in {x["cls"] for x in dl}})
    for n, r in rows.items():
        print(n, r["cfg"], "one", r["one"], "four", r["four"])


if __name__ == "__main__":
    main()
