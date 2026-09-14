"""Generate A45's stage-0 (P24 interval 1) netlist.

A45 studies whether swapping the active GS61008T commutation-capacitance
library for the 2024 Table-3-named EPC2067 candidate (see
paper_locked/04_component_models/EPC2067_commutation_capacitance.lib) moves
the A42 zero-snubber negative-current ZVS threshold, and in which direction.

Interval 1 (R04D0) has no CH1/CL1 commutation-capacitance elements at all
(see paper_locked/02_ectc2024_main/spice/R04D0_p24_first_interval_shared_ladder.cir):
only the switches, flying capacitor and inductor. Its result is therefore
mathematically independent of which device's commutation-capacitance library
is used downstream. This stage is still rebuilt and rerun byte-for-byte
(only the header comment changes) so that the full interval-1->2->3 chain is
verifiably re-run for A45, per this project's chained-state provenance rule,
rather than silently re-using R04D0's committed output numbers.
"""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D0_p24_first_interval_shared_ladder.cir"
)
OUT = (
    TRACK
    / "A45_epc2067_table3_candidate_commutation"
    / "A45_stage0_interval1_shared_ladder.cir"
)

HEADER_OLD = (
    "* R04D0 - P24 first interval on the shared Fig.3 flying-capacitor ladder"
)
HEADER_NEW = (
    "* A45 stage 0 - P24 interval 1, re-run unchanged from R04D0\n"
    "* This stage has no CH1/CL1 commutation-capacitance element, so it is\n"
    "* mathematically identical regardless of the GS61008T vs EPC2067 library\n"
    "* choice made downstream in A45 stage 1/2. Rerun here only for the\n"
    "* required full-chain provenance trail (see A45 BOUNDARY.md); its output\n"
    "* is expected to reproduce R04D0's committed IL1_MAX/VC1_END/IL2_AT_TON\n"
    "* values exactly and that reproduction is checked, not assumed."
)


def build() -> Path:
    text = PARENT.read_text()
    assert HEADER_OLD in text, "R04D0 header text changed; update this script"
    text = text.replace(HEADER_OLD, HEADER_NEW, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    return OUT


if __name__ == "__main__":
    print(build())
