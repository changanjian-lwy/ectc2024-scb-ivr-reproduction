"""Generate A48's fixed-delay dead-time feasibility sweep.

Parent: paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir
(the same P24 t2->t3 local chain, same fixed quantities as A42's zero-snubber
baseline: Vin=48V, Vo=1V, nP=4, NM=1, Ipk=125A, Eq.-(4) L=1.4667nH, GS61008T
CH=385pF/CL=770pF, 7/3.5 mOhm RDS(on)).

Only changed variable relative to A42/R04D3A: QH1's turn-on rule. A42/R04D3A
use an ideal event detector -- QH1 turns on the instant V(vin,a1)<0. A48
replaces that with a fixed-delay turn-on: QH1 turns on at a fixed time
T_DEAD after the QL1 release event (I(L1)<-INEG), regardless of V(vin,a1)'s
value at that instant.

A supporting (not itself the changed variable) ideal GaN off-state
reverse-conduction diode -- the same DGAN_IDEAL model A27 already uses,
Vf=0, Ron=1 mOhm, P25-labelled -- is placed across QH1 so the simulation
stays well-posed if T_DEAD is long enough for the natural Vds=0 crossing to
occur before the forced turn-on fires. It only activates after Vds has
already reached ~0 and does not affect the pre-crossing residual-Vds
measurement used for the primary result.
"""

from __future__ import annotations

from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
HERE = TRACK / "A48_dead_time_feasibility_sweep"

# The three fixed release rows reused from A42: its two P24_EXPLICIT rows
# (1%, 2%) and A42's own already-found local natural-ZVS threshold row
# (7.77%, A42's own bracketed reference case).
NEG_FRAC_ROWS = {
    "01pct": (0.01, "P24_EXPLICIT"),
    "02pct": (0.02, "P24_EXPLICIT"),
    "777bp": (0.0777, "A42_NATURAL_ZVS_REFERENCE"),
}

# Coarse grid, ns: physically reasonable real GaN driver dead-time span.
COARSE_T_DEAD_NS = (0.5, 1, 2, 3, 5, 7, 10, 15, 20)

# Refinement grids target only the 7.77% row's found transition bracket.
# Two stages, same coarse-then-refine convention as A42's 0.1%/0.01%
# negative-current grids.
REFINEMENT_T_DEAD_NS = (2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0)
FINE_T_DEAD_NS = (2.10, 2.12, 2.14, 2.15, 2.16, 2.17, 2.18, 2.20, 2.22, 2.24)

MACHINE_BLOCK_OLD = """.machine 1p
.state P24_QL1_NEGATIVE 0
.state P24_COMMUTATE_TO_HIGH 1
.state P24_QH1_ZVS_ON 2
.rule P24_QL1_NEGATIVE P24_COMMUTATE_TO_HIGH I(L1)<-INEG
.rule P24_COMMUTATE_TO_HIGH P24_QH1_ZVS_ON V(vin,a1)<0
.output (gl1) 5*(state==P24_QL1_NEGATIVE)
.output (gh1) 5*(state==P24_QH1_ZVS_ON)
.output (state_mon) state
.endmachine"""

MACHINE_BLOCK_NEW = """.machine 1p
.state P24_QL1_NEGATIVE 0
.state P24_COMMUTATE_TO_HIGH 1
.rule P24_QL1_NEGATIVE P24_COMMUTATE_TO_HIGH I(L1)<-INEG
.output (gl1) 5*(state==P24_QL1_NEGATIVE)
.output (release_flag) 5*(state==P24_COMMUTATE_TO_HIGH)
.output (state_mon) state
.endmachine

* A48 CHANGED VARIABLE: fixed-delay turn-on. QH1's gate is driven by a
* pure time delay of the release event, NOT by the ideal V(vin,a1)<0
* detector rule the parent used. The driver does not wait for Vds=0.
B_GH1_FIXED_DELAY gh1 0 V=delay(V(release_flag),T_DEAD)
RRELEASE release_flag 0 1k"""

OLD_SH1_LINE = "SH1 vin a1 gh1 0 SWH"
NEW_SH1_BLOCK = (
    "SH1 vin a1 gh1 0 SWH\n"
    "* A48 SUPPORTING ADDITION (not the changed variable): ideal GaN\n"
    "* off-state reverse-conduction path, same DGAN_IDEAL model A27 uses\n"
    "* (Vf=0, Ron=1 mOhm, P25-labelled), so the run stays well-posed if\n"
    "* T_DEAD is long enough for Vds to reach 0 naturally before forced\n"
    "* turn-on. Reverse-biased and inactive until Vds<0.\n"
    "DH1_REVERSE a1 vin DGAN_IDEAL"
)

OLD_MEAS_BLOCK = """.meas tran P24_T_QL1_OFF WHEN I(L1)=-INEG FALL=1
.meas tran P24_IL1_AT_QL1_OFF FIND I(L1) WHEN I(L1)=-INEG FALL=1
.meas tran P24_T3_HIGH_VDS_ZERO WHEN V(vin,a1)=0 FALL=1
.meas tran P24_IL1_AT_T3 FIND I(L1) WHEN V(vin,a1)=0 FALL=1
.meas tran P24_COMMUTATION_DURATION PARAM P24_T3_HIGH_VDS_ZERO-P24_T_QL1_OFF
.meas tran P24_VDS_HS_MIN MIN V(vin,a1)
.meas tran P24_VDS_HS_MIN_AFTER_2NS MIN V(vin,a1) FROM=2n TO=50n
.meas tran P24_VDS_HS_END FIND V(vin,a1) AT=50n
.meas tran P24_VDS_LS_MAX MAX V(x1)
.meas tran P24_NEGATIVE_TARGET PARAM {INEG}
.meas tran NP_EXPLICIT PARAM {NP}
.meas tran NM_EXPLICIT PARAM {NM}"""

NEW_MEAS_BLOCK = """.meas tran P24_T_QL1_OFF WHEN I(L1)=-INEG FALL=1
.meas tran P24_IL1_AT_QL1_OFF FIND I(L1) WHEN I(L1)=-INEG FALL=1
.meas tran P24_T3_HIGH_VDS_ZERO WHEN V(vin,a1)=0 FALL=1
.meas tran P24_IL1_AT_T3 FIND I(L1) WHEN V(vin,a1)=0 FALL=1
.meas tran P24_COMMUTATION_DURATION PARAM P24_T3_HIGH_VDS_ZERO-P24_T_QL1_OFF
* A48 forced (fixed-delay) turn-on event and the residual switching voltage
* at that instant -- the primary extracted quantity of this experiment.
.meas tran P24_T_FORCED_ON WHEN V(gh1)=2.5 RISE=1
.meas tran P24_VDS_AT_FORCED_ON FIND V(vin,a1) WHEN V(gh1)=2.5 RISE=1
.meas tran P24_IL1_AT_FORCED_ON FIND I(L1) WHEN V(gh1)=2.5 RISE=1
.meas tran P24_VDS_HS_MIN MIN V(vin,a1)
.meas tran P24_VDS_HS_MIN_AFTER_2NS MIN V(vin,a1) FROM=2n TO=50n
.meas tran P24_VDS_HS_END FIND V(vin,a1) AT=50n
.meas tran P24_VDS_LS_MAX MAX V(x1)
.meas tran P24_NEGATIVE_TARGET PARAM {INEG}
.meas tran T_DEAD_NS PARAM {T_DEAD*1e9}
.meas tran NP_EXPLICIT PARAM {NP}
.meas tran NM_EXPLICIT PARAM {NM}"""

OLD_SAVE_LINE = ".save V(x1) V(vin,a1) I(L1) V(gl1) V(gh1) V(state_mon)"
NEW_SAVE_LINE = ".save V(x1) V(vin,a1) I(L1) V(gl1) V(gh1) V(release_flag) V(state_mon)"

# A42/R04D3A's chgtol=1e-16 was tuned for a SOFT (near-zero-differential)
# ZVS closure; it is numerically incompatible with A48's genuinely hard
# turn-on cases (forcing an ~1.75 mOhm switch closed across several volts
# demands charge-transfer resolution far finer than 1e-16 C per step to
# satisfy that tolerance, which never converges in practice -- verified to
# hang indefinitely). Relaxed here to LTspice's own default (1e-14), 100x
# looser, which resolves the hang. reltol/abstol are left at A42's original
# values. Verified against A42's own original 1%/7.77% netlists with only
# chgtol relaxed: the pre-event LC resonance reproduces A42's published
# values exactly (9.2566-9.2567 V minimum for 1%, matching A42's own
# 9.256580 V), so this relaxation does not change the physics being
# measured -- it only allows the added hard-switching branch to converge.
OLD_OPTIONS_LINE = ".options reltol=1e-7 abstol=1e-10 chgtol=1e-16"
NEW_OPTIONS_LINE = ".options reltol=1e-7 abstol=1e-10 chgtol=1e-14"


def render(row_key: str, neg_frac: float, source_label: str, t_dead_ns: float) -> str:
    source = PARENT.read_text()
    text = source

    text = text.replace(
        "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS",
        f"* A48 - fixed-delay dead-time turn-on, {row_key} row, "
        f"T_DEAD={t_dead_ns:g} ns ({source_label})",
        1,
    )
    text = text.replace(
        "* END EVENT: P24 t3, Vds(QH1)=0 and ideal event logic commands QH1 ON.",
        "* END EVENT: QH1 forced ON at a FIXED TIME T_DEAD after QL1 release,\n"
        "* regardless of V(vin,a1). This replaces R04D3A/A42's ideal\n"
        "* V(vin,a1)<0 event-detector rule -- see BOUNDARY.md.",
        1,
    )
    text = text.replace(
        "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
        f"* selected A48 release row: {neg_frac * 100:g}% of the P24 Eq.(2) "
        f"phase peak (125 A), reused unchanged from A42 ({source_label}).",
        1,
    )
    text = text.replace(
        ".include ../../04_component_models/",
        ".include ../../../../paper_locked/04_component_models/",
    )
    text = text.replace(
        ".include ../../../../paper_locked/04_component_models/"
        "GS61008T_commutation_capacitance.lib",
        ".include ../../../../paper_locked/04_component_models/"
        "GS61008T_commutation_capacitance.lib\n"
        ".include ../../../../paper_locked/04_component_models/"
        "GaN_reverse_conduction_ideal.lib",
        1,
    )
    text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={neg_frac:.4f}", 1)

    rds_anchor = (
        ".param RHS={GS61008T_RDS_TYP_25C/NHS} RLS={GS61008T_RDS_TYP_25C/NLS}"
    )
    if rds_anchor not in text:
        raise RuntimeError("parent RDS(on) param line did not match expected anchor")
    text = text.replace(
        rds_anchor,
        rds_anchor + f"\n.param T_DEAD={t_dead_ns:g}n",
        1,
    )

    if MACHINE_BLOCK_OLD not in text:
        raise RuntimeError("parent .machine block text did not match expected anchor")
    text = text.replace(MACHINE_BLOCK_OLD, MACHINE_BLOCK_NEW, 1)

    if OLD_SH1_LINE not in text:
        raise RuntimeError("parent SH1 line did not match expected anchor")
    text = text.replace(OLD_SH1_LINE, NEW_SH1_BLOCK, 1)

    if OLD_MEAS_BLOCK not in text:
        raise RuntimeError("parent .meas block did not match expected anchor")
    text = text.replace(OLD_MEAS_BLOCK, NEW_MEAS_BLOCK, 1)

    if OLD_SAVE_LINE not in text:
        raise RuntimeError("parent .save line did not match expected anchor")
    text = text.replace(OLD_SAVE_LINE, NEW_SAVE_LINE, 1)

    if OLD_OPTIONS_LINE not in text:
        raise RuntimeError("parent .options line did not match expected anchor")
    text = text.replace(OLD_OPTIONS_LINE, NEW_OPTIONS_LINE, 1)

    return text


def build_grid(out_dir: Path, t_dead_values_ns: tuple[float, ...], tag: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for row_key, (neg_frac, source_label) in NEG_FRAC_ROWS.items():
        for t_dead_ns in t_dead_values_ns:
            text = render(row_key, neg_frac, source_label, t_dead_ns)
            td_tag = f"{t_dead_ns:g}".replace(".", "p")
            path = out_dir / f"a48_{tag}_{row_key}_tdead_{td_tag}ns.cir"
            path.write_text(text)
            generated.append(path)
    return generated


def _prune_to_777_only(paths: list[Path]) -> list[Path]:
    kept = []
    for path in paths:
        if "777bp" in path.name:
            kept.append(path)
        else:
            path.unlink(missing_ok=True)
    return kept


def build() -> dict[str, list[Path]]:
    coarse = build_grid(HERE / "cases", COARSE_T_DEAD_NS, "coarse")
    # Refinement stages only need the 7.77% row -- prune the others, since
    # 1%/2% never transition (dead time cannot manufacture missing negative-
    # current margin) and do not need finer resolution.
    refinement = _prune_to_777_only(
        build_grid(HERE / "refinement_cases", REFINEMENT_T_DEAD_NS, "refine")
    )
    fine = _prune_to_777_only(
        build_grid(HERE / "fine_cases", FINE_T_DEAD_NS, "fine")
    )
    return {"coarse": coarse, "refinement": refinement, "fine": fine}


if __name__ == "__main__":
    result = build()
    for tag, paths in result.items():
        print(f"# {tag}: {len(paths)} cases")
        for generated_path in paths:
            print(generated_path)
