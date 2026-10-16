"""D85: the final design point's loss ledger, item by item (2.5 MHz design, per 250 W module).

    PYTHONPATH=src python3 scripts/p24_loss_ledger.py

First the old numbers from their own inputs, bit for bit: A124's middle budget (a124_summary p125_n0, D62's terms on the
A124 record) and D83's efficiencies (D73's split + D83's copper + D83's core + D75 / D70's package terms). Then the
ledger: the semiconductor terms from the gate-level plant's books (V6, A206 run_E_N0_steady_ls0p3, settled, switches at
the datasheet maximum, 50 pH loop with its damper; LTspice within 0.5-0.7 %), the terms the books do not hold (gate
drive, series-capacitor ESR, the loop damper's dissipation, D80), D83's inductor copper and core, D75's lateral copper.
Overlaps are resolved by replacement (each physical loss once; the doc's Section 2). Temperature as D73 / D84: switch
conduction x (1 + A_SW (T - 25)), copper x (1 + A_CU (T - 25)), everything else held. Writes
symbolic_derivations/03_P24_native/diagnostics/D85_loss_ledger.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_electrothermal as ET  # noqa: E402
import p24_hbs1_units as H  # noqa: E402
import scb_ivr.p24_loss_budget as lb  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
A124_REC = TA / "A124_p24_two_point_five_mhz" / "cosim" / "run_p125_n0.json"
BOOKS = {"N0": ("A206_p24_low_side_zvs_turn_on", "a206_summary.json", ("runs", "E_N0_steady_ls0p3"), "run_E_N0_steady_ls0p3.json"),
         "N75": ("A211_p24_loss_against_load", "a211_summary.json", ("runs", "e_N75_25_100"), "run_e_N75_25_100.json"),
         "S75": ("A211_p24_loss_against_load", "a211_summary.json", ("runs", "e_S75_25_100"), "run_e_S75_25_100.json")}
N_DEV = 4 * (lb.N_H + lb.N_L)
T_HOT = 85.0


def _mod(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def eff(p_out, p):
    return 100.0 * p_out / (p_out + p)


def reproduce():
    """A124's published budget and D83's published efficiencies from their inputs (exact float equality)."""
    m = lb.measure(json.loads(A124_REC.read_text()))
    b = lb.budget(m["phases"], m["ton_s"], m["period_s"], 7.3333333e-9 / 2.5, dict(ET.MIDDLE, l_tech="mpc_hbs1_500nH"),   # A124's L1
                  m["rails_v"], m["dv_next_v"], p_rev=m["p_rev_w"], p_out=m["p_out_w"])
    pub = json.loads((TA / "A124_p24_two_point_five_mhz" / "a124_summary.json").read_text())["p125_n0"]["budget_w"]
    a124_ok = all(b[k] == pub[k] for k in pub)
    d83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]["2.5MHz"]
    st = d83["cases"]["steady"]
    p25, cu = H.budget(m, st["l_nh"] * 1e-9, H.UNITS[st["unit"]][1] / H.UNITS[st["unit"]][0] * 1e6)   # as D83 (Ohm / H)
    d75 = json.loads((DIAG / "D75_footprint.json").read_text())
    got = {"eff_no_core": eff(m["p_out_w"], p25)}
    for tag in ("lo", "hi"):
        for kn, kv in (("k1", 1.0), ("kV", d83["kappa_nearest"])):
            w = kv * d83["core"][tag]["k1_eq1_w"]
            got[f"{tag}_{kn}_eq1"] = eff(m["p_out_w"], p25 + w)
            for pk, (cu_key, loop) in H.PKG.items():
                got[f"{tag}_{kn}_eq1_{pk}"] = eff(m["p_out_w"], p25 + w + d75["lateral"][cu_key]["w_20mm"] + loop)
    d83_ok = got["eff_no_core"] == st["eff_no_core"] and all(got[k] == st["eff"][k] for k in got if k != "eff_no_core")
    old_semis = {k: b[k] for k in ("switch_conduction", "hard_turn_on", "turn_off_overlap", "reverse_conduction",
                                    "gate_drive", "series_caps")}
    return {"a124_budget_w": {k: b[k] for k in pub}, "a124_bit_for_bit": a124_ok, "d83_eff": got, "d83_bit_for_bit": d83_ok,
            "d83_p25_w": p25, "d83_copper_w": cu, "a124_f_hz": 1.0 / m["period_s"], "old_semis_w": old_semis,
            "p_out_w": m["p_out_w"]}


def books(board):
    """The V6 plant's settled books (W per module) from the summary; recomputed from the record when it is here."""
    folder, summ, keys, rec = BOOKS[board]
    s = json.loads((TA / folder / summ).read_text())
    for k in keys:
        s = s[k]
    st = s.get("settled", s)                       # A206: whole()'s settled block; A211: the run's own books (a210)
    out = {"books_w": st["books_w"], "period_ns": st["period_ns"], "p_out_w": st["p_out_w"], "peak_a": st["peak_a"],
           "record": f"{folder}/cosim/{rec}", "recomputed": None}
    path = TA / folder / "cosim" / rec
    if path.exists() and "settled" in s:
        a206 = _mod("a206_analyze", TA / "A206_p24_low_side_zvs_turn_on" / "a206_analyze.py")
        again = a206.whole(path)["settled"]["books_w"]
        out["recomputed"] = all(again[k] == st["books_w"][k] for k in again)
    return out


def ledger(board, rep, temp=25.0):
    """Items (W per module) for one board's semiconductors with the design point's passives, at temperature temp."""
    bk = books(board)
    bw = bk["books_w"]
    d83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]["2.5MHz"]
    d80 = json.loads((DIAG / "D80_thermal_gate.json").read_text())["inputs"]
    d75 = json.loads((DIAG / "D75_footprint.json").read_text())["lateral"]
    f = 1e9 / bk["period_ns"]
    ksw, kcu = 1 + ET.A_SW * (temp - 25), 1 + ET.A_CU * (temp - 25)
    it = {
        "conduction_high": bw["switches_high"] * ksw, "conduction_low": bw["switches_low"] * ksw,
        "edges_high": bw["edges_high"], "edges_low": bw["edges_low"], "reverse_dead_time": bw["rev_fit"],
        "gate_drive": N_DEV * lb.QG_TYP * lb.VGS * f, "series_caps_esr": rep["old_semis_w"]["series_caps"],
        "loop_damper_50pH": d80["damper50_w"], "inductor_copper": d83["cases"]["steady"]["copper_w"] * kcu}
    core = {f"{e}_{kn}": kv * d83["core"][e]["k1_eq1_w"] for e in ("lo", "hi") for kn, kv in (("k1", 1.0), ("kV", d83["kappa_nearest"]))}
    lat = {k: d75[k]["w_20mm"] * kcu for k in ("429um", "86um")}
    e = d80["edges_w_per_module"]
    hot = sum(e["hot"]["edge_w"]) + sum(e["hot"]["rev_w"]) - sum(e["nom"]["edge_w"]) - sum(e["nom"]["rev_w"])
    return {"board": board, "temp_c": temp, "f_hz": f, "items_w": it, "core_w": core, "lateral_w": lat, "books": bk,
            "loop_150pH_extra_w": ET.PKG["86um_150pH"]["loop"] - ET.PKG["429um_50pH"]["loop"],
            "gate_drive_zvs_low_sides_w": (4 * lb.N_H * lb.QG_TYP + 4 * lb.N_L * (lb.QG_TYP - lb.QGD)) * lb.VGS * f,
            "edges_hot_sensitivity_w": hot * (temp - 25.0) / 100.0}   # D80: nominal -> 125 C devices, linear in T


def efficiencies(L, p_out=250.0):
    base = sum(L["items_w"].values())
    chip = base - L["items_w"]["loop_damper_50pH"]                       # no package: no loop, no lateral copper
    p150 = base + L["lateral_w"]["86um"] + L["loop_150pH_extra_w"]
    out = {"no_core": {"chip": eff(p_out, chip), "pkg_429um_50pH": eff(p_out, base + L["lateral_w"]["429um"]),
                       "pkg_86um_150pH": eff(p_out, p150)}}
    for ck, cw in L["core_w"].items():
        out[ck] = {"chip": eff(p_out, chip + cw), "pkg_429um_50pH": eff(p_out, base + cw + L["lateral_w"]["429um"]),
                   "pkg_86um_150pH": eff(p_out, p150 + cw)}
    out["sum_w"] = {"chip_no_core": chip, "pkg_429um_50pH_no_core": base + L["lateral_w"]["429um"]}
    return out


def main():
    rep = reproduce()
    res = {"reproduction": rep, "ledgers": {}}
    for board in ("N0", "N75", "S75"):
        for t in (25.0, T_HOT):
            L = ledger(board, rep, t)
            L["eff_pct"] = efficiencies(L)
            res["ledgers"][f"{board}_{t:g}C"] = L
    n0 = res["ledgers"]["N0_25C"]["items_w"]
    o = rep["old_semis_w"]
    res["old_vs_new_n0_25c"] = {
        "conduction": [o["switch_conduction"], n0["conduction_high"] + n0["conduction_low"]],
        "edges_and_reverse": [o["hard_turn_on"] + o["turn_off_overlap"] + o["reverse_conduction"],
                              n0["edges_high"] + n0["edges_low"] + n0["reverse_dead_time"]],
        "gate_drive": [o["gate_drive"], n0["gate_drive"]], "series_caps_esr": [o["series_caps"], n0["series_caps_esr"]],
        "loop": [ET.PKG["429um_50pH"]["loop"], n0["loop_damper_50pH"]],
        "inductor_copper": [rep["a124_budget_w"]["inductor_copper"], n0["inductor_copper"]]}
    (DIAG / "D85_loss_ledger.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(f"reproduction: A124 budget {rep['a124_bit_for_bit']}, D83 efficiencies {rep['d83_bit_for_bit']}")
    for name, L in res["ledgers"].items():
        e = L["eff_pct"]
        print(f"{name}: items {sum(L['items_w'].values()):.2f} W (books recomputed {L['books']['recomputed']}); "
              f"no core {e['no_core']['chip']:.2f} / {e['no_core']['pkg_429um_50pH']:.2f} %; "
              f"k1 {e['hi_k1']['chip']:.2f}-{e['lo_k1']['chip']:.2f} / {e['hi_k1']['pkg_429um_50pH']:.2f}-{e['lo_k1']['pkg_429um_50pH']:.2f} %; "
              f"kV {e['hi_kV']['chip']:.2f}-{e['lo_kV']['chip']:.2f} / {e['hi_kV']['pkg_429um_50pH']:.2f}-{e['lo_kV']['pkg_429um_50pH']:.2f} %")
    for k, (a, b) in res["old_vs_new_n0_25c"].items():
        print(f"  {k:18s} {a:7.2f} -> {b:7.2f} W ({b - a:+.2f})")


if __name__ == "__main__":
    main()
