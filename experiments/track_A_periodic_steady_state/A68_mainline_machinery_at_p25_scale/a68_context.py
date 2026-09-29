"""A68 - run the main line's P25-native event machinery READ ONLY (no main-line
file is modified) with (a) its own synthetic fixture and (b) P25-scale values.

Tests A67's hypothesis that D23-D38's failures come from the fixture's scale
ratios. The main-line code is the other session's working tree (partly
uncommitted); `source_hashes()` records exactly which bytes were run.

Usage: python3 a68_context.py fixture|p25|p25_override
"""
import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from scb_ivr.p25_control_memory import KnownPeak, Policy, start_at_high_on  # noqa: E402
from scb_ivr.p25_cycle_modes import cycle_mode  # noqa: E402
from scb_ivr.p25_entry_direction import DirectionTolerance  # noqa: E402
from scb_ivr.p25_event_guards import Snapshot  # noqa: E402
from scb_ivr.p25_local_flow import ConstantPorts  # noqa: E402
from scb_ivr.p25_native_events import NativeBoundary, PeakReference  # noqa: E402
from scb_ivr.p25_nodal_contract import Components  # noqa: E402
from scb_ivr.p25_periodic_section import ModelIdentity, ReturnTolerance  # noqa: E402
from scb_ivr.p25_reverse_contract import ReverseModel, Tolerances  # noqa: E402
from scb_ivr.p25_root_location import RootSettings  # noqa: E402
from scb_ivr.p25_seed_evaluation import evaluate_seed  # noqa: E402
from scb_ivr.p25_shooting_contract import ShootingContract, SectionSeed  # noqa: E402


def source_hashes():
    files = sorted((PROJECT / "src" / "scb_ivr").glob("p25_*.py")) + [PROJECT / "scripts" / "audit_p25_synthetic_seeds.py"]
    h = hashlib.sha256()
    for f in files:
        h.update(f.read_bytes())
    return h.hexdigest()[:16], len(files)


def make_context(sc):
    parts = Components(sc["coss_f"], (0.,) * 6, sc["series_f"], sc["output_f"], sc["inductance_h"], (0.,) * 3, sc["label"])
    policy = Policy((sc["ton_s"],) * 3, 1e-8, 1e-8, sc["time_tol_s"], True, sc["label"] + " ideal control")
    ports = ConstantPorts(sc["load_a"], 0., sc["label"] + " constant current")
    reverse = ReverseModel("ideal_zero_drop", (0.,) * 6, "declared ideal mathematical branch")
    boundary = NativeBoundary(3, 1, 1, "dynamic_Co_current_ports", sc["alpha"])
    a2, x1, out, i1, i2, i3 = sc["seed"]
    state = Snapshot(boundary, sc["label"], "absolute", 0, 0., sc["vin"],
                     (sc["vin"], a2, x1, 0., 0., out), (i1, i2, i3), cycle_mode("M1").gates)
    peaks = tuple(KnownPeak(PeakReference(k, sc["peak_ref_a"], "declared_design_peak", sc["label"]), 0.)
                  for k in (1, 2, 3))
    memory = start_at_high_on(state, phase=1, peaks=peaks, policy=policy)
    contract = ShootingContract(memory, ModelIdentity(parts, reverse, policy, sc["label"]), ports, sc["label"])
    root = RootSettings(sc["time_tol_s"], 1e-8, 200, "sampled continuous local affine flow")
    options = dict(return_tolerance=ReturnTolerance(1e-6, 1e-6, sc["time_tol_s"] * 1e3, 0.),
                   stage_horizons_s=sc["horizons_s"], intervals=sc["intervals"],
                   voltage_root=root, current_root=root, electrical=Tolerances(1e-8, 1e-8, 1e-8),
                   direction=DirectionTolerance(1e-8, 1e-8, 1e-10, 1e-10))
    return contract, options


def describe(r):
    steps = []
    for s in r.attempt.steps:
        o = s.outcome
        m = o.memory
        steps.append({"mode": s.mode, "phase": s.phase, "status": o.status,
                      "t_end_s": None if m is None else m.last_event.time_s,
                      "i_end_a": None if m is None else list(m.last_event.current_a),
                      "v_end_v": None if m is None else list(m.last_event.voltage_v)})
    return {"status": r.status, "failed_mode": r.attempt.failed_mode, "steps": steps}


def run(sc, seed=None):
    contract, options = make_context(sc)
    z = seed if seed is not None else sc["seed"]
    t0 = time.time()
    r = evaluate_seed(contract, SectionSeed(z[0], z[1], z[2], tuple(z[3:])), **options)
    d = describe(r)
    d["wall_s"] = time.time() - t0
    d["seed"] = list(z)
    return r, d


FIXTURE = dict(label="D12 synthetic fixture (control)", coss_f=(1.,) * 6, series_f=(17., 19.), output_f=23.,
               inductance_h=(2., 3., 4.), ton_s=.02, load_a=1., alpha=.05, vin=12., peak_ref_a=20.,
               seed=(4., 2., 1., 20., 2., 3.), time_tol_s=1e-9, horizons_s=(1., 10., 10., 10.), intervals=200)

# P25 scale (P25_SUPPLEMENT orders of magnitude; PROJECT_DECISION where stated):
L25, TON25, VIN, VO, ALPHA, PEAK = 30e-9, 500e-9, 12., 1., .05, 50.
SLOPE = VO / L25                              # all-low decay, A/s
I_N = ALPHA * PEAK                            # negative target, 1 A
T25 = TON25 * (VIN / 3) / VO                  # boundary-mode period, 2 us
# Series capacitors: P25 assumes zero series-capacitor ripple (Sec. II) and publishes no value;
# 100 uF (~0.1 V ripple) is a PROJECT_DECISION. A first run with 10 uF drooped ~1.25 V (see RESULTS).
P25 = dict(label="P25-scale test, Cs 100 uF", coss_f=(0.69e-9,) * 3 + (1.38e-9,) * 3, series_f=(100e-6, 100e-6), output_f=100e-6,
           inductance_h=(L25,) * 3, ton_s=TON25, load_a=3 * (((VIN / 3 - VO) * TON25 / L25) / 2 - I_N),
           alpha=ALPHA, vin=VIN, peak_ref_a=PEAK,
           seed=(4., 4., 1., -I_N, -I_N + SLOPE * T25 / 3, -I_N + SLOPE * 2 * T25 / 3),
           time_tol_s=1e-15, horizons_s=(200e-9, 2e-6, 2e-6, 200e-9), intervals=4000)

# ---- DIAGNOSTIC OVERRIDE (in memory only; NOT the main line's accepted rule) ----
# The main line's D11 rule blocks any negative reverse gap, even inside the
# numerical tolerance ("no projection"). This wrapper releases ONLY reverse
# gaps with -tol <= value < 0 whose rate is outward (> rate tolerance), and
# records each use. Everything else is the main line's own decision.
OVERRIDE_LOG = []


def install_entry_override():
    import scb_ivr.p25_entry_direction as E
    original = E.classify_entry

    def wrapped(flow, reverse, tolerance):
        rep = original(flow, reverse, tolerance)
        items, changed = [], False
        for i in rep.items:
            if (i.status == "OUTSIDE_DOMAIN" and i.name.startswith("reverse.") and i.unit == "V"
                    and -tolerance.voltage_v <= i.value < 0 and i.rate > tolerance.voltage_rate_v_s):
                OVERRIDE_LOG.append({"t_s": flow.start.time_s, "mode": flow.mode, "gap": i.name,
                                     "value_v": i.value, "rate_v_s": i.rate})
                items.append(E.EntryItem(i.name, i.value, i.rate, i.unit, "LEAVING_REVERSE_BOUNDARY"))
                changed = True
            else:
                items.append(i)
        if not changed:
            return rep
        release = tuple(i.name for i in items if i.status == "LEAVING_REVERSE_BOUNDARY")
        blockers = tuple(i.name for i in items if i.status not in {"INTERIOR", "LEAVING_REVERSE_BOUNDARY"})
        return E.EntryReport(tuple(items), release, blockers)

    E.classify_entry = wrapped


if __name__ == "__main__":
    which = sys.argv[1]
    sc = {"fixture": FIXTURE, "p25": P25, "p25_override": P25}[which]
    if which == "p25_override":
        install_entry_override()
    digest, n = source_hashes()
    print(f"main-line source hash {digest} over {n} files (read only)")
    r, d = run(sc)
    print(json.dumps({k: v for k, v in d.items() if k != "steps"}, indent=1))
    for s in d["steps"]:
        i = s["i_end_a"]
        print(f"  {s['mode']:4s} ph{s['phase']} {s['status']:40s} t={s['t_end_s']} i={None if i is None else [round(x, 4) for x in i]}")
