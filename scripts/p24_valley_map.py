"""D63: the cycle-by-cycle valley map against the co-simulation's transients (validation), and its design map.

    python3 scripts/p24_valley_map.py

1. D57's zero-voltage threshold against the rail at 1.4667 nH and 7.333 nH (cached in the diagnostics file; computed
   once, ~2 min).
2. Validation: every load and line step the co-simulation has run on the designs D63 covers (5 MHz 5% / 20% / 25%,
   1 MHz 5% / 10%; timed, comparator; 60 / 30 / 100 kHz), with the co-simulation's registered results (source in
   each row).
3. The design map at 1 MHz 10%: the turn-off rule (comparator, timed, floor) x Cs (15, 3 uF) x the input slew
   (+-4.8 V over 1-50 us) and the +-62.5 A load steps.
Writes symbolic_derivations/03_P24_native/diagnostics/D63_valley_map.json.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import node_model  # noqa: E402
from scb_ivr.p24_valley_map import Design, metrics, simulate, thresholds  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
OUT = DIAG / "D63_valley_map.json"
L5, L1 = 1.4666667e-9, 7.3333333e-9
F30 = dict(kp_ns=287.23, ki_ns=11.9816)
T_STEP = 50e-6


def ith_table():
    if OUT.exists():
        old = json.loads(OUT.read_text()).get("thresholds")
        if old:
            return old
    return {str(lf): thresholds(lf) for lf in (L1, L5)}


def t_tr(lf, i_neg):
    e = EdgeCircuit()
    t1 = node_model(replace(e, lf=lf)).valley_free(i_neg, t_max=200e-9)[0]
    t4 = node_model(replace(e, lf=lf, v_rail=12.0, dv_cs=0.0, n_next=0)).valley_free(i_neg, t_max=200e-9)[0]
    return (t1, t1, t1, t4)


def designs(ith):
    th5, th1 = tuple(tuple(x) for x in ith[str(L5)]), tuple(tuple(x) for x in ith[str(L1)])
    d5 = lambda pct, mode: Design(lf=L5, cs=3e-6, i_tgt=-pct * 1.25, mode=mode, kp_ns=188.851, ki_ns=5.5105,
                                  ton_cfg_ns=17.75, smax=32, rs_low_ns=400.0, t_tr=t_tr(L5, pct * 1.25), ith=th5)
    d1 = lambda pct, mode, **kw: Design(lf=L1, cs=15e-6, i_tgt=-pct * 1.25, mode=mode, t_tr=t_tr(L1, pct * 1.25), ith=th1, **kw)
    return d5, d1


# (name, design key, step kwargs, co-simulation: extreme mV, back us, peak A, outcome, source)
CASES = [
    ("1MHz 10% cmp 60k -62.5A", ("d1", 10, "cmp", {}), {"i_step": -62.5}, (28.04, 16.12, 158, "ok", "A116 c60_s_m62")),
    ("1MHz 10% cmp 60k +62.5A", ("d1", 10, "cmp", {}), {"i_step": 62.5}, (-28.55, 22.38, 176, "ok", "A116 c60_s_p62")),
    ("1MHz 10% cmp 30k -62.5A", ("d1", 10, "cmp", F30), {"i_step": -62.5}, (47.31, 52.47, 158, "ok", "A116 c30_s_m62")),
    ("1MHz 10% cmp 30k +62.5A", ("d1", 10, "cmp", F30), {"i_step": 62.5}, (-48.21, 79.63, 174, "ok", "A116 c30_s_p62")),
    ("1MHz 10% timed 60k -62.5A", ("d1", 10, "timed", {}), {"i_step": -62.5}, (546.35, None, 554, "runaway", "A115 n10_s_m62")),
    ("1MHz 10% timed 60k +62.5A", ("d1", 10, "timed", {}), {"i_step": 62.5}, (-19.90, 13.67, 174, "ok", "A115 n10_s_p62")),
    ("1MHz 10% timed 30k -62.5A", ("d1", 10, "timed", F30), {"i_step": -62.5}, (-36.37, 199.82, 158, "slow", "A116 t30_s_m62")),
    ("1MHz 10% timed 30k +62.5A", ("d1", 10, "timed", F30), {"i_step": 62.5}, (-29.89, 98.46, 174, "ok", "A116 t30_s_p62")),
    ("1MHz 5% timed 60k -62.5A", ("d1", 5, "timed", {}), {"i_step": -62.5}, (19.54, 45.32, 158, "slow", "A115 n5_s_m62")),
    ("1MHz 5% timed 60k +62.5A", ("d1", 5, "timed", {}), {"i_step": 62.5}, (-19.33, 24.81, 168, "ok", "A115 n5_s_p62")),
    ("5MHz 5% timed -62.5A", ("d5", 5, "timed", {}), {"i_step": -62.5}, (11.30, None, None, "ok", "C02 s1_s_m62")),
    ("5MHz 5% timed +62.5A", ("d5", 5, "timed", {}), {"i_step": 62.5}, (-14.59, None, None, "ok", "C02 s1_s_p62")),
    ("5MHz 25% timed -62.5A", ("d5", 25, "timed", {}), {"i_step": -62.5}, (-14.95, 183.0, None, "slow", "A112 p25_s_m62")),
    ("5MHz 25% cmp -62.5A", ("d5", 25, "cmp", {}), {"i_step": -62.5}, (16.89, 8.9, None, "ok", "A113 cmp_s_m62")),
    ("5MHz 5% timed +4.8V/1us", ("d5", 5, "timed", {}), {"dvin": 4.8, "t_slew": 1e-6}, (11.8, None, 207, "peak", "A106")),
    ("5MHz 5% timed -4.8V/1us", ("d5", 5, "timed", {}), {"dvin": -4.8, "t_slew": 1e-6}, (-18.5, None, None, "ok", "A106")),
    ("5MHz 20% timed +4.8V/1us", ("d5", 20, "timed", {}), {"dvin": 4.8, "t_slew": 1e-6}, (-9.1, None, 199, "ok", "A114 (A112 p20)")),
    ("5MHz 25% timed -4.8V/1us", ("d5", 25, "timed", {}), {"dvin": -4.8, "t_slew": 1e-6}, (-34.0, 182.0, None, "slow", "A112 p25")),
    ("5MHz 25% cmp +4.8V/1us", ("d5", 25, "cmp", {}), {"dvin": 4.8, "t_slew": 1e-6}, (-70.9, None, 287, "peak", "A114 c25")),
    ("5MHz 25% cmp -4.8V/1us", ("d5", 25, "cmp", {}), {"dvin": -4.8, "t_slew": 1e-6}, (15.8, 2.8, None, "ok", "A114 c25")),
    ("1MHz 10% cmp 60k +4.8V/1us", ("d1", 10, "cmp", {}), {"dvin": 4.8, "t_slew": 1e-6}, (-129.32, 51.90, 341, "peak", "A116 c60_l_p48_1us")),
    ("1MHz 10% cmp 60k -4.8V/1us", ("d1", 10, "cmp", {}), {"dvin": -4.8, "t_slew": 1e-6}, (94.16, 43.73, 206, "peak", "A116 c60_l_m48_1us")),
    ("1MHz 10% timed 60k +4.8V/1us", ("d1", 10, "timed", {}), {"dvin": 4.8, "t_slew": 1e-6}, (499.91, None, 546, "runaway", "A116 t60_l_p48_1us")),
    ("1MHz 10% timed 60k -4.8V/1us", ("d1", 10, "timed", {}), {"dvin": -4.8, "t_slew": 1e-6}, (-452.68, None, 495, "runaway", "A116 t60_l_m48_1us")),
    ("1MHz 10% timed 30k +4.8V/1us", ("d1", 10, "timed", F30), {"dvin": 4.8, "t_slew": 1e-6}, (40.78, 73.63, 233, "peak", "A116 t30_l_p48_1us")),
]


def ph1_crossing(recs):
    a = [r for r in recs if r["t"] >= T_STEP]
    d = [r["depth"][0] for r in a]
    return max(d), sum(1 for v in d if v > 0)


def run_case(d, kw, t_end=450e-6):
    r = simulate(d, t_end, T_STEP, **kw)
    m = metrics(r, T_STEP)
    m["ph1_depth_a"], m["ph1_crossing_periods"] = ph1_crossing(r)
    return m


def main():
    ith = ith_table()
    d5, d1 = designs(ith)
    make = lambda key: (d5(key[1], key[2]) if key[0] == "d5" else d1(key[1], key[2], **key[3]))
    out = {"thresholds": ith, "validation": [], "map": []}
    print("validation (model against the co-simulation)")
    for name, key, kw, (mv, back, pk, outcome, src) in CASES:
        m = run_case(make(key), kw)
        out["validation"].append({"case": name, "source": src, "cosim": {"extreme_mv": mv, "back_us": back, "peak_a": pk, "outcome": outcome},
                                  "model": m})
        print(f"  {name:30s} cosim {mv:+8.2f} mV {'' if back is None else f'{back:6.1f} us'} {'' if pk is None else f'{pk} A'} [{outcome}]"
              f" | model {m['extreme_mv']:+7.1f} mV {m['back_us']:6.1f} us {m['peak_max_a']:4.0f} A, phase 1 crossing "
              f"{m['ph1_depth_a']:5.1f} A x {m['ph1_crossing_periods']:3d}, slots {max(m['depth_max_a'][1:]):5.1f} A  ({src})")
    print("design map, 1 MHz 10% (60 kHz loop)")
    base = d1(10, "cmp")
    for cs in (15e-6, 3e-6):
        for mode in ("cmp", "timed", "floor"):
            dd = replace(base, cs=cs, mode=mode)
            for kw, label in [({"i_step": -62.5}, "-62.5A"), ({"i_step": 62.5}, "+62.5A")] + \
                    [({"dvin": dv, "t_slew": s * 1e-6}, f"{dv:+.1f}V/{s}us") for s in (1, 2, 5, 10, 20, 50) for dv in (4.8, -4.8)]:
                m = run_case(dd, kw, t_end=600e-6)
                out["map"].append({"cs_uf": cs * 1e6, "mode": mode, "step": label, "model": m})
                print(f"  Cs {cs * 1e6:4.0f} uF {mode:5s} {label:11s}: {m['extreme_mv']:+7.1f} mV, back {m['back_us']:6.1f} us, peak "
                      f"{m['peak_max_a']:5.0f} A, phase 1 crossing {m['ph1_depth_a']:5.1f} A x {m['ph1_crossing_periods']:3d}, slots "
                      f"{max(m['depth_max_a'][1:]):5.1f} A")
    DIAG.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
